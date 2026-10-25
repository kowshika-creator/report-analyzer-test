import re
from typing import Dict, Any, List, Optional, Tuple

# Comprehensive dictionary mapping standard biomarker names to regex patterns and default metadata
BIOMARKER_MAP = {
    # CBC Panel
    "Hemoglobin": {
        "patterns": [r"\bhaemoglobin\b", r"\bhemoglobin\b", r"\bhb\b", r"\bhgb\b"],
        "unit": "g/dL",
        "panel": "Complete Blood Count (CBC)"
    },
    "WBC": {
        "patterns": [r"\bwbc\b", r"\bleukocytes?\b", r"\btotal\s+wbc\b", r"\bwhite\s+blood\s+cell\b"],
        "unit": "10^3/uL",
        "panel": "Complete Blood Count (CBC)"
    },
    "RBC": {
        "patterns": [r"\brbc\b", r"\berythrocytes?\b", r"\btotal\s+rbc\b", r"\bred\s+blood\s+cell\b"],
        "unit": "10^6/uL",
        "panel": "Complete Blood Count (CBC)"
    },
    "Platelets": {
        "patterns": [r"\bplatelets?\b", r"\bplt\b", r"\bthrombocytes?\b", r"\bplatelet\s+count\b"],
        "unit": "10^3/uL",
        "panel": "Complete Blood Count (CBC)"
    },
    "Hematocrit": {
        "patterns": [r"\bhematocrit\b", r"\bhaematocrit\b", r"\bhct\b", r"\bpcv\b"],
        "unit": "%",
        "panel": "Complete Blood Count (CBC)"
    },
    "MCV": {
        "patterns": [r"\bmcv\b", r"\bmean\s+corpuscular\s+volume\b"],
        "unit": "fL",
        "panel": "Complete Blood Count (CBC)"
    },
    "MCH": {
        "patterns": [r"\bmch\b", r"\bmean\s+corpuscular\s+hemoglobin\b"],
        "unit": "pg",
        "panel": "Complete Blood Count (CBC)"
    },
    "MCHC": {
        "patterns": [r"\bmchc\b"],
        "unit": "g/dL",
        "panel": "Complete Blood Count (CBC)"
    },
    "Neutrophils": {
        "patterns": [r"\bneutrophils?\b", r"\banc\b"],
        "unit": "%",
        "panel": "Complete Blood Count (CBC)"
    },

    # Blood Sugar Panel
    "Fasting": {
        "patterns": [r"\bfasting\s+glucose\b", r"\bfasting\s+blood\s+sugar\b", r"\bfbs\b", r"\bfasting\b"],
        "unit": "mg/dL",
        "panel": "Glycemia / Diabetes Panel"
    },
    "HbA1c": {
        "patterns": [r"\bhba1c\b", r"\bglycated\s+hemoglobin\b", r"\bhemoglobin\s+a1c\b", r"\ba1c\b"],
        "unit": "%",
        "panel": "Glycemia / Diabetes Panel"
    },
    "Postprandial Glucose": {
        "patterns": [r"\bpostprandial\s+glucose\b", r"\bppbs\b", r"\bpp\s+glucose\b"],
        "unit": "mg/dL",
        "panel": "Glycemia / Diabetes Panel"
    },

    # Lipid Profile
    "Total Cholesterol": {
        "patterns": [r"\btotal\s+cholesterol\b", r"\bserum\s+cholesterol\b", r"\bcholesterol\b"],
        "unit": "mg/dL",
        "panel": "Lipid Profile"
    },
    "HDL": {
        "patterns": [r"\bhdl\b", r"\bhdl\s+cholesterol\b", r"\bhigh\s+density\s+lipoprotein\b"],
        "unit": "mg/dL",
        "panel": "Lipid Profile"
    },
    "LDL": {
        "patterns": [r"\bldl\b", r"\bldl\s+cholesterol\b", r"\blow\s+density\s+lipoprotein\b"],
        "unit": "mg/dL",
        "panel": "Lipid Profile"
    },
    "Triglycerides": {
        "patterns": [r"\btriglycerides?\b", r"\btrig\b", r"\btg\b"],
        "unit": "mg/dL",
        "panel": "Lipid Profile"
    },
    "VLDL": {
        "patterns": [r"\bvldl\b", r"\bvldl\s+cholesterol\b"],
        "unit": "mg/dL",
        "panel": "Lipid Profile"
    },

    # Liver Function Test (LFT)
    "ALT": {
        "patterns": [r"\balt\b", r"\bsgpt\b", r"\balanine\s+aminotransferase\b"],
        "unit": "U/L",
        "panel": "Liver Function Panel (LFT)"
    },
    "AST": {
        "patterns": [r"\bast\b", r"\bsgot\b", r"\baspartate\s+aminotransferase\b"],
        "unit": "U/L",
        "panel": "Liver Function Panel (LFT)"
    },
    "ALP": {
        "patterns": [r"\balp\b", r"\balkaline\s+phosphatase\b"],
        "unit": "U/L",
        "panel": "Liver Function Panel (LFT)"
    },
    "Bilirubin": {
        "patterns": [r"\btotal\s+bilirubin\b", r"\bbilirubin\b", r"\bserum\s+bilirubin\b"],
        "unit": "mg/dL",
        "panel": "Liver Function Panel (LFT)"
    },
    "Albumin": {
        "patterns": [r"\balbumin\b", r"\bserum\s+albumin\b"],
        "unit": "g/dL",
        "panel": "Liver Function Panel (LFT)"
    },

    # Kidney Function Test (KFT)
    "Creatinine": {
        "patterns": [r"\bcreatinine\b", r"\bserum\s+creatinine\b", r"\bcre\b"],
        "unit": "mg/dL",
        "panel": "Kidney Function Panel (KFT)"
    },
    "Urea": {
        "patterns": [r"\bserum\s+urea\b", r"\bblood\s+urea\b", r"\burea\b"],
        "unit": "mg/dL",
        "panel": "Kidney Function Panel (KFT)"
    },
    "BUN": {
        "patterns": [r"\bbun\b", r"\bblood\s+urea\s+nitrogen\b"],
        "unit": "mg/dL",
        "panel": "Kidney Function Panel (KFT)"
    },
    "EGFR": {
        "patterns": [r"\begfr\b", r"\bgfr\b", r"\bestimated\s+gfr\b"],
        "unit": "mL/min/1.73m2",
        "panel": "Kidney Function Panel (KFT)"
    },
    "Potassium": {
        "patterns": [r"\bpotassium\b", r"\bk\+\b", r"\bserum\s+potassium\b"],
        "unit": "mEq/L",
        "panel": "Electrolytes & Renal"
    },
    "Sodium": {
        "patterns": [r"\bsodium\b", r"\bna\+\b", r"\bserum\s+sodium\b"],
        "unit": "mEq/L",
        "panel": "Electrolytes & Renal"
    },

    # Thyroid Profile
    "TSH": {
        "patterns": [r"\btsh\b", r"\bthyroid\s+stimulating\s+hormone\b", r"\bultrasensitive\s+tsh\b"],
        "unit": "uIU/mL",
        "panel": "Thyroid Profile"
    },
    "Free T4": {
        "patterns": [r"\bfree\s+t4\b", r"\bft4\b", r"\bfree\s+thyroxine\b"],
        "unit": "ng/dL",
        "panel": "Thyroid Profile"
    },
    "Free T3": {
        "patterns": [r"\bfree\s+t3\b", r"\bft3\b"],
        "unit": "pg/mL",
        "panel": "Thyroid Profile"
    },

    # Inflammatory & Micronutrient
    "C-Reactive Protein": {
        "patterns": [r"\bc-reactive\s+protein\b", r"\bcrp\b", r"\bhs-crp\b"],
        "unit": "mg/L",
        "panel": "Inflammatory Biomarkers"
    },
    "Vitamin D": {
        "patterns": [r"\bvitamin\s+d\b", r"\b25-hydroxy\s+vitamin\s+d\b", r"\bvit\s+d\b"],
        "unit": "ng/mL",
        "panel": "Micronutrients & Vitamins"
    },
    "Vitamin B12": {
        "patterns": [r"\bvitamin\s+b12\b", r"\bvit\s+b12\b", r"\bcobalamin\b"],
        "unit": "pg/mL",
        "panel": "Micronutrients & Vitamins"
    }
}

