from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any, Tuple
import io
import os
import json
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

from pypdf import PdfReader
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from database import get_db, engine, Base
import models
import schemas
from gemini_service import extract_biomarkers_with_gemini, analyze_holistic_risks
import chat_router
import auth_router

# JWT session configuration
SECRET_KEY = "AXON_SECURE_CLINICAL_SESSION_SIGNATURE_KEY"
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[int]:
    """
    Dependency to decode JWT from Authorization header and return the user ID.
    Returns None if missing or invalid to maintain optional authentication endpoints.
    """
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None


app = FastAPI(
    title="AI Lab Report Analyzer API",
    description="Backend API for parsing lab reports, mapping standard reference ranges, predicting disease risks, and generating empathetic simplified summaries.",
    version="1.3.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key="AXON_SESSION_SECRET_OAUTH_COOKIE_KEY"
)

# Register medical chatbot router
app.include_router(router=chat_router.router)

# Register user authentication router
app.include_router(router=auth_router.router)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Service Function 1: File Text Extraction
    Reads the incoming PDF file bytes and extracts its raw text content.
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def get_mock_image_text() -> str:
    """
    Returns a standard regex-compatible medical lab report raw text mockup
    if both local OCR and Gemini Vision fallbacks fail.
    """
    return (
        "==================================================\n"
        "AXON CLINICAL LABORATORY REPORT\n"
        "==================================================\n"
        "Patient Name: John Doe\n"
        "Date of Analysis: 2026-05-31\n"
        "Session: Standard Morning Fasting\n"
        "==================================================\n"
        "BIOMARKER            VALUE      UNIT\n"
        "Hemoglobin:          10.5       g/dL\n"
        "WBC:                 7.5        10^3/uL\n"
        "Platelets:           280.0      10^3/uL\n"
        "HbA1c:               5.8        %\n"
        "Fasting:             145.0      mg/dL\n"
        "Total Cholesterol:   260.0      mg/dL\n"
        "HDL:                 35.0       mg/dL\n"
        "LDL:                 155.0      mg/dL\n"
        "Triglycerides:       185.0      mg/dL\n"
        "Creatinine:          0.85       mg/dL\n"
        "TSH:                 6.2        uIU/mL\n"
        "Free T4:             1.1        ng/dL\n"
    )

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Preprocesses the incoming raw image bytes (grayscale, contrast, sharpening)
    to optimize OCR legibility.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # 1. Convert to grayscale
        image = image.convert("L")
        # 2. Amplify contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        # 3. Apply edge-sharpening filter
        image = image.filter(ImageFilter.SHARPEN)
        return image
    except Exception as e:
        raise ValueError(f"Failed to preprocess image: {str(e)}")

def validate_extracted_text(text: str):
    """
    Validates that the extracted text looks like a medical lab report.
    Checks for presence of basic medical/lab keywords.
    """
    text_lower = text.lower().strip()
    
    # 1. Check length
    if len(text_lower) < 15:
        raise ValueError(
            "The document contains no readable text. Please ensure you upload "
            "a clear, well-lit medical lab report."
        )
        
    # 2. Check for common medical report keywords
    keywords = [
        "hemoglobin", "wbc", "rbc", "platelet", "cholesterol", "glucose", "hba1c", 
        "tsh", "creatinine", "urea", "bilirubin", "alt", "ast", "report", "patient", 
        "reference", "interval", "range", "result", "value", "unit", "specimen", 
        "blood", "serum", "clinical", "laboratory", "analysis", "test"
    ]
    
    # Count how many keywords are present
    match_count = sum(1 for kw in keywords if kw in text_lower)
    
    # If the text has absolutely no medical context keywords, reject it.
    if match_count == 0:
        raise ValueError(
            "No clinical biomarkers or readable medical terms detected in the document. "
            "Please upload a valid laboratory report."
        )

def sanitize_patient_text(text: str) -> str:
    """
    Scrubs Personally Identifiable Information (PII) such as SSNs, Aadhaar numbers,
    phone numbers, email addresses, and patient name lines before DB persistence.
    """
    import re
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SCRUBBED_SSN]', text)
    text = re.sub(r'\b\d{4}-\d{4}-\d{4}\b', '[SCRUBBED_AADHAAR]', text)
    text = re.sub(r'(?:\+91\s*)?\b[6-9]\d{9}\b', '[SCRUBBED_PHONE]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[SCRUBBED_EMAIL]', text)
    text = re.sub(r'(?:Patient Name|Patient|Name|Mr\.|Ms\.|Mrs\.)\s*(?::\s*)?[A-Za-z\s]+', '[DE-IDENTIFIED]', text, flags=re.IGNORECASE)
    return text

