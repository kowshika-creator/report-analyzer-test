# -*- coding: utf-8 -*-
import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field
import google.generativeai as genai
from schemas import ScanReportAnalysis

class ExtractedBiomarker(BaseModel):
    value: float = Field(description="The numerical floating-point value of the biomarker.")
    reference_interval: Optional[str] = Field(
        None, 
        description="The biological reference interval/range (e.g., '12.0 - 17.5', '0.4 - 1.0', '< 6.0', '5.0 - 8.0') printed next to the biomarker on the document. If not printed, please output the standard accepted clinical reference range for this biomarker."
    )
    unit: Optional[str] = Field(
        None,
        description="The unit of measurement (e.g., 'g/dL', 'mg/dL', 'U/L', 'uIU/mL', 'ng/mL') printed next to the biomarker. If not printed, please output the standard clinical unit of measurement for this biomarker."
    )
    confidence: Optional[float] = Field(
        0.95,
        description="Confidence score between 0.00 and 1.00 based on image contrast, character legibility, and line clarity. Set < 0.80 if image line is smudged or blurry."
    )

class BiomarkerExtraction(BaseModel):
    biomarkers: Dict[str, ExtractedBiomarker] = Field(
        description="A dictionary mapping biomarker names (e.g. 'Hemoglobin', 'TSH', 'Total Cholesterol') to their extracted details."
    )

class HolisticAnalysis(BaseModel):
    disease_risks: List[str] = Field(
        description="List of identified disease risks or health patterns, translated to the requested language."
    )
    patient_summary: str = Field(
        description="Comforting, ultra-simple, non-technical summary explaining the findings to the patient, translated to the requested language."
    )

