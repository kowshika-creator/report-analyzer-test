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

def evaluate_reference_ranges(
    biomarkers: Dict[str, Dict[str, Any]], 
    db_session: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates extracted biomarkers against reference ranges in priority order:
    1. Printed Reference Range on Patient Report
    2. SQLite Reference Database
    3. Built-in Standard Clinical Guidelines

    Returns structured dicts matching MetricAnalysis schema with annotated reference_source.
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
        val = data.get("value", 0.0)
        ref_printed = data.get("reference_interval")
        unit_given = data.get("unit")
        confidence = data.get("confidence", 0.95)
        panel_cat = data.get("panel_category", "General Clinical Metric")

        dyn_min, dyn_max = parse_printed_interval(ref_printed) if ref_printed else (None, None)
        matched_db_range = db_map.get(name.lower())
        fallback = FALLBACK_CLINICAL_RANGES.get(name)

        # Determine reference bounds & source tag
        if dyn_min is not None or dyn_max is not None:
            min_bound = dyn_min if dyn_min is not None else 0.0
            max_bound = dyn_max if dyn_max is not None else 99999.0
            source_tag = "Lab Report"
            desc = f"[Printed Ref Range: {ref_printed}] Evaluated using printed report bounds."
            unit = unit_given if unit_given else (matched_db_range.unit if matched_db_range else "units")
        elif matched_db_range:
            min_bound = matched_db_range.min_normal
            max_bound = matched_db_range.max_normal
            source_tag = "AXON Local Database"
            desc = matched_db_range.description or f"Standard clinical bounds for {name}."
            unit = unit_given if unit_given else matched_db_range.unit
        elif fallback:
            min_bound = fallback["min"]
            max_bound = fallback["max"]
            source_tag = "Standard Clinical Guidelines"
            desc = fallback["desc"]
            unit = unit_given if unit_given else fallback["unit"]
        else:
            min_bound = 0.0
            max_bound = 99999.0
            source_tag = "Clinical Guidelines"
            desc = f"Custom or non-standard metric evaluated locally."
            unit = unit_given if unit_given else "units"

        # Determine evaluation status
        if val < min_bound:
            status = "Low"
        elif val > max_bound:
            status = "High"
        else:
            status = "Normal"

        is_low_conf = confidence < 0.80

        evaluated_metrics.append({
            "biomarker_name": name,
            "value": val,
            "unit": unit,
            "min_normal": min_bound if min_bound != float('inf') else 99999.0,
            "max_normal": max_bound if max_bound != float('inf') else 99999.0,
            "status": status,
            "confidence": round(float(confidence), 2),
            "is_low_confidence": is_low_conf,
            "reference_source": source_tag,
            "description": desc,
            "panel_category": panel_cat
        })

    return evaluated_metrics