def extract_text_from_image(image_bytes: bytes, api_key: Optional[str] = None) -> Tuple[str, bool]:
    """
    Service Function: Image OCR Text Extraction
    1. Preprocesses image for better text clarity.
    2. Runs local Tesseract OCR engine (pytesseract).
    3. Falls back gracefully to local EasyOCR local parsing.
    4. Falls back gracefully to native Gemini multimodal vision or local mock text on failure.
    Returns a tuple: (extracted_text, is_mock_fallback)
    """
    candidates = []
    validation_errors = []

    # 1. Try pytesseract
    try:
        processed_image = preprocess_image(image_bytes)
        text = pytesseract.image_to_string(processed_image)
        if text and text.strip():
            print("Successfully extracted text using local pytesseract OCR.")
            try:
                validate_extracted_text(text)
                return text, False
            except ValueError as ve:
                candidates.append(text)
                validation_errors.append(str(ve))
        else:
            validation_errors.append("pytesseract returned empty output.")
    except Exception as e:
        print(f"Local OCR failed or Tesseract is not installed: {str(e)}.")
        validation_errors.append(f"pytesseract execution error: {str(e)}")

    # 2. Try EasyOCR
    try:
        print("Attempting local EasyOCR parsing...")
        import easyocr
        import numpy as np
        
        processed_image = preprocess_image(image_bytes)
        img_np = np.array(processed_image)
        
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        results = reader.readtext(img_np)
        
        easy_text = "\n".join([r[1] for r in results])
        if easy_text and easy_text.strip():
            print("Successfully extracted text using local EasyOCR!")
            try:
                validate_extracted_text(easy_text)
                return easy_text, False
            except ValueError as ve:
                candidates.append(easy_text)
                validation_errors.append(str(ve))
        else:
            validation_errors.append("EasyOCR returned empty output.")
    except Exception as easy_err:
        print(f"Local EasyOCR failed: {str(easy_err)}")
        validation_errors.append(f"EasyOCR execution error: {str(easy_err)}")

    # 3. Try Gemini Multimodal Vision
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        print("Falling back to Gemini multimodal vision OCR...")
        try:
            from gemini_service import generate_gemini_content
            image = Image.open(io.BytesIO(image_bytes))
            prompt_str = (
                "You are an expert clinical transcriber. Transcribe all text, numbers, and biomarkers from this medical laboratory report image exactly as they appear. "
                "CRITICAL: If the image is not a medical report (e.g. if it is a face, scenery, an object, a person, or does not contain clinical metrics), you MUST reply with exactly: 'ERROR: NOT_A_MEDICAL_REPORT'"
            )
            response = generate_gemini_content(api_key, [prompt_str, image])
            if response.text and response.text.strip():
                text = response.text
                if "NOT_A_MEDICAL_REPORT" in text:
                    raise ValueError("The uploaded image does not appear to be a medical laboratory report. Please ensure the document is aligned and contains medical values.")
                
                try:
                    validate_extracted_text(text)
                    return text, False
                except ValueError as ve:
                    candidates.append(text)
                    validation_errors.append(str(ve))
        except ValueError as ve:
            raise ve
        except Exception as gemini_err:
            print(f"Gemini vision OCR fallback failed: {str(gemini_err)}")
            validation_errors.append(f"Gemini Vision execution error: {str(gemini_err)}")

    # Check validation failures
    if candidates:
        raise ValueError(validation_errors[-1])

    print("Using local mock clinical text fallback...")
    return get_mock_image_text(), True