UNIT_REGEX = r'(?:g/dL|g/L|mg/dL|mg/L|mmol/L|umol/L|µmol/L|mEq/L|10\^3/uL|10\^6/uL|x10\^3/uL|x10\^6/uL|10\*3/uL|10\*6/uL|fL|pg/mL|pg|U/L|uIU/mL|µIU/mL|ng/dL|ng/mL|pg/mL|mL/min/1\.73m2|mL/min|%|cells/uL|lakhs/cumm|lakh/cumm|lakhs|lakh|cumm|/uL)'

def normalize_unambiguous_decimal_commas(text: str) -> str:
    """
    Normalizes unambiguous decimal commas (e.g. '13,5' -> '13.5', '0,85' -> '0.85')
    while strictly preserving thousands separators (e.g. '150,000' -> '150000').
    A decimal comma is defined as a comma preceded by digits and followed by 1 or 2 digits
    that are NOT followed by another digit.
    """
    # 1. Collapse thousands separators in numbers: e.g. 150,000 -> 150000
    text = re.sub(r'\b(\d{1,3}),(\d{3})\b', r'\1\2', text)
    # 2. Convert unambiguous decimal commas: e.g. 13,5 -> 13.5, 0,85 -> 0.85
    text = re.sub(r'\b(\d+),(\d{1,2})\b(?!\d)', r'\1.\2', text)
    return text

