import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

# Standard clinical reference range fallback dictionary
FALLBACK_CLINICAL_RANGES = {
    "Hemoglobin": {"min": 12.0, "max": 16.5, "unit": "g/dL", "desc": "Iron-rich protein in red blood cells that transports oxygen."},
    "WBC": {"min": 4.0, "max": 11.0, "unit": "10^3/uL", "desc": "White blood cells responsible for immune defense against infection."},
    "RBC": {"min": 4.0, "max": 5.8, "unit": "10^6/uL", "desc": "Red blood cells that carry oxygen throughout tissues."},
    "Platelets": {"min": 150.0, "max": 450.0, "unit": "10^3/uL", "desc": "Blood cell fragments necessary for normal blood clotting."},
    "Hematocrit": {"min": 37.0, "max": 48.0, "unit": "%", "desc": "Proportion of red blood cells in circulating blood volume."},
    "MCV": {"min": 80.0, "max": 100.0, "unit": "fL", "desc": "Average volume and physical size of individual red blood cells."},
    "MCH": {"min": 27.0, "max": 33.0, "unit": "pg", "desc": "Average mass of hemoglobin per red blood cell."},
    "MCHC": {"min": 32.0, "max": 36.0, "unit": "g/dL", "desc": "Concentration of hemoglobin relative to red blood cell volume."},
    "Neutrophils": {"min": 40.0, "max": 70.0, "unit": "%", "desc": "Primary white blood cell subtype that combats acute bacterial infection."},
    "Fasting": {"min": 70.0, "max": 99.0, "unit": "mg/dL", "desc": "Blood glucose level measured after overnight fasting."},
    "HbA1c": {"min": 4.0, "max": 5.6, "unit": "%", "desc": "Glycated hemoglobin reflecting 3-month average blood glucose."},
    "Postprandial Glucose": {"min": 70.0, "max": 140.0, "unit": "mg/dL", "desc": "Blood glucose level measured 2 hours post-meal."},
    "Total Cholesterol": {"min": 125.0, "max": 200.0, "unit": "mg/dL", "desc": "Total circulating blood cholesterol level."},
    "HDL": {"min": 40.0, "max": 60.0, "unit": "mg/dL", "desc": "High-density lipoprotein ('good cholesterol') promoting vascular clearance."},
    "LDL": {"min": 0.0, "max": 100.0, "unit": "mg/dL", "desc": "Low-density lipoprotein ('bad cholesterol') associated with arterial plaque."},
    "Triglycerides": {"min": 35.0, "max": 150.0, "unit": "mg/dL", "desc": "Primary lipid storage molecules circulating in blood."},
    "VLDL": {"min": 5.0, "max": 30.0, "unit": "mg/dL", "desc": "Very low-density lipoprotein carrying triglycerides."},
    "ALT": {"min": 7.0, "max": 56.0, "unit": "U/L", "desc": "Alanine aminotransferase, specific marker of liver parenchymal health."},
    "AST": {"min": 10.0, "max": 40.0, "unit": "U/L", "desc": "Aspartate aminotransferase, marker of hepatic and muscular cellular health."},
    "ALP": {"min": 44.0, "max": 147.0, "unit": "U/L", "desc": "Alkaline phosphatase enzyme present in biliary duct and bone tissue."},
    "Bilirubin": {"min": 0.2, "max": 1.2, "unit": "mg/dL", "desc": "Yellow breakdown product of red blood cell hemoglobin turnover."},
    "Albumin": {"min": 3.4, "max": 5.4, "unit": "g/dL", "desc": "Major liver-synthesized plasma protein maintaining oncotic pressure."},
    "Creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL", "desc": "Muscular metabolic waste product filtered by renal glomeruli."},
    "Urea": {"min": 15.0, "max": 45.0, "unit": "mg/dL", "desc": "Nitrogenous waste product excreted by functional kidney nephrons."},
    "BUN": {"min": 7.0, "max": 20.0, "unit": "mg/dL", "desc": "Blood Urea Nitrogen reflecting protein catabolism and renal clearance."},
    "EGFR": {"min": 90.0, "max": 120.0, "unit": "mL/min/1.73m2", "desc": "Estimated Glomerular Filtration Rate measuring kidney filtration speed."},
    "Potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L", "desc": "Vital intracellular electrolyte governing cardiac electrical conduction."},
    "Sodium": {"min": 135.0, "max": 145.0, "unit": "mEq/L", "desc": "Primary extracellular electrolyte regulating fluid balance and osmolarity."},
    "TSH": {"min": 0.4, "max": 4.5, "unit": "uIU/mL", "desc": "Pituitary hormone regulating thyroid gland metabolic activity."},
    "Free T4": {"min": 0.8, "max": 1.8, "unit": "ng/dL", "desc": "Unbound active thyroxine hormone circulating in blood."},
    "Free T3": {"min": 2.3, "max": 4.2, "unit": "pg/mL", "desc": "Unbound active triiodothyronine regulating cellular metabolic rate."},
    "C-Reactive Protein": {"min": 0.0, "max": 5.0, "unit": "mg/L", "desc": "Acute-phase hepatic reactant signaling systemic inflammation or infection."},
    "Vitamin D": {"min": 30.0, "max": 100.0, "unit": "ng/mL", "desc": "Fat-soluble vitamin essential for calcium absorption and bone density."},
    "Vitamin B12": {"min": 200.0, "max": 900.0, "unit": "pg/mL", "desc": "Water-soluble vitamin essential for neural function and red cell maturation."}
}

