import io
import os
import re
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Applies image preprocessing (Grayscale, Contrast Amplification, Edge Sharpening)
    to maximize OCR character legibility for physical lab report scans.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")  # Grayscale
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Amplify contrast
        image = image.filter(ImageFilter.SHARPEN)  # Edge sharpen
        return image
    except Exception as e:
        raise ValueError(f"Failed to preprocess image for local OCR: {str(e)}")

def validate_extracted_medical_text(text: str) -> bool:
    """
    Validates whether extracted OCR text contains recognizable medical lab report keywords.
    """
    if not text or len(text.strip()) < 15:
        return False
    text_lower = text.lower()
    keywords = [
        "hemoglobin", "haemoglobin", "hb", "wbc", "rbc", "platelet", "cholesterol", 
        "glucose", "hba1c", "tsh", "creatinine", "urea", "bilirubin", "alt", "ast", 
        "report", "patient", "reference", "interval", "range", "result", "value", 
        "unit", "specimen", "blood", "serum", "clinical", "laboratory", "analysis", "test"
    ]
    matches = sum(1 for kw in keywords if kw in text_lower)
    return matches > 0

def get_fallback_lab_text() -> str:
    """
    Returns a standard local sample clinical report text when OCR engines return unreadable binary noise.
    """
    return (
        "==================================================\n"
        "AXON LOCAL CLINICAL LABORATORY REPORT SAMPLE\n"
        "==================================================\n"
        "Biomarker            Value     Unit      Reference Range\n"
        "Hemoglobin:          10.5      g/dL      (12.0 - 16.0)\n"
        "WBC Count:           7.5       10^3/uL   (4.0 - 11.0)\n"
        "Platelet Count:      130.0     10^3/uL   (150 - 450)\n"
        "Fasting Glucose:     145.0     mg/dL     (70.0 - 100.0)\n"
        "HbA1c:               6.2       %         (4.0 - 5.6)\n"
        "Total Cholesterol:   245.0     mg/dL     (125 - 200)\n"
        "HDL Cholesterol:     35.0      mg/dL     (40 - 60)\n"
        "LDL Cholesterol:     155.0     mg/dL     (0 - 100)\n"
        "Triglycerides:       185.0     mg/dL     (35 - 150)\n"
        "Serum Creatinine:    1.4       mg/dL     (0.6 - 1.2)\n"
        "Serum TSH:           6.2       uIU/mL    (0.4 - 4.5)\n"
        "ALT (SGPT):          45.0      U/L       (7 - 56)\n"
        "C-Reactive Protein:  14.5      mg/L      (0.0 - 5.0)\n"
        "==================================================\n"
    )

def extract_text_locally(
    file_bytes: bytes, 
    is_pdf: bool = False, 
    is_image: bool = True
) -> Tuple[str, str, bool]:
    """
    Local OCR Extraction Pipeline:
    1. Tesseract OCR (pytesseract)
    2. EasyOCR Fallback
    3. PDF Text Extraction (pypdf)
    4. Local Structured Fallback Text

    Returns:
        Tuple[raw_text, ocr_engine_used, is_fallback]
    """
    # Step 1: If PDF, attempt direct text extraction first
    if is_pdf:
        try:
            from pypdf import PdfReader
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            pdf_text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pdf_text += t + "\n"
            if validate_extracted_medical_text(pdf_text):
                return pdf_text, "PyPDF Local Engine", False
            elif pdf_text and pdf_text.strip():
                return pdf_text, "PyPDF Local Engine", False
        except Exception as e:
            print(f"Local PyPDF extraction notice: {e}")

    # Step 2: Attempt Tesseract OCR
    if is_image or is_pdf:
        try:
            import pytesseract
            processed_img = preprocess_image(file_bytes)
            tes_text = pytesseract.image_to_string(processed_img)
            if validate_extracted_medical_text(tes_text):
                return tes_text, "Tesseract Local OCR", False
        except Exception as e:
            print(f"Tesseract OCR not available or failed: {e}")

    # Step 3: Attempt EasyOCR
    if is_image or is_pdf:
        try:
            import easyocr
            import numpy as np
            processed_img = preprocess_image(file_bytes)
            img_np = np.array(processed_img)
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            results = reader.readtext(img_np)
            easy_text = "\n".join([r[1] for r in results])
            if validate_extracted_medical_text(easy_text):
                return easy_text, "EasyOCR Local Engine", False
        except Exception as e:
            print(f"EasyOCR not available or failed: {e}")

    # Step 4: If decoding plain text directly works
    try:
        text_decoded = file_bytes.decode("utf-8", errors="ignore")
        if validate_extracted_medical_text(text_decoded):
            return text_decoded, "Direct Local Text Parser", False
    except Exception:
        pass

    # Step 5: Safe local sample report fallback
    print("Using local sample clinical report text fallback...")
    return get_fallback_lab_text(), "AXON Local Sample Fallback", True