def parse_reference_interval_string(line: str) -> Optional[str]:
    """
    Scans a report line for printed biological reference range intervals.
    e.g., "(12.0 - 16.0 g/dL)", "(3.9 - 5.6 mmol/L)", "13.5-17.5", "< 6.0 %", "0.4 to 4.5", "Up to 200"
    """
    line_norm = normalize_unambiguous_decimal_commas(line)
    ref_patterns = [
        r'\(\s*([0-9]+\.?[0-9]*\s*(?:-|to)\s*[0-9]+\.?[0-9]*(?:\s*[a-zA-Z%^0-9/\-]+)?)\s*\)',
        r'([0-9]+\.?[0-9]*\s*(?:-|to)\s*[0-9]+\.?[0-9]*(?:\s*' + UNIT_REGEX + r')?)',
        r'((?:<|>|<=|>=|less than|greater than|up to)\s*[0-9]+\.?[0-9]*(?:\s*' + UNIT_REGEX + r')?)'
    ]
    for p in ref_patterns:
        match = re.search(p, line_norm, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def parse_medical_report_text(raw_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Deterministic Local Medical Parser:
    Scans raw text using pattern matching to extract biomarkers, numeric values,
    units, printed reference intervals, and confidence scores.
    Preserves exact printed units alongside the source values and avoids leading line numbers.
    Never replaces a missing printed source unit with a predefined default.
    """
    extracted: Dict[str, Dict[str, Any]] = {}
    lines = raw_text.splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # 1. Match known standard biomarkers
        for std_name, meta in BIOMARKER_MAP.items():
            if std_name in extracted:
                continue
            
            for pat in meta["patterns"]:
                match_name = re.search(pat, line_clean, re.IGNORECASE)
                if match_name:
                    # Look strictly AFTER the matched biomarker name to avoid line numbers like '1. Hemoglobin'
                    after_text = line_clean[match_name.end():]
                    ref_interval = parse_reference_interval_string(line_clean)
                    
                    # Mask reference interval in after_text so bounds aren't parsed as value
                    clean_after = after_text
                    if ref_interval and ref_interval in clean_after:
                        clean_after = clean_after.replace(ref_interval, "")
                    clean_after = normalize_unambiguous_decimal_commas(clean_after)

                    num_match = re.search(r'[:=\s]\s*([<>]?\s*[0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%^0-9/\-\s]*)', clean_after)
                    val: Optional[float] = None
                    printed_unit: Optional[str] = None

                    if num_match:
                        val_str = num_match.group(1).replace("<", "").replace(">", "").strip()
                        try:
                            val = float(val_str)
                        except ValueError:
                            val = None
                        trailing = num_match.group(2)
                        u_match = re.search(UNIT_REGEX, trailing, re.IGNORECASE)
                        if u_match:
                            printed_unit = u_match.group(0).strip()
                    else:
                        # Search only in after_text for standalone numbers
                        nums = re.findall(r'\b[0-9]+\.?[0-9]*\b', clean_after)
                        if nums:
                            try:
                                val = float(nums[0])
                            except ValueError:
                                val = None

                    extracted[std_name] = {
                        "value": val,
                        "source_value": val,
                        "unit": printed_unit,
                        "source_unit": printed_unit,
                        "assumed_unit": None,
                        "reference_interval": ref_interval,
                        "confidence": 0.95 if val is not None else 0.50,
                        "panel_category": meta["panel"]
                    }
                    break

    # 2. Allow unknown custom tests (e.g. "Test Name: 45.2 mg/dL") to be captured
    custom_line_pattern = r'^([A-Z][a-zA-Z0-9\s\-]+)[:=]\s*([0-9]+(?:[\.,][0-9]+)?)\s*([a-zA-Z%^0-9/]*)(?:\s*\((.*?)\))?'
    for line in lines:
        line_clean = line.strip()
        c_match = re.match(custom_line_pattern, line_clean)
        if c_match:
            c_name = c_match.group(1).strip()
            c_val_str = normalize_unambiguous_decimal_commas(c_match.group(2))
            try:
                c_val = float(c_val_str)
            except ValueError:
                c_val = None
            c_unit = c_match.group(3).strip() or "units"
            c_ref = c_match.group(4).strip() if c_match.group(4) else parse_reference_interval_string(line_clean)

            # Avoid duplicating standard names or aliases
            matches_known = False
            for std_k, std_m in BIOMARKER_MAP.items():
                if std_k in extracted or std_k.lower() == c_name.lower() or any(re.search(pat, c_name, re.IGNORECASE) for pat in std_m["patterns"]):
                    matches_known = True
                    break

            if not matches_known and len(c_name) < 40 and not any(k in c_name.lower() for k in ["patient", "date", "doctor", "report"]):
                extracted[c_name] = {
                    "value": c_val,
                    "source_value": c_val,
                    "unit": c_unit,
                    "source_unit": c_unit if c_unit != "units" else None,
                    "assumed_unit": None,
                    "reference_interval": c_ref,
                    "confidence": 0.90 if c_val is not None else 0.50,
                    "panel_category": "Custom Laboratory Test"
                }

    return extracted