def compare_biomarkers_with_db(biomarkers: Dict[str, Dict], db: Session) -> List[schemas.MetricAnalysis]:
    """
    Service Function 3: Database Comparison
    Queries the SQLite reference database for each biomarker extracted,
    tags each value as 'Low', 'Normal', or 'High' prioritizing dynamic reference intervals if present.
    """
    from gemini_service import parse_reference_interval
    
    db_ranges = db.query(models.ReferenceRange).all()
    analyzed_metrics = []
    
    for key, item in biomarkers.items():
        if isinstance(item, dict):
            val = item.get("value")
            ref_interval = item.get("reference_interval")
            unit_override = item.get("unit")
            confidence = item.get("confidence", 0.95)
        else:
            val = float(item) if item is not None else 0.0
            ref_interval = None
            unit_override = None
            confidence = 0.95

        if confidence is None:
            confidence = 0.95
            
        is_low_conf = confidence < 0.80
        
        # Find matching standard range by biomarker_name or alias
        matched_range = None
        for db_range in db_ranges:
            aliases = [a.strip().lower() for a in (db_range.alias_names or "").split(",") if a.strip()]
            if (db_range.biomarker_name.lower() == key.lower() or 
                    key.lower() in aliases):
                matched_range = db_range
                break
                
        # 1. Parse dynamic reference range if available
        dyn_min, dyn_max = None, None
        is_dynamic = False
        if ref_interval:
            dyn_min, dyn_max = parse_reference_interval(ref_interval)
            if dyn_min is not None or dyn_max is not None:
                is_dynamic = True
                
        # 2. Determine units
        unit = unit_override if unit_override else (matched_range.unit if matched_range else "units")
        
        # 3. Determine description
        if matched_range:
            description = matched_range.description
            if is_dynamic:
                description = f"[Dynamic Ref Interval] Evaluated using report bounds ({ref_interval}). {description}"
        else:
            description = f"Biomarker analyzed using standard clinical reference guidelines ({ref_interval})."
            
        # 4. Perform evaluation
        if is_dynamic:
            # Fallback for open-ended boundaries
            min_bound = dyn_min if dyn_min is not None else (matched_range.min_normal if matched_range else 0.0)
            max_bound = dyn_max if dyn_max is not None else (matched_range.max_normal if matched_range else 99999.0)
        else:
            min_bound = matched_range.min_normal if matched_range else 0.0
            max_bound = matched_range.max_normal if matched_range else 0.0
            
        if matched_range or is_dynamic:
            if val < min_bound:
                status = "Low"
            elif val > max_bound:
                status = "High"
            else:
                status = "Normal"
        else:
            status = "Normal"
            
        # Standardize biomarker name to database name if matched
        biomarker_name = matched_range.biomarker_name if matched_range else key
        
        # 5. Critical Emergency Red Flag Panic Threshold Checks
        is_critical = False
        critical_reason = None
        bio_lower = biomarker_name.lower()
        
        if bio_lower in ["platelets", "plt", "platelet"]:
            if val < 20.0:  # < 20,000 / uL
                is_critical = True
                critical_reason = f"CRITICAL BLEEDING RISK: Platelet count ({val} 10^3/uL) is below emergency threshold (< 20.0 10^3/uL)."
        elif bio_lower in ["hemoglobin", "hb", "hgb"]:
            if val < 6.5:   # < 6.5 g/dL
                is_critical = True
                critical_reason = f"CRITICAL ANEMIA EMERGENCY: Hemoglobin ({val} g/dL) is below life-safety threshold (< 6.5 g/dL)."
        elif bio_lower in ["fasting", "fasting glucose", "glucose", "fbs"]:
            if val > 300.0:
                is_critical = True
                critical_reason = f"CRITICAL HYPERGLYCEMIA ALERT: Fasting Glucose ({val} mg/dL) exceeds emergency limit (> 300 mg/dL)."
            elif val < 40.0:
                is_critical = True
                critical_reason = f"CRITICAL HYPOGLYCEMIA ALERT: Fasting Glucose ({val} mg/dL) is below emergency limit (< 40 mg/dL)."
        elif bio_lower in ["potassium", "k+"]:
            if val < 2.5:
                is_critical = True
                critical_reason = f"CRITICAL HYPOKALEMIA ALERT: Serum Potassium ({val} mEq/L) is below cardiac safety threshold (< 2.5 mEq/L)."
            elif val > 6.5:
                is_critical = True
                critical_reason = f"CRITICAL HYPERKALEMIA ALERT: Serum Potassium ({val} mEq/L) exceeds cardiac safety threshold (> 6.5 mEq/L)."
        elif bio_lower in ["creatinine", "cre"]:
            if val > 5.0:
                is_critical = True
                critical_reason = f"CRITICAL RENAL CRISIS ALERT: Serum Creatinine ({val} mg/dL) exceeds acute renal safety limit (> 5.0 mg/dL)."
        elif bio_lower in ["alt", "sgpt", "ast", "sgot"]:
            if val > 1000.0:
                is_critical = True
                critical_reason = f"CRITICAL HEPATIC INJURY ALERT: Liver enzyme {biomarker_name} ({val} U/L) exceeds acute injury limit (> 1000 U/L)."
        elif bio_lower in ["tsh"]:
            if val > 50.0:
                is_critical = True
                critical_reason = f"CRITICAL THYROID CRISIS: TSH ({val} uIU/mL) indicates severe endocrine crisis (> 50 uIU/mL)."
        
        analyzed_metrics.append(
            schemas.MetricAnalysis(
                biomarker_name=biomarker_name,
                value=val,
                unit=unit,
                min_normal=min_bound if min_bound != float('inf') else 99999.0,
                max_normal=max_bound if max_bound != float('inf') else 99999.0,
                status=status,
                confidence=round(float(confidence), 2),
                is_low_confidence=is_low_conf,
                is_critical=is_critical,
                critical_reason=critical_reason,
                description=description
            )
        )
            
    return analyzed_metrics


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Lab Report Analyzer API", "status": "running"}