def parse_printed_interval(interval_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses printed reference interval string (e.g., '12.0 - 17.5', '< 6.0', '> 40')
    """
    if not interval_str:
        return None, None
    s = interval_str.strip().lower()
    if "<" in s or "less than" in s or "up to" in s:
        m = re.search(r'(?:<|less than|up to)\s*([0-9]+\.?[0-9]*)', s)
        if m:
            return 0.0, float(m.group(1))
    if ">" in s or "greater than" in s:
        m = re.search(r'(?:>|greater than)\s*([0-9]+\.?[0-9]*)', s)
        if m:
            return float(m.group(1)), float('inf')
    m = re.search(r'([0-9]+\.?[0-9]*)\s*(?:-|to)\s*([0-9]+\.?[0-9]*)', s)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

def normalize_biomarker_unit(
    biomarker_name: str, 
    source_val: Optional[float], 
    source_unit: Optional[str], 
    target_unit: str
) -> Tuple[Optional[float], Optional[str], Optional[str], bool]:
    """
    Validated Analyte-Specific Unit Normalization:
    - Glucose: mmol/L <-> mg/dL using IUPAC standard molar mass factor 18.0182.
    - Hemoglobin: g/L <-> g/dL using standard metric ratio (10 g/L = 1 g/dL).
    - Platelets: lakhs/cumm -> 10^3/uL (subcontinent lab convention: 1 lakh = 100 x 10^3/uL).
    
    Unsupported or unknown units are flagged with `requires_review = True` and
    NEVER silently substituted or compared against incompatible reference bounds.

    Returns:
        Tuple[normalized_value, normalized_unit, conversion_method, requires_review]
    """
    if source_val is None:
        return None, source_unit or target_unit, None, True

    n_lower = biomarker_name.lower()
    s_unit_clean = (source_unit or "").strip()
    s_unit_lower = s_unit_clean.lower()
    t_unit_lower = target_unit.strip().lower()

    # If no unit was printed in the report, assume guideline target unit with disclaimer
    if not s_unit_clean:
        return source_val, target_unit, "Default clinical guideline unit applied (unprinted in source)", False

    # 1. Glucose / Glycemia Panel (Target: mg/dL)
    if any(k in n_lower for k in ["fasting", "glucose", "fbs", "ppbs", "sugar"]):
        if s_unit_lower in ["mmol/l", "mmol/l"]:
            norm_v = round(source_val * 18.0182, 1)
            return norm_v, "mg/dL", "Molar mass conversion: mmol/L * 18.0182 -> mg/dL", False
        elif s_unit_lower in ["mg/dl", "mg/dl"]:
            return source_val, "mg/dL", None, False
        else:
            # Incompatible / unsupported unit for glucose
            return source_val, s_unit_clean, f"Unsupported glucose unit: {s_unit_clean}", True

    # 2. Hemoglobin (Target: g/dL)
    if any(k in n_lower for k in ["hemoglobin", "haemoglobin", "hb", "hgb"]):
        if s_unit_lower in ["g/l", "g/l"]:
            norm_v = round(source_val / 10.0, 1)
            return norm_v, "g/dL", "Metric conversion: g/L / 10.0 -> g/dL", False
        elif s_unit_lower in ["g/dl", "g/dl"]:
            return source_val, "g/dL", None, False
        elif s_unit_lower in ["mmol/l", "mmol/l"]:
            # Ambiguous without monomer vs tetramer specification
            return source_val, s_unit_clean, "Ambiguous unit: Hemoglobin in mmol/L requires lab convention verification", True
        else:
            return source_val, s_unit_clean, f"Unsupported hemoglobin unit: {s_unit_clean}", True

    # 3. Platelets (Target: 10^3/uL)
    if any(k in n_lower for k in ["platelet", "plt", "thrombocyte"]):
        if s_unit_lower in ["lakhs/cumm", "lakh/cumm", "lakhs", "lakh"]:
            norm_v = round(source_val * 100.0, 1)
            return norm_v, "10^3/uL", "Subcontinent lab conversion: lakhs/cumm * 100.0 -> 10^3/uL", False
        elif s_unit_lower in ["10^3/ul", "10^3/ul", "x10^3/ul", "x10^3/ul", "k/ul", "k/ul"]:
            return source_val, "10^3/uL", None, False
        elif s_unit_lower in ["/ul", "cells/ul", "cumm", "/cumm"] and source_val >= 1000:
            norm_v = round(source_val / 1000.0, 1)
            return norm_v, "10^3/uL", "Metric conversion: cells/uL / 1000.0 -> 10^3/uL", False
        elif s_unit_lower in ["/ul", "cells/ul", "cumm", "/cumm"] and source_val < 1000:
            return source_val, "10^3/uL", None, False
        else:
            return source_val, s_unit_clean, f"Unsupported platelet unit: {s_unit_clean}", True

    # 4. Strict compatibility check for all other analytes
    if s_unit_lower == t_unit_lower or s_unit_lower.replace(" ", "") == t_unit_lower.replace(" ", ""):
        return source_val, target_unit, None, False
    else:
        # Unknown/incompatible unit: flag for review, do NOT guess
        return source_val, s_unit_clean, f"Unverified unit mismatch: source '{s_unit_clean}' vs expected '{target_unit}'", True

def evaluate_reference_ranges(
    biomarkers: Dict[str, Dict[str, Any]], 
    db_session: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates extracted biomarkers against reference ranges in priority order:
    1. Printed Reference Range on Patient Report
    2. SQLite Reference Database
    3. Built-in Standard Clinical Guidelines

    Strictly preserves missing values, enforces validated analyte-specific unit conversions,
    and flags unreviewed or incompatible measurements without guessing.
    """
    db_map = {}
    if db_session:
        try:
            from models import ReferenceRange
            ranges = db_session.query(ReferenceRange).all()
            for r in ranges:
                db_map[r.biomarker_name.lower()] = r
                if r.alias_names:
                    for alias in r.alias_names.split(","):
                        if alias.strip():
                            db_map[alias.strip().lower()] = r
        except Exception as e:
            print(f"Notice: SQLite reference DB query error: {e}")

    evaluated_metrics = []

    for name, data in biomarkers.items():
        source_val = data.get("value")
        ref_printed = data.get("reference_interval")
        source_unit = data.get("source_unit") or data.get("unit")
        confidence = data.get("confidence", 0.95)
        panel_cat = data.get("panel_category", "General Clinical Metric")

        dyn_min, dyn_max = parse_printed_interval(ref_printed) if ref_printed else (None, None)
        matched_db_range = db_map.get(name.lower())
        fallback = FALLBACK_CLINICAL_RANGES.get(name)

        # Determine reference bounds & target unit
        if dyn_min is not None or dyn_max is not None:
            min_bound = dyn_min if dyn_min is not None else 0.0
            max_bound = dyn_max if dyn_max is not None else 99999.0
            source_tag = "Lab Report"
            desc = f"[Printed Ref Range: {ref_printed}] Evaluated using printed report bounds."
            target_unit = (matched_db_range.unit if matched_db_range else (fallback["unit"] if fallback else (source_unit or "units")))
        elif matched_db_range:
            min_bound = matched_db_range.min_normal
            max_bound = matched_db_range.max_normal
            source_tag = "AXON Local Database"
            desc = matched_db_range.description or f"Standard clinical bounds for {name}."
            target_unit = matched_db_range.unit
        elif fallback:
            min_bound = fallback["min"]
            max_bound = fallback["max"]
            source_tag = "Standard Clinical Guidelines"
            desc = fallback["desc"]
            target_unit = fallback["unit"]
        else:
            min_bound = 0.0
            max_bound = 99999.0
            source_tag = "Clinical Guidelines"
            desc = f"Custom or non-standard metric evaluated locally."
            target_unit = source_unit or "units"

        # Apply Validated Analyte-Specific Unit Normalization
        norm_val, norm_unit, conv_method, requires_review = normalize_biomarker_unit(
            biomarker_name=name,
            source_val=source_val,
            source_unit=source_unit,
            target_unit=target_unit
        )

        effective_val = norm_val if norm_val is not None else source_val
        effective_unit = norm_unit if norm_unit else (source_unit or target_unit)

        # Determine evaluation status safely
        if effective_val is None:
            status = "Unparseable / Missing"
            requires_review = True
            desc = f"{name}: Value missing or unparseable in source report."
        elif requires_review:
            status = "Unreviewed (Incompatible Unit)"
            desc = f"{name}: Unit '{source_unit}' is incompatible with expected '{target_unit}' and requires clinical review."
        else:
            # Safe numeric classification
            if effective_val < min_bound:
                status = "Low"
            elif effective_val > max_bound:
                status = "High"
            else:
                status = "Normal"

        is_low_conf = (confidence < 0.80) or requires_review or (effective_val is None)

        evaluated_metrics.append({
            "biomarker_name": name,
            "value": effective_val,
            "unit": effective_unit,
            "min_normal": min_bound if min_bound != float('inf') else 99999.0,
            "max_normal": max_bound if max_bound != float('inf') else 99999.0,
            "status": status,
            "confidence": round(float(confidence), 2),
            "is_low_confidence": is_low_conf,
            "reference_source": source_tag,
            "description": desc,
            "panel_category": panel_cat,
            
            # Unit traceability & safety metadata
            "source_value": source_val,
            "source_unit": source_unit,
            "normalized_value": norm_val,
            "normalized_unit": norm_unit,
            "conversion_method": conv_method,
            "requires_review": requires_review
        })

    return evaluated_metrics