def parse_reference_interval(interval_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses a reference interval string (e.g. "12.0 - 17.5", "< 6.0", "> 40", "Negative / Less than 6.0")
    and extracts the lower and upper bounds as floats.
    """
    if not interval_str:
        return None, None
    
    interval_str = interval_str.strip().lower()
    
    # Check for formats like "< 6.0", "less than 6.0", "negative / less than 6.0", "up to 10"
    if "<" in interval_str or "less than" in interval_str or "up to" in interval_str:
        match = re.search(r'(?:<|less than|up to)\s*([0-9]+(?:\.[0-9]+)?)', interval_str)
        if match:
            return 0.0, float(match.group(1))
            
    # Check for formats like "> 40" or "greater than 40"
    if ">" in interval_str or "greater than" in interval_str:
        match = re.search(r'(?:>|greater than)\s*([0-9]+(?:\.[0-9]+)?)', interval_str)
        if match:
            return float(match.group(1)), float('inf')
            
    # Check for formats like "12.0 - 17.5" or "12.0-17.5" or "12.0 to 17.5"
    match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:-|to)\s*([0-9]+(?:\.[0-9]+)?)', interval_str)
    if match:
        return float(match.group(1)), float(match.group(2))
        
    return None, None

def generate_gemini_content(api_key: str, prompt_parts: Any, generation_config: Any = None) -> Any:
    """
    Attempts content generation across candidate Gemini model names
    (gemini-3.6-flash, gemini-3.5-flash, gemini-2.5-flash, gemini-2.0-flash, gemini-flash-latest)
    for resilient API compatibility across different account tiers.
    """
    genai.configure(api_key=api_key)
    candidate_models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    last_err = None
    for m_name in candidate_models:
        try:
            model = genai.GenerativeModel(m_name)
            if generation_config:
                return model.generate_content(prompt_parts, generation_config=generation_config)
            else:
                return model.generate_content(prompt_parts)
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("Failed to invoke Gemini API with candidate models.")

def get_working_gemini_model(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-3.6-flash")

def extract_biomarkers_with_gemini(raw_text: str, api_key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Calls the native Gemini model to parse raw lab report text and return a 
    structured JSON mapping of biomarker names to their numerical values, reference intervals, and units.
    Provides a resilient regex-based fallback if the API key is missing or calls fail.
    Returns a unified dict format: { "BiomarkerName": {"value": float, "reference_interval": str|None, "unit": str|None} }
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    extracted_data = {}
    if not api_key:
        print("Warning: Gemini API key missing. Falling back to local clinical regex matching.")
        raw_extracted = run_regex_fallback_parser(raw_text)
        extracted_data = raw_extracted
    else:
        try:
            prompt = (
                "You are an expert medical data structuring assistant. Your task is to extract all medical biomarkers "
                "from any type of clinical laboratory report (including blood tests, urine analyses, thyroid profiles, "
                "vitamin panels, metabolic tests, etc.) from the raw text provided below.\n\n"
                "Rules:\n"
                "1. Map each recognized biomarker name (e.g., 'Hemoglobin', 'Fasting Sugar', 'Urine pH', 'Vitamin D3', 'TSH') "
                "to its extracted details (numerical float value, biological reference interval string, and unit string).\n"
                "2. For the 'reference_interval', extract the exact reference range printed next to the biomarker in the text. "
                "If no reference interval is listed in the document for an extracted biomarker, please provide the standard "
                "accepted clinical default reference range/interval for that biomarker based on standard medical guidelines.\n"
                "3. For the 'unit', extract the unit of measurement printed in the text. If not found, please provide the standard "
                "clinical unit of measurement for that biomarker.\n"
                "4. Do not invent any biomarkers or values that are not in the text. Only extract what is physically listed in the text.\n\n"
                "Return a JSON object matching this exact format:\n"
                "{\n"
                '  "biomarkers": {\n'
                '    "BiomarkerName": {\n'
                '      "value": 12.5,\n'
                '      "reference_interval": "12.0 - 17.5",\n'
                '      "unit": "g/dL",\n'
                '      "confidence": 0.95\n'
                "    }\n"
                "  }\n"
                "}\n\n"
                f"Raw Lab Report Text:\n{raw_text}"
            )
            
            response = generate_gemini_content(
                api_key,
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            result_json = json.loads(response.text)
            extracted_data = result_json.get("biomarkers", {})
            
        except Exception as e:
            print(f"Error during native Gemini processing: {e}. Falling back to local clinical regex matching.")
            extracted_data = run_regex_fallback_parser(raw_text)
            
    # Normalize the output dictionary so every value is a standardized dictionary
    normalized = {}
    for k, v in extracted_data.items():
        if isinstance(v, dict):
            try:
                conf = float(v.get("confidence", 0.95))
            except (ValueError, TypeError):
                conf = 0.95
            try:
                normalized[k] = {
                    "value": float(v.get("value")),
                    "reference_interval": v.get("reference_interval"),
                    "unit": v.get("unit"),
                    "confidence": conf
                }
            except (ValueError, TypeError):
                pass
        else:
            try:
                normalized[k] = {
                    "value": float(v),
                    "reference_interval": None,
                    "unit": None,
                    "confidence": 0.95
                }
            except (ValueError, TypeError):
                pass
                
    return normalized



def analyze_holistic_risks(metrics: List[Dict], language: str, api_key: Optional[str] = None) -> Dict:
    """
    Calls Gemini to analyze extracted parameters holistically for:
    1. Disease Risk Predictor: Clinical pattern recognition across multiple variables.
    2. Patient Simplifier: Comforting patient summary in plain non-technical language.
    3. Multilingual Translation: Output the summary and risks in English, Tamil, 
    Hindi, or Telugu.
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    # Format metrics for prompting
    metrics_str = ""
    for m in metrics:
        metrics_str += f"- {m['biomarker_name']}: {m['value']} {m['unit']} (Status: {m['status']}, Normal Range: {m['min_normal']} - {m['max_normal']})\n"

    if not api_key:
        print("Warning: Gemini API key missing. Running local rule-based disease predictor and translation.")
        return run_local_holistic_fallback(metrics, language)

    try:
        prompt = (
            "You are an expert clinical consultant and compassionate patient advocate.\n"
            "Review these clinical laboratory findings (which could include blood test metrics, urine parameters, thyroid values, vitamins, etc.) holistically:\n"
            f"{metrics_str}\n"
            "Task 1: Disease Risk Predictor\n"
            "Look for interrelated clinical patterns across metrics and identify possible health risks (e.g., if Glucose is high and Total Cholesterol is high, note potential Metabolic Syndrome risk. If ALT/AST are high, note Liver Stress risk).\n"
            "CRITICAL SPECIFICATION: If you observe a combination of elevated C-Reactive Protein / CRP (e.g. > 40 mg/L), elevated Neutrophils (e.g. > 75%), and dipping/low Platelets (e.g. < 150.0 10^3/uL / 1.5 Lakhs), you MUST flag an 'Acute Inflammatory/Infectious Response Pattern' and explain it in comforting, non-alarmist, patient-friendly terms.\n\n"
            "Task 2: Patient Simplifier\n"
            "Explain what these findings mean to the patient in ultra-simple, comforting, non-technical language. Act like an empathetic doctor explaining results clearly, without confusing jargon, giving minor lifestyle advice.\n\n"
            "Task 3: Multilingual Support\n"
            f"You MUST translate the final list of disease risks AND the patient simplified summary into this language: {language}.\n\n"
            "Return the final payload as a JSON object matching this exact format:\n"
            "{\n"
            '  "disease_risks": ["Risk 1", "Risk 2"],\n'
            '  "patient_summary": "Summary text..."\n'
            "}"
        )
        
        response = generate_gemini_content(
            api_key,
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return {
            "disease_risks": result.get("disease_risks", []),
            "patient_summary": result.get("patient_summary", "")
        }
    except Exception as e:
        print(f"Error calling Gemini for holistic analysis: {e}. Executing local fallback.")
        return run_local_holistic_fallback(metrics, language)


def run_local_holistic_fallback(metrics: List[Dict], language: str) -> Dict:
    """
    Expert rule-based fallback system simulating disease risk prediction and 
    empathetic patient summaries in 4 languages: English, Tamil, Hindi, Telugu.
    """
    # 1. Evaluate patterns
    val_map = {m['biomarker_name'].lower(): m for m in metrics}
    
    low_indicators = [m['biomarker_name'] for m in metrics if m['status'].lower() == 'low']
    high_indicators = [m['biomarker_name'] for m in metrics if m['status'].lower() == 'high']
    
    risks = []
    
    # Pattern A: Metabolic / Diabetes
    has_high_glucose = "fasting" in val_map and val_map["fasting"]["status"].lower() == "high"
    has_high_chol = "total cholesterol" in val_map and val_map["total cholesterol"]["status"].lower() == "high"
    has_high_trig = "triglycerides" in val_map and val_map["triglycerides"]["status"].lower() == "high"
    has_high_hba1c = "hba1c" in val_map and val_map["hba1c"]["status"].lower() == "high"
    
    if has_high_glucose or has_high_hba1c:
        if has_high_chol or has_high_trig:
            risks.append("Metabolic Syndrome Pattern (Cardiovascular & Diabetes Risk)")
        else:
            risks.append("Impaired Glycemia / Prediabetes Risk")
            
    # Pattern B: Anemia
    has_low_hb = "hemoglobin" in val_map and val_map["hemoglobin"]["status"].lower() == "low"
    has_low_rbc = "rbc" in val_map and val_map["rbc"]["status"].lower() == "low"
    if has_low_hb or has_low_rbc:
        risks.append("Iron Deficiency Anemia (Low Oxygen Carrier Pattern)")
        
    # Pattern C: Thyroid
    has_high_tsh = "tsh" in val_map and val_map["tsh"]["status"].lower() == "high"
    has_low_tsh = "tsh" in val_map and val_map["tsh"]["status"].lower() == "low"
    if has_high_tsh:
        risks.append("Hypothyroidism Pattern (Underactive Thyroid Activity)")
    elif has_low_tsh:
        risks.append("Hyperthyroidism Pattern (Overactive Thyroid Activity)")
        
    # Pattern D: Liver
    has_high_alt = "alt" in val_map and val_map["alt"]["status"].lower() == "high"
    has_high_ast = "ast" in val_map and val_map["ast"]["status"].lower() == "high"
    if has_high_alt or has_high_ast:
        risks.append("Hepatic Cell Stress (Liver Function Inflammatory Risk)")
        
    # Pattern E: Kidney
    has_high_creat = "creatinine" in val_map and val_map["creatinine"]["status"].lower() == "high"
    has_low_egfr = "egfr" in val_map and val_map["egfr"]["status"].lower() == "low"
    if has_high_creat or has_low_egfr:
        risks.append("Renal Stress (Decreased Glomerular Filtration Pattern)")

    # Pattern F: Acute Inflammatory/Infectious Response Pattern
    has_high_crp = "c-reactive protein" in val_map and val_map["c-reactive protein"]["value"] > 40
    has_high_neut = "neutrophils" in val_map and val_map["neutrophils"]["value"] > 75
    has_low_plat = "platelets" in val_map and val_map["platelets"]["value"] < 150
    has_acute_pattern = has_high_crp and has_high_neut and has_low_plat
    if has_acute_pattern:
        risks.append("Acute Inflammatory/Infectious Response Pattern")

    # General fallback risk item if there are other abnormal parameters
    other_abnormal = [m['biomarker_name'] for m in metrics if m['status'].lower() in ['low', 'high'] and m['biomarker_name'].lower() not in ['fasting', 'total cholesterol', 'hemoglobin', 'tsh', 'alt', 'ast', 'creatinine', 'neutrophils', 'platelets', 'c-reactive protein']]
    if other_abnormal:
        risks.append(f"Atypical levels detected in: {', '.join(other_abnormal)}. Please review with your physician.")

    if not risks:
        risks.append("No critical multi-metric clinical patterns identified. Excellent baseline health.")
    # 2. Empathy Synthesizer and Translator
    lang = language.strip().lower()
    
    translations = {
        "tamil": {
            "risks_map": {
                "Metabolic Syndrome Pattern (Cardiovascular & Diabetes Risk)": "வளர்சிதை மாற்ற நோய்க்குறி முறை (இருதய மற்றும் நீரிழிவு ஆபத்து)",
                "Impaired Glycemia / Prediabetes Risk": "பலவீனமான கிளைசீமியா / நீரிழிவு நோய் ஆபத்து",
                "Iron Deficiency Anemia (Low Oxygen Carrier Pattern)": "இரும்புச்சத்து குறைபாடு இரத்த சோகை (குறைந்த ஆக்ஸிஜன் கடத்தி முறை)",
                "Hypothyroidism Pattern (Underactive Thyroid Activity)": "ஹைப்போதைராய்டிசம் முறை (செயலற்ற தைராய்டு செயல்பாடு)",
                "Hyperthyroidism Pattern (Overactive Thyroid Activity)": "ஹைப்பர் தைராய்டிசம் முறை (அதிவேக தைராய்டு செயல்பாடு)",
                "Hepatic Cell Stress (Liver Function Inflammatory Risk)": "கல்லீரல் செல் அழுத்தம் (கல்லீரல் செயல்பாடு அழற்சி ஆபத்து)",
                "Renal Stress (Decreased Glomerular Filtration Pattern)": "சிறுநீரக அழுத்தம் (குறைந்த குளோமருலர் வடிகட்டுதல் முறை)",
                "Acute Inflammatory/Infectious Response Pattern": "தீவிர அழற்சி/தொற்று எதிர்வினை முறை",
                "No critical multi-metric clinical patterns identified. Excellent baseline health.": "முக்கியமான மருத்துவ முறைகள் எதுவும் கண்டறியப்படவில்லை. சிறந்த அடிப்படை ஆரோக்கியம்."
            },
            "summary": (
                "வணக்கம். உங்கள் இரத்தப் பரிசோதனை அறிக்கையை நாங்கள் விரிவாக பகுப்பாய்வு செய்துள்ளோம். "
                f"சில அளவுகள் (அதிகரித்த {', '.join(high_indicators) if high_indicators else 'எதுவும் இல்லை'} மற்றும் "
                f"குறைந்த {', '.join(low_indicators) if low_indicators else 'எதுவும் இல்லை'} அளவுகள்) சாதாரண வரம்பிற்கு வெளியே இருப்பதை நாங்கள் கவனித்தோம். "
                "உடனடியாக கவலைப்படத் தேவையில்லை. சீரான உணவு, போதுமான தண்ணீர் குடிப்பது மற்றும் "
                "இந்த முடிவுகளை விரிவாக மதிப்பாய்வு செய்ய உங்கள் மருத்துவரை அணுகுமாறு நாங்கள் பரிந்துரைக்கிறோம்."
                + (" மேலும், உடலில் அதிகரித்த அழற்சி மற்றும் சற்று குறைந்த பிளேட்லெட்டுகளின் தற்காலிக முறையை நாங்கள் கவனித்தோம், இது உங்கள் உடல் ஒரு தொற்றுக்கு எதிராக தீவிரமாக போராடுகிறது என்பதைக் குறிக்கிறது. இது மிகவும் பொதுவான பாதுகாப்பு வழிமுறையாகும்; நீங்கள் நன்றாக ஓய்வெடுக்கவும், நீரேற்றத்துடன் இருக்கவும், உங்கள் மருத்துவரை அணுகவும் பரிந்துரைக்கிறோம்." if has_acute_pattern else "")
            )
        },
        "telugu": {
            "risks_map": {
                "Metabolic Syndrome Pattern (Cardiovascular & Diabetes Risk)": "మెటబాలిక్ సిండ్రోమ్ సరళి (హృదయ మరియు మధుమేహం ప్రమాదం)",
                "Impaired Glycemia / Prediabetes Risk": "క్షీణించిన గ్లైసీమయా / ప్రీ-డయాబెటిస్ ప్రమాదం",
                "Iron Deficiency Anemia (Low Oxygen Carrier Pattern)": "ఇనుము లోపం రక్తహీనత (తక్కువ ఆక్సిజన్ వాహక సరళి)",
                "Hypothyroidism Pattern (Underactive Thyroid Activity)": "హైపోథైరాయిడిజం సరళి (తక్కువ థైరాయిడ్ కార్యాచరణ)",
                "Hyperthyroidism Pattern (Overactive Thyroid Activity)": "హైపర్ థైరాయిడిజం సరళి (అధిక థైరాయిడ్ కార్యాచరణ)",
                "Hepatic Cell Stress (Liver Function Inflammatory Risk)": "కాలేయ కణాల ఒత్తిడి (కాలేయ పనితీరు తాపజనక ప్రమాదం)",
                "Renal Stress (Decreased Glomerular Filtration Pattern)": "మూత్రపిండాల ఒత్తిడి (తగ్గిన గ్లోమెరులర్ వడపోత సరళి)",
                "Acute Inflammatory/Infectious Response Pattern": "తీవ్రమైన తాపజనక/ఇన్ఫెక్షన్ ప్రతిస్పందన సరళి",
                "No critical multi-metric clinical patterns identified. Excellent baseline health.": "ఎటువంటి క్లిష్టమైన క్లినికల్ నమూనాలు గుర్తించబడలేదు. అద్భుతమైన ఆరోగ్య పునాది."
            },
            "summary": (
                "నమస్కారం. మేము మీ రక్త నివేదికను సమగ్రంగా విశ్లేషించాము. "
                f"కొన్ని విలువలు (ఎక్కువగా ఉన్నవి {', '.join(high_indicators) if high_indicators else 'ఏవీ లేవు'} మరియు "
                f"తక్కువగా ఉన్నవి {', '.join(low_indicators) if low_indicators else 'ఏవీ లేవు'}) సాధారణ పరిధికి వెలుపల ఉన్నట్లు మేము గమనించాము. "
                "వెంటనే ఆందోళన చెందాల్సిన పని లేదు. సమతుల్య ఆహారం తీసుకోవడం, తగినంత నీరు తాగడం మరియు "
                "మీ వైద్యుడిని సంప్రదించి ఈ ఫలితాలను వివరంగా సమీక్షించుకోవాలని మేము సిఫార్సు చేస్తున్నాము."
                + (" అదనంగా, మేము శరీరంలో పెరిగిన వాపు మరియు కొద్దిగా తగ్గిన ప్లేట్‌లెట్ల తాత్కాలిక సరళిని గమనించాము, ఇది మీ శరీరం ఇన్ఫెక్షన్‌తో పోరాడుతోందని సూచిస్తుంది. ఇది సాధారణ రక్షణ విధానం; బాగా విశ్రాంతి తీసుకోండి మరియు మీ వైద్యుడిని సంప్రదించండి." if has_acute_pattern else "")
            )
        },
        "english": {
            "risks_map": {},
            "summary": (
                "Hello. We have comprehensively analyzed your blood report. "
                f"We noticed that some parameters (Elevated: {', '.join(high_indicators) if high_indicators else 'None'}, "
                f"Low: {', '.join(low_indicators) if low_indicators else 'None'}) are outside the standard reference range. "
                "There is no need for immediate alarm. Maintaining a balanced diet, staying well hydrated, and "
                "scheduling a review with your physician to discuss these findings is highly recommended."
                + (" Additionally, we noticed a temporary pattern of elevated systemic inflammation and dipping platelets, which suggests your body is actively fighting off an infection. This is a normal defense mechanism; please rest well, stay hydrated, and follow up with your doctor." if has_acute_pattern else "")
            )
        }
    }
    
    selected_trans = translations.get(lang, translations["english"])
    mapped_risks = [selected_trans.get("risks_map", {}).get(r, r) for r in risks]
    
    return {
        "disease_risks": mapped_risks,
        "patient_summary": selected_trans.get("summary", translations["english"]["summary"])
    }

def run_regex_fallback_parser(text: str) -> Dict[str, float]:
    """
    Advanced regex-based fallback that matches key biomarkers inside raw text
    when the Gemini API is offline or key is not provided.
    Supports both standard same-line matching and high-fidelity consecutive-line scans.
    """
    extracted_biomarkers: Dict[str, float] = {}
    
    # 1. Standard single-line patterns (using lenient non-digit scans and comma supports)
    patterns = {
        "Hemoglobin": r"(?:Hemoglobin|Haemoglobin|Hb|Hgb)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "WBC": r"(?:White Blood Cells|WBC|Leukocytes|TWBC)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Platelets": r"(?:Platelets?|PLT|Thrombocytes)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "RBC": r"(?:Red Blood Cells|RBC|TRBC|Erythrocytes)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Neutrophils": r"(?:Neutrophils|NEUT|NEUT%|Segmented Neutrophils|Polymorphs)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        
        "HbA1c": r"(?:HbA1c|Hemoglobin A1c|A1c)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Fasting": r"(?:Fasting Glucose|FBS|Fasting Blood Sugar)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Post-Prandial": r"(?:Post-Prandial|PPBS|Post-Meal Glucose)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        
        "Total Cholesterol": r"(?:Total Cholesterol|Cholesterol|Total Chol|Chol)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "HDL": r"(?:HDL Cholesterol|HDL)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "LDL": r"(?:LDL Cholesterol|LDL)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Triglycerides": r"(?:Triglycerides|TRIG)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        
        "ALT": r"(?:ALT|SGPT|Alanine Aminotransferase)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "AST": r"(?:AST|SGOT|Aspartate Aminotransferase)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Total Bilirubin": r"(?:Total Bilirubin|TBIL|Total Bili|Bili Total|Bilirubin)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Direct Bilirubin": r"(?:Direct Bilirubin|DBIL|Direct Bili|Bili Direct)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Alkaline Phosphatase": r"(?:Alkaline Phosphatase|ALP|Alk Phos)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Albumin": r"(?:Albumin|ALB)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        
        "Creatinine": r"(?:Creatinine|Serum Creatinine|CRE)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "BUN": r"(?:BUN|Blood Urea Nitrogen)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "EGFR": r"(?:eGFR|EGFR|GFR)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        
        "TSH": r"(?:TSH|Thyroid Stimulating Hormone)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Free T3": r"(?:Free T3|FT3)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "Free T4": r"(?:Free T4|FT4)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)",
        "C-Reactive Protein": r"(?:C-Reactive Protein|CRP|hs-CRP|hsCRP)[^\d\n]*?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)"
    }
    
    for biomarker, regex in patterns.items():
        match = re.search(regex, text, re.IGNORECASE)
        if match:
            try:
                # Support comma numbers, e.g. 150,000 -> 150000.0
                val_str = match.group(1).replace(",", "")
                extracted_biomarkers[biomarker] = float(val_str)
            except ValueError:
                pass
                
    # 2. High-Fidelity Consecutive-Line Parser (essential for vertical OCR columns)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    aliases = {
        "Hemoglobin": ["hemoglobin", "haemoglobin", "hb", "hgb"],
        "WBC": ["wbc", "twbc", "white blood cells", "leukocytes"],
        "Platelets": ["platelets", "platelet", "plt", "thrombocytes"],
        "RBC": ["rbc", "trbc", "red blood cells", "erythrocytes"],
        "Neutrophils": ["neutrophils", "polymorphs", "neut", "segmented neutrophils"],
        "HbA1c": ["hba1c", "glycated hemoglobin"],
        "Fasting": ["fasting", "fasting glucose", "fbs"],
        "Post-Prandial": ["post-prandial", "ppbs"],
        "Total Cholesterol": ["total cholesterol", "cholesterol", "total chol"],
        "HDL": ["hdl", "hdl cholesterol"],
        "LDL": ["ldl", "ldl cholesterol"],
        "Triglycerides": ["triglycerides", "trig"],
        "ALT": ["alt", "sgpt"],
        "AST": ["ast", "sgot"],
        "Total Bilirubin": ["total bilirubin", "bilirubin", "tbil"],
        "Direct Bilirubin": ["direct bilirubin", "dbil"],
        "Alkaline Phosphatase": ["alkaline phosphatase", "alp", "alk phos"],
        "Creatinine": ["creatinine", "cre"],
        "TSH": ["tsh", "thyroid stimulating hormone"],
        "Free T4": ["free t4", "ft4"],
        "C-Reactive Protein": ["c-reactive protein", "crp"]
    }
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        matched_biomarker = None
        for bio, key_list in aliases.items():
            if any(k == line_lower or line_lower.startswith(k + " ") or line_lower.endswith(" " + k) for k in key_list):
                matched_biomarker = bio
                break
                
        if matched_biomarker and matched_biomarker not in extracted_biomarkers:
            # Look at subsequent lines (up to 4 lines ahead) for a valid numerical value
            for offset in range(1, 5):
                if i + offset >= len(lines):
                    break
                next_line = lines[i + offset]
                # Match a clean integer or float starting the line (optionally including commas)
                num_match = re.search(r"^\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\b", next_line)
                if num_match:
                    try:
                        val_str = num_match.group(1).replace(",", "")
                        extracted_biomarkers[matched_biomarker] = float(val_str)
                        break
                    except ValueError:
                        pass
                        
    # 3. Clinical Unit Normalization
    if "WBC" in extracted_biomarkers and extracted_biomarkers["WBC"] > 100.0:
        # e.g. 4500 Cells/Cumm -> 4.5 10^3/uL
        extracted_biomarkers["WBC"] /= 1000.0
        
    if "RBC" in extracted_biomarkers and 10.0 < extracted_biomarkers["RBC"] < 100.0:
        # e.g. 43.0 -> 4.3 10^6/uL
        extracted_biomarkers["RBC"] /= 10.0
        
    if "Platelets" in extracted_biomarkers and extracted_biomarkers["Platelets"] < 10.0:
        # e.g. 1.20 Lakhs/cumm -> 120.0 10^3/uL
        extracted_biomarkers["Platelets"] *= 100.0
        
    return extracted_biomarkers