@app.get("/api/v1/ranges", response_model=List[schemas.ReferenceRangeResponse])
def get_reference_ranges(db: Session = Depends(get_db)):
    """
    Fetch all standard clinical reference ranges from the SQLite database.
    """
    ranges = db.query(models.ReferenceRange).all()
    return ranges

@app.post("/api/analyze-report", response_model=schemas.AnalysisResponse)
async def analyze_report_v2(
    file: UploadFile = File(...),
    language: str = Form("English"),
    x_gemini_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """
    End-to-End Holistic Processing Pipeline:
    1. Read and extract raw text from PDF.
    2. Structurally parse biomarker mappings via Native Gemini Model.
    3. Compare values against SQLite reference ranges and tag as 'Low', 'Normal', or 'High'.
    4. Run holistic Disease Risk Predictor and Patient Simplifier in the chosen Language.
    """
    filename_lower = file.filename.lower()
    is_pdf = filename_lower.endswith('.pdf')
    is_image = filename_lower.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'))
        
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
    # Pipeline Step 1: Text Extraction
    is_mock_fallback = False
    try:
        if is_pdf:
            try:
                raw_text = extract_text_from_pdf(contents)
                if not raw_text or not raw_text.strip():
                    raise ValueError("Empty PDF text extracted.")
            except Exception as pdf_err:
                print(f"Warning: PDF extraction failed ({pdf_err}). Falling back to mock clinical text.")
                raw_text = get_mock_image_text()
                is_mock_fallback = True
        elif is_image:
            raw_text, is_mock_fallback = extract_text_from_image(contents, api_key=x_gemini_api_key)
        else:
            # Try decoding as plain text
            try:
                raw_text = contents.decode("utf-8")
                validate_extracted_text(raw_text)
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload PDF, image, or plain text documents."
                )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Immediately scrub any PII before processing or storage
    from anonymizer import anonymize_text
    raw_text = anonymize_text(raw_text)
        
    # Pipeline Step 2: Native Gemini Structured Extraction
    extracted_biomarkers = extract_biomarkers_with_gemini(raw_text, api_key=x_gemini_api_key)
    
    if not extracted_biomarkers:
        if is_mock_fallback:
            # Fallback to mock dictionary if OCR/PDF text extraction failed completely and we are in demo mode
            extracted_biomarkers = {
                "Hemoglobin": 11.2,
                "WBC": 7.5,
                "Platelets": 130.0,
                "RBC": 4.8,
                "Neutrophils": 78.0,
                "HbA1c": 5.8,
                "Fasting": 108.0,
                "Total Cholesterol": 245.0,
                "HDL": 35.0,
                "LDL": 155.0,
                "ALT": 42.0,
                "Creatinine": 1.4,
                "EGFR": 82.0,
                "TSH": 5.2,
                "Free T4": 1.1,
                "C-Reactive Protein": 45.0
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No clinical biomarkers could be parsed from your document. "
                    "Please verify that the document is a valid medical laboratory report containing numeric values, "
                    "or configure a Gemini API key in Settings for clinical-grade AI parsing."
                )
            )
            
    # Pipeline Step 3: Database Comparison & Tagging
    analyzed_metrics = compare_biomarkers_with_db(extracted_biomarkers, db)
    
    # Convert Pydantic schemas to dictionary format for prompt context
    # Convert Pydantic schemas to dictionary format for prompt context
    metrics_list = [m.model_dump() for m in analyzed_metrics]
    
    # Pipeline Step 4: Holistic Risk Analysis, Simplification & Language Translation
    holistic_analysis = analyze_holistic_risks(metrics_list, language, api_key=x_gemini_api_key)
    
    # Save the report if the user is authenticated
    if user_id:
        try:
            db_report = models.UploadedReport(
                user_id=user_id,
                filename=file.filename,
                patient_summary=holistic_analysis.get("patient_summary", ""),
                disease_risks=json.dumps(holistic_analysis.get("disease_risks", [])),
                language=language
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            # Save individual metrics
            for m in analyzed_metrics:
                db_metric = models.ReportMetric(
                    report_id=db_report.id,
                    biomarker_name=m.biomarker_name,
                    value=m.value,
                    unit=m.unit,
                    min_normal=m.min_normal,
                    max_normal=m.max_normal,
                    status=m.status,
                    confidence=m.confidence,
                    is_low_confidence=m.is_low_confidence,
                    is_critical=m.is_critical,
                    critical_reason=m.critical_reason,
                    description=m.description
                )
                db.add(db_metric)
            db.commit()
            print(f"Successfully saved uploaded report to DB under user ID {user_id}!")
        except Exception as db_err:
            db.rollback()
            print(f"Failed to save report to database: {str(db_err)}")
            
    critical_alerts = [m.critical_reason for m in analyzed_metrics if m.is_critical and m.critical_reason]

    return schemas.AnalysisResponse(
        filename=file.filename,
        status="success",
        metrics=analyzed_metrics,
        disease_risks=holistic_analysis.get("disease_risks", []),
        has_critical_alert=len(critical_alerts) > 0,
        critical_alerts=critical_alerts,
        patient_summary=holistic_analysis.get("patient_summary", ""),
        language=language,
        is_mock_fallback=is_mock_fallback
    )

# Alias route to ensure frontend backward-compatibility
@app.post("/api/v1/analyze", response_model=schemas.AnalysisResponse)
async def analyze_report_v1(
    file: UploadFile = File(...),
    language: str = Form("English"),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    return await analyze_report_v2(file=file, language=language, db=db, user_id=user_id)

@app.get("/api/metrics/history")
def get_metrics_history(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Pulls all verified past lab uploads for the logged-in user ID and
    formats them as a chronological array sorted by date, ready for data visualization.
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials are required to view report history."
        )
        
    # Fetch user's reports ordered by upload_date ascending
    reports = db.query(models.UploadedReport).filter(
        models.UploadedReport.user_id == user_id
    ).order_by(models.UploadedReport.upload_date.asc()).all()
    
    formatted_reports = []
    for r in reports:
        # Calculate normal and abnormal metric counts
        normal_count = 0
        abnormal_count = 0
        
        metrics_list = []
        for m in r.metrics:
            status_lower = m.status.lower()
            if status_lower in ["low", "high"]:
                abnormal_count += 1
            else:
                normal_count += 1
                
            metrics_list.append({
                "biomarker_name": m.biomarker_name,
                "value": m.value,
                "unit": m.unit,
                "min_normal": m.min_normal,
                "max_normal": m.max_normal,
                "status": m.status,
                "description": m.description
            })
            
        try:
            disease_risks = json.loads(r.disease_risks) if r.disease_risks else []
        except Exception:
            disease_risks = []
            
        formatted_reports.append({
            "id": f"report-{r.id}",
            "filename": r.filename,
            "date": r.upload_date.strftime("%Y-%m-%d"),
            "normal_count": normal_count,
            "abnormal_count": abnormal_count,
            "disease_risks": disease_risks,
            "patient_summary": r.patient_summary,
            "metrics": metrics_list
        })
        
    return formatted_reports

@app.get("/api/user/profile")
def get_user_profile(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    GET /api/user/profile
    Retrieves current user baseline clinical parameters and biological profile details.
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Session authentication required to access this endpoint."
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
        
    return {
        "full_name": user.full_name or "",
        "age": user.age or 0,
        "biological_sex": user.biological_sex or "",
        "weight_kg": user.weight_kg or 0.0,
        "height_cm": user.height_cm or 0.0,
        "chronic_conditions": [c.strip() for c in (user.chronic_conditions or "").split(",") if c.strip()],
        "primary_health_goal": user.primary_health_goal or "",
        "is_onboarded": user.is_onboarded
    }

@app.put("/api/user/profile")
def update_user_profile(
    profile: schemas.ProfileUpdateSchema,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    PUT /api/user/profile
    Saves initial onboarding user medical parameters and biological profile constraints inside SQLite,
    flagging the user profile as is_onboarded = True.
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Session authentication required to access this endpoint."
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
        
    # Bind incoming profile schema parameters
    user.full_name = profile.full_name.strip()
    user.age = profile.age
    user.biological_sex = profile.biological_sex.strip()
    user.weight_kg = profile.weight_kg
    user.height_cm = profile.height_cm
    
    # Conditionally format list to comma-separated string
    user.chronic_conditions = ",".join([c.strip() for c in profile.chronic_conditions if c.strip()])
    user.primary_health_goal = profile.primary_health_goal.strip()
    
    # Set onboarded flag
    user.is_onboarded = True
    
    try:
        db.commit()
        db.refresh(user)
        return {
            "status": "success",
            "message": "Clinical onboarding profile synchronized successfully.",
            "is_onboarded": user.is_onboarded
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Profile synchronization failed: {str(e)}"
        )


@app.post("/api/v1/reports/export-pdf")
def export_report_pdf(payload: schemas.AnalysisResponse):
    """
    POST /api/v1/reports/export-pdf
    Generates and streams a clean 1-page Patient Health Summary PDF document.
    """
    from pdf_exporter import generate_patient_summary_pdf
    
    metrics_dicts = [m.model_dump() for m in payload.metrics]
    
    pdf_bytes = generate_patient_summary_pdf(
        filename=payload.filename,
        metrics=metrics_dicts,
        patient_summary=payload.patient_summary,
        disease_risks=payload.disease_risks,
        language=payload.language,
        has_critical_alert=payload.has_critical_alert,
        critical_alerts=payload.critical_alerts
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=AXON_Clinical_Health_Summary_{payload.language}.pdf"
        }
    )


@app.post("/api/v1/reports/compare-trends", response_model=schemas.TrendComparisonResponse)
def compare_report_trends(
    request: schemas.TrendComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/reports/compare-trends
    Compares two historical lab reports and computes delta changes (e.g. Fasting Glucose dropped by 12 mg/dL).
    """
    base_report = db.query(models.UploadedReport).filter(models.UploadedReport.id == request.baseline_report_id).first()
    curr_report = db.query(models.UploadedReport).filter(models.UploadedReport.id == request.current_report_id).first()

    if not base_report or not curr_report:
        raise HTTPException(status_code=404, detail="One or both of the specified reports were not found.")

    base_date = base_report.upload_date.strftime("%B %Y")
    curr_date = curr_report.upload_date.strftime("%B %Y")

    base_map = {m.biomarker_name.lower(): m for m in base_report.metrics}
    deltas = []

    for curr in curr_report.metrics:
        b_name = curr.biomarker_name
        b_lower = b_name.lower()
        if b_lower in base_map:
            base = base_map[b_lower]
            v_base = base.value
            v_curr = curr.value
            diff = round(v_curr - v_base, 2)
            pct = round((diff / v_base) * 100, 1) if v_base != 0 else 0.0

            is_bad_param = b_lower in [
                "fasting", "fasting glucose", "hba1c", "total cholesterol", "ldl",
                "triglycerides", "alt", "ast", "creatinine", "tsh", "c-reactive protein", "crp"
            ]

            if abs(diff) < 0.05:
                direction = "stable"
                insight = f"Your {b_name} remained stable at {v_curr} {curr.unit} compared to your {base_date} report."
            elif (diff < 0 and is_bad_param) or (diff > 0 and not is_bad_param):
                direction = "improved"
                action_word = "dropped" if diff < 0 else "increased"
                insight = f"Great progress! Your {b_name} {action_word} by {abs(diff)} {curr.unit} ({v_base} -> {v_curr} {curr.unit}) compared to your {base_date} report. Keep up the lifestyle changes!"
            else:
                direction = "worsened"
                action_word = "rose" if diff > 0 else "dipped"
                insight = f"Attention: Your {b_name} {action_word} by {abs(diff)} {curr.unit} ({v_base} -> {v_curr} {curr.unit}) compared to your {base_date} report."

            deltas.append(schemas.BiomarkerDelta(
                biomarker_name=b_name,
                baseline_value=v_base,
                current_value=v_curr,
                delta_value=diff,
                percentage_change=pct,
                unit=curr.unit,
                direction=direction,
                insight_text=insight
            ))

    improved_count = sum(1 for d in deltas if d.direction == "improved")
    worsened_count = sum(1 for d in deltas if d.direction == "worsened")

    summary = f"Longitudinal comparison ({base_date} → {curr_date}): {improved_count} parameters improved, {worsened_count} require ongoing monitoring."

    return schemas.TrendComparisonResponse(
        baseline_date=base_date,
        current_date=curr_date,
        deltas=deltas,
        longitudinal_summary=summary
    )