def analyze_radiology_scan(raw_text: str, language: str = "English", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses unstructured radiology & imaging scan reports (MRI, CT, X-Ray, Ultrasound, Mammogram, PET),
    classifies findings, translates into reassuring plain language, identifies emergency flags,
    and returns a structured payload conforming to ScanReportAnalysis.
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        # Local fallback heuristic parser if no API key is available
        return {
            "scan_metadata": {
                "modality": "Imaging Scan",
                "body_region": "Anatomical Region",
                "indication": None,
                "technique_notes": None
            },
            "triage": {
                "is_emergency": False,
                "emergency_message": None,
                "summary_headline": "Report parsed in demonstration mode. Configure Gemini API key for clinical-grade multi-modality translation."
            },
            "findings_breakdown": [
                {
                    "finding_text": "Sample scan findings parsed",
                    "category": "normal",
                    "plain_english_explanation": "Please provide a Gemini API key in Settings to activate real-time radiological term extraction and classification.",
                    "clinical_significance": "Awaiting live AI key configuration."
                }
            ],
            "radiologist_impression_summary": "Demonstration mode. Add your Gemini API key to generate comprehensive radiologist impression syntheses.",
            "questions_for_doctor": [
                "What do the findings in this imaging scan mean for my care plan?",
                "Are any follow-up scans or clinical tests recommended?",
                "Are there specific activities or movements I should avoid?"
            ]
        }

    prompt = (
        "You are a specialized Clinical Imaging and Radiology Report Analyzer. Your task is to parse unstructured "
        f"medical scan reports (MRI, CT, X-Ray, Ultrasound, Mammogram, PET), translate complex radiological terminology "
        f"into patient-friendly language ({language}), detect incidental vs. actionable findings, and identify potential acute emergencies.\n\n"
        "### CORE CLINICAL RULES:\n"
        "1. NEGATION HANDLING (CRITICAL): Strictly differentiate between confirmed findings and ruled-out conditions. "
        "If a report states 'No acute fracture', 'No pneumothorax', 'Negative for acute hemorrhage', or 'No mass effect', "
        "classify the status as 'normal'. NEVER categorize a negated finding as 'abnormal' or 'urgent'.\n"
        "2. FINDING CATEGORIZATION: Strictly categorize each finding into:\n"
        "   - 'normal': Expected baseline anatomy or explicitly ruled-out conditions.\n"
        "   - 'incidental': Harmless, common anomalies (e.g., simple cysts, mild disc desiccation, minor osteophytes) not representing the primary disease process.\n"
        "   - 'abnormal': Meaningful findings requiring planned clinical follow-up or treatment.\n"
        "   - 'urgent': Acute, life-threatening conditions (e.g., acute hemorrhage, tension pneumothorax, appendicitis, active extravasation, cord compression).\n"
        "3. PATIENT COMMUNICATION: Translate medical jargon into plain English using reassuring, non-alarmist language. "
        "Explain what it is and what it typically implies.\n"
        "4. DOCTOR QUESTIONS: Generate 3-4 targeted, high-yield questions for the patient to ask their ordering physician.\n"
        "5. SAFETY & GUARDRAILS: NEVER state a definitive diagnosis (avoid 'You have cancer'). Use non-definitive phrasing "
        "('The scan notes findings consistent with...', 'Described as...'). Set 'is_emergency' to true ONLY when immediate same-day "
        "emergency medical evaluation is warranted.\n\n"
        f"Raw Radiology Report Text:\n{raw_text}\n"
    )

    try:
        json_prompt = (
            prompt + "\n\nFormat your response as valid JSON matching this structure:\n"
            "{\n"
            '  "scan_metadata": {"modality": "string", "body_region": "string", "indication": "string or null", "technique_notes": "string or null"},\n'
            '  "triage": {"is_emergency": false, "emergency_message": "string or null", "summary_headline": "string"},\n'
            '  "findings_breakdown": [{"finding_text": "string", "category": "normal|incidental|abnormal|urgent", "plain_english_explanation": "string", "clinical_significance": "string"}],\n'
            '  "radiologist_impression_summary": "string",\n'
            '  "questions_for_doctor": ["string"]\n'
            "}"
        )
        response = generate_gemini_content(
            api_key,
            json_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        parsed_json = json.loads(response.text)
        return parsed_json
    except Exception as e:
        print(f"Error in analyze_radiology_scan: {e}")
        raise RuntimeError(f"Failed to analyze radiology scan: {str(e)}")

def analyze_radiology_scan_image(image_bytes: bytes, mime_type: str = "image/jpeg", language: str = "English", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses an uploaded physical medical scan image (Chest X-Ray, CT slice, MRI scan, Ultrasound, Mammogram),
    identifies visible radiological structures and anomalies using Gemini Multimodal Vision,
    classifies findings (normal, incidental, abnormal, urgent), and returns a structured ScanReportAnalysis.
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        return {
            "scan_metadata": {
                "modality": "Plain Radiograph / Scan Image",
                "body_region": "Chest / Body Region",
                "indication": "Direct scan image review",
                "technique_notes": "Multimodal visual inspection"
            },
            "triage": {
                "is_emergency": False,
                "emergency_message": None,
                "summary_headline": "Scan image loaded in demo mode. Configure your Gemini API key in Settings to activate real-time multimodal visual radiological inspection."
            },
            "findings_breakdown": [
                {
                    "finding_text": "Medical scan image uploaded",
                    "category": "normal",
                    "plain_english_explanation": "Please provide a Gemini API key in Settings to run clinical-grade visual feature recognition across bones, soft tissues, and organ margins.",
                    "clinical_significance": "Awaiting active multimodal API key."
                }
            ],
            "radiologist_impression_summary": "Demonstration mode. Add Gemini API key for automated multimodal image findings translation.",
            "questions_for_doctor": [
                "What clinical findings are observed on this scan image?",
                "Are any supplementary views or follow-up imaging studies needed?"
            ]
        }

    prompt = (
        "You are an expert Clinical Imaging and Radiology Vision AI. Your task is to perform an in-depth radiological "
        f"visual analysis of the attached medical scan image (e.g., X-Ray, CT, MRI, Ultrasound, Mammogram) and translate your observations into patient-friendly language ({language}).\n\n"
        "### CLINICAL VISUAL ANALYSIS INSTRUCTIONS:\n"
        "1. Identify the Modality (e.g., Plain Radiograph Chest X-Ray PA/AP, Lumbar Spine MRI, Head CT) and Anatomical Region.\n"
        "2. Systematically inspect all visible structures:\n"
        "   - Bony structures / skeletal framework (ribs, clavicles, spine, joints) for fractures, lytic lesions, or alignment.\n"
        "   - Soft tissues and organ silhouettes (lungs, heart size, mediastinum, diaphragm, gastric bubble, pleural spaces).\n"
        "   - Look for opacities, consolidations, blunting of costophrenic angles, effusions, masses, pneumothorax, or foreign objects.\n"
        "3. FINDING CATEGORIZATION (Strictly 4 tags):\n"
        "   - 'normal': Expected healthy anatomy (e.g., 'Cardiac silhouette within normal limits', 'Trachea midline', 'No pneumothorax').\n"
        "   - 'incidental': Benign, common variants (e.g., prominent normal gastric bubble, minor degenerative spurs, calcified granuloma).\n"
        "   - 'abnormal': Meaningful pathology requiring non-urgent clinical follow-up (e.g., basal haziness/infiltrate, cardiomegaly, mild pleural thickening).\n"
        "   - 'urgent': Acute life threats (e.g., large tension pneumothorax, massive pleural effusion with shift, acute displaced fracture, free intra-abdominal air under diaphragm).\n"
        "4. PATIENT COMMUNICATION: Translate medical terms into reassuring, plain English. Explain what the visual pattern represents.\n"
        "5. QUESTIONS FOR DOCTOR: Formulate 3-4 targeted, high-yield questions for the ordering physician.\n"
        "6. SAFETY GUARDRAILS: Do NOT issue a definitive diagnosis (avoid 'You have pneumonia'). Use descriptive phrasing ('Findings consistent with...', 'Visual pattern suggests...'). Set 'is_emergency' to true ONLY for acute emergency flags.\n"
    )

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }

    try:
        json_prompt = (
            prompt + "\n\nFormat your response as valid JSON matching this structure:\n"
            "{\n"
            '  "scan_metadata": {"modality": "string", "body_region": "string", "indication": "string or null", "technique_notes": "string or null"},\n'
            '  "triage": {"is_emergency": false, "emergency_message": "string or null", "summary_headline": "string"},\n'
            '  "findings_breakdown": [{"finding_text": "string", "category": "normal|incidental|abnormal|urgent", "plain_english_explanation": "string", "clinical_significance": "string"}],\n'
            '  "radiologist_impression_summary": "string",\n'
            '  "questions_for_doctor": ["string"]\n'
            "}"
        )
        response = generate_gemini_content(
            api_key,
            [json_prompt, image_part],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error in analyze_radiology_scan_image: {e}")
        raise RuntimeError(f"Failed to analyze scan image: {str(e)}")


