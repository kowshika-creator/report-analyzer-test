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

def parse_printed_interval_with_unit(interval_str: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Parses printed reference interval string (e.g., '12.0 - 17.5 g/dL', '3.9 - 5.6 mmol/L', '< 6.0 %')
    Returns: Tuple[min_bound, max_bound, interval_unit]
    """
    if not interval_str:
        return None, None, None
    s = interval_str.strip()
    
    # Check for unit in interval string using UNIT_REGEX
    from core.medical_parser import UNIT_REGEX
    unit_match = re.search(UNIT_REGEX, s, re.IGNORECASE)
    int_unit = unit_match.group(0).strip() if unit_match else None

    # Parse numeric bounds
    s_lower = s.lower()
    if "<" in s_lower or "less than" in s_lower or "up to" in s_lower:
        m = re.search(r'(?:<|less than|up to)\s*([0-9]+\.?[0-9]*)', s_lower)
        if m:
            return 0.0, float(m.group(1)), int_unit
    if ">" in s_lower or "greater than" in s_lower:
        m = re.search(r'(?:>|greater than)\s*([0-9]+\.?[0-9]*)', s_lower)
        if m:
            return float(m.group(1)), float('inf'), int_unit
    m = re.search(r'([0-9]+\.?[0-9]*)\s*(?:-|to)\s*([0-9]+\.?[0-9]*)', s_lower)
    if m:
        return float(m.group(1)), float(m.group(2)), int_unit
    return None, None, int_unit

def parse_printed_interval(interval_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses printed reference interval string (e.g., '12.0 - 17.5', '< 6.0', '> 40')
    """
    mn, mx, _ = parse_printed_interval_with_unit(interval_str)
    return mn, mx

def convert_analyte_value(
    biomarker_name: str, 
    val: Optional[float], 
    from_unit: Optional[str], 
    to_unit: Optional[str]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Verified Analyte-Specific Conversion Engine:
    Converts a numeric value from from_unit to to_unit for a specific analyte.
    Returns: Tuple[converted_value, method_description, requires_review]
    """
    if val is None:
        return None, None, True
    if not from_unit or not to_unit:
        return val, "Missing unit specification for conversion", True

    fu = from_unit.strip().lower().replace(" ", "")
    tu = to_unit.strip().lower().replace(" ", "")
    name_l = biomarker_name.lower()

    if fu == tu:
        return val, None, False

    # 1. Glucose panel: mmol/L <-> mg/dL (IUPAC factor: 18.0182)
    if any(k in name_l for k in ["fasting", "glucose", "fbs", "ppbs", "sugar"]):
        if fu == "mmol/l" and tu == "mg/dl":
            return round(val * 18.0182, 1), "Molar mass conversion: mmol/L * 18.0182 -> mg/dL", False
        elif fu == "mg/dl" and tu == "mmol/l":
            return round(val / 18.0182, 2), "Molar mass conversion: mg/dL / 18.0182 -> mmol/L", False
        else:
            return val, f"Unsupported glucose unit conversion: '{from_unit}' to '{to_unit}'", True

    # 2. Hemoglobin: g/L <-> g/dL (Factor: 10.0)
    if any(k in name_l for k in ["hemoglobin", "haemoglobin", "hb", "hgb"]):
        if fu == "g/l" and tu == "g/dl":
            return round(val / 10.0, 1), "Metric conversion: g/L / 10.0 -> g/dL", False
        elif fu == "g/dl" and tu == "g/l":
            return round(val * 10.0, 1), "Metric conversion: g/dL * 10.0 -> g/L", False
        elif fu == "mmol/l" or tu == "mmol/l":
            return val, "Ambiguous unit: Hemoglobin in mmol/L requires lab convention verification", True
        else:
            return val, f"Unsupported hemoglobin unit conversion: '{from_unit}' to '{to_unit}'", True

    # 3. Platelets: target 10^3/uL
    if any(k in name_l for k in ["platelet", "plt", "thrombocyte"]):
        is_lakhs = fu in ["lakhs/cumm", "lakh/cumm", "lakhs", "lakh"]
        is_cells = fu in ["/ul", "cells/ul", "cumm", "/cumm", "cells/cumm"]
        is_k = fu in ["10^3/ul", "x10^3/ul", "10*3/ul", "x10*3/ul", "k/ul"]
        
        target_is_k = tu in ["10^3/ul", "x10^3/ul", "10*3/ul", "x10*3/ul", "k/ul"]
        
        if is_k and target_is_k:
            return val, None, False
        if is_lakhs and target_is_k:
            return round(val * 100.0, 1), "Subcontinent lab conversion: lakhs/cumm * 100.0 -> 10^3/uL", False
        if is_cells and target_is_k:
            # Conservative handling: do not accept values below 1000 as though they were already 10^3/uL
            if val >= 1000.0:
                return round(val / 1000.0, 1), "Metric conversion: cells/uL / 1000.0 -> 10^3/uL", False
            else:
                return val, f"Platelet value {val} {from_unit} is below 1,000 cells/uL: ambiguous or extreme value requires manual clinical review and cannot be assumed as 10^3/uL.", True
        return val, f"Unsupported platelet unit conversion: '{from_unit}' to '{to_unit}'", True

    # 4. Strict compatibility check for all other analytes
    if fu == tu:
        return val, None, False
    return val, f"Unverified unit mismatch: source '{from_unit}' vs expected '{to_unit}'", True

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
    - Platelets: lakhs/cumm -> 10^3/uL, cells/uL (>= 1000) -> 10^3/uL.
    
    Unsupported or unknown units are flagged with `requires_review = True` and
    NEVER silently substituted or compared against incompatible reference bounds.

    Returns:
        Tuple[normalized_value, normalized_unit, conversion_method, requires_review]
    """
    if source_val is None:
        return None, source_unit or target_unit, None, True

    s_unit_clean = (source_unit or "").strip()
    if not s_unit_clean:
        return source_val, None, f"Default clinical unit '{target_unit}' assumed (unprinted in source report). Manual clinical verification required.", True

    norm_val, method, requires_review = convert_analyte_value(
        biomarker_name=biomarker_name,
        val=source_val,
        from_unit=s_unit_clean,
        to_unit=target_unit
    )

    if requires_review:
        return source_val, s_unit_clean, method, True
    
    return norm_val, target_unit, method, False

def evaluate_reference_ranges(
    biomarkers: Dict[str, Dict[str, Any]], 
    db_session: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates extracted biomarkers against reference ranges in priority order:
    1. Printed Reference Range on Patient Report
    2. SQLite Reference Database
    3. Built-in Standard Clinical Guidelines

    Every numeric comparison strictly uses compatible units across:
    - The measured value
    - The lower reference bound
    - The upper reference bound

    Preserves original source values and units. If the measurement is converted,
    both reference bounds are converted using verified analyte-specific conversion,
    or the comparison is performed consistently in the source unit.
    Ambiguous or unsupported units are flagged for review and never assigned misleading
    Low, Normal, or High classifications.
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
        source_val = data.get("source_value") if data.get("source_value") is not None else data.get("value")
        ref_printed = data.get("reference_interval")
        source_unit = data.get("source_unit") if "source_unit" in data else data.get("unit")
        confidence = data.get("confidence", 0.95)
        panel_cat = data.get("panel_category", "General Clinical Metric")

        matched_db_range = db_map.get(name.lower())
        fallback = FALLBACK_CLINICAL_RANGES.get(name)
        standard_unit = (matched_db_range.unit if matched_db_range else (fallback["unit"] if fallback else (source_unit or "units")))

        dyn_min, dyn_max, interval_unit = parse_printed_interval_with_unit(ref_printed) if ref_printed else (None, None, None)
        
        assumed_unit = None
        norm_val = None
        norm_unit = None
        conv_method = None
        requires_review = False
        status = "Normal"
        source_tag = "Clinical Guidelines"
        desc = ""

        # Case 1: Missing or unparseable source value
        if source_val is None:
            status = "Unparseable / Missing"
            requires_review = True
            effective_val = None
            effective_unit = source_unit or standard_unit
            min_bound = 0.0
            max_bound = 99999.0
            source_tag = "Lab Report" if ref_printed else ("AXON Local Database" if matched_db_range else "Clinical Guidelines")
            desc = f"{name}: Value missing or unparseable in source report."

        # Case 2: Printed reference interval present on patient report
        elif dyn_min is not None or dyn_max is not None:
            source_tag = "Lab Report"
            
            # Check for inverted or ambiguous interval (e.g. 15.0 - 10.0)
            if dyn_min is not None and dyn_max is not None and dyn_min > dyn_max:
                requires_review = True
                status = "Unreviewed (Ambiguous Reference Interval)"
                effective_val = source_val
                effective_unit = interval_unit or source_unit or standard_unit
                min_bound = dyn_min
                max_bound = dyn_max
                desc = f"[Printed Ref Range: {ref_printed}] Inverted or ambiguous reference interval requires manual clinical review."

            # Check if source unit is missing
            elif not source_unit:
                assumed_unit = interval_unit or standard_unit
                requires_review = True
                status = "Unreviewed (Missing Source Unit)"
                effective_val = source_val
                effective_unit = assumed_unit
                min_bound = dyn_min if dyn_min is not None else 0.0
                max_bound = dyn_max if dyn_max is not None else 99999.0
                conv_method = f"Default clinical unit '{assumed_unit}' assumed (unprinted in source report). Manual clinical verification required."
                desc = f"[Printed Ref Range: {ref_printed}] Value printed without source unit. Assumed '{assumed_unit}'; manual clinical review required."

            else:
                # Both source value and source unit are printed
                effective_int_unit = interval_unit or source_unit

                # Check if interval unit conflicts with source unit without a valid conversion
                if interval_unit and interval_unit.lower().replace(" ", "") != source_unit.lower().replace(" ", ""):
                    # Attempt analyte-specific conversion from source_unit to interval_unit
                    test_val, test_m, test_rev = convert_analyte_value(name, source_val, source_unit, interval_unit)
                    if test_rev:
                        requires_review = True
                        status = "Unreviewed (Incompatible Unit)"
                        effective_val = source_val
                        effective_unit = source_unit
                        min_bound = dyn_min if dyn_min is not None else 0.0
                        max_bound = dyn_max if dyn_max is not None else 99999.0
                        desc = f"[Printed Ref Range: {ref_printed}] Source unit '{source_unit}' conflicts with printed interval unit '{interval_unit}'. Clinical review required."
                    else:
                        norm_val = test_val
                        norm_unit = interval_unit
                        conv_method = test_m
                        effective_val = norm_val
                        effective_unit = interval_unit
                        min_bound = dyn_min if dyn_min is not None else 0.0
                        max_bound = dyn_max if dyn_max is not None else 99999.0
                        desc = f"[Printed Ref Range: {ref_printed}] Measured value converted from {source_val} {source_unit} to {interval_unit} to match printed interval."
                        if effective_val < min_bound:
                            status = "Low"
                        elif effective_val > max_bound:
                            status = "High"
                        else:
                            status = "Normal"
                else:
                    # Source unit matches interval unit (e.g. Glucose 5.5 mmol/L with 3.9 - 5.6 mmol/L)
                    # Check if standard target unit differs and can be converted consistently
                    if source_unit.lower().replace(" ", "") != standard_unit.lower().replace(" ", ""):
                        c_val, m_val, r_val = convert_analyte_value(name, source_val, source_unit, standard_unit)
                        c_min, _, r_min = convert_analyte_value(name, dyn_min, source_unit, standard_unit) if dyn_min is not None else (0.0, None, False)
                        c_max, _, r_max = convert_analyte_value(name, dyn_max, source_unit, standard_unit) if dyn_max is not None else (float('inf'), None, False)

                        if r_val or r_min or r_max:
                            # Cannot convert to standard unit; check if source_unit itself is valid or ambiguous
                            if r_val:
                                requires_review = True
                                status = "Unreviewed (Incompatible Unit)"
                                effective_val = source_val
                                effective_unit = source_unit
                                min_bound = dyn_min if dyn_min is not None else 0.0
                                max_bound = dyn_max if dyn_max is not None else 99999.0
                                desc = f"{name}: Unit '{source_unit}' is unsupported or ambiguous ({m_val}). Clinical review required."
                            else:
                                # Compare consistently in source unit
                                effective_val = source_val
                                effective_unit = source_unit
                                min_bound = dyn_min if dyn_min is not None else 0.0
                                max_bound = dyn_max if dyn_max is not None else 99999.0
                                desc = f"[Printed Ref Range: {ref_printed}] Evaluated consistently in source unit '{source_unit}'."
                                if effective_val < min_bound:
                                    status = "Low"
                                elif effective_val > max_bound:
                                    status = "High"
                                else:
                                    status = "Normal"
                        else:
                            # BOTH measured value and BOTH bounds converted using verified analyte-specific conversion!
                            norm_val = c_val
                            norm_unit = standard_unit
                            conv_method = f"{m_val} (both measurement and printed reference bounds converted consistently)"
                            effective_val = norm_val
                            effective_unit = standard_unit
                            min_bound = c_min
                            max_bound = c_max if c_max != float('inf') else 99999.0
                            desc = f"[Printed Ref Range: {ref_printed}] Evaluated using printed bounds converted consistently to {standard_unit}."
                            if effective_val < min_bound:
                                status = "Low"
                            elif effective_val > max_bound:
                                status = "High"
                            else:
                                status = "Normal"
                    else:
                        # Already in standard unit
                        effective_val = source_val
                        effective_unit = source_unit
                        min_bound = dyn_min if dyn_min is not None else 0.0
                        max_bound = dyn_max if dyn_max is not None else 99999.0
                        norm_val = source_val
                        norm_unit = source_unit
                        desc = f"[Printed Ref Range: {ref_printed}] Evaluated using printed report bounds."
                        if effective_val < min_bound:
                            status = "Low"
                        elif effective_val > max_bound:
                            status = "High"
                        else:
                            status = "Normal"

        # Case 3: No printed reference interval; evaluate against SQLite DB or Clinical Guidelines
        else:
            if matched_db_range:
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

            # Check for missing source unit
            if not source_unit:
                assumed_unit = target_unit
                requires_review = True
                status = "Unreviewed (Missing Source Unit)"
                effective_val = source_val
                effective_unit = target_unit
                conv_method = f"Default clinical unit '{target_unit}' assumed (unprinted in source report). Manual clinical verification required."
                desc = f"{name}: Value printed without source unit. Cannot evaluate against expected '{target_unit}' reference bounds without clinical verification."

            else:
                # Normalize against target reference database unit
                norm_v, norm_u, method, req_review = normalize_biomarker_unit(
                    biomarker_name=name,
                    source_val=source_val,
                    source_unit=source_unit,
                    target_unit=target_unit
                )

                if req_review:
                    requires_review = True
                    status = "Unreviewed (Incompatible Unit)"
                    effective_val = source_val
                    effective_unit = source_unit
                    conv_method = method
                    desc = f"{name}: Unit '{source_unit}' conflicts with reference database unit '{target_unit}' ({method}) and requires clinical review."
                else:
                    norm_val = norm_v
                    norm_unit = norm_u
                    conv_method = method
                    effective_val = norm_val
                    effective_unit = norm_unit
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
            "assumed_unit": assumed_unit,
            "normalized_value": norm_val,
            "normalized_unit": norm_unit,
            "conversion_method": conv_method,
            "requires_review": requires_review
        })

    return evaluated_metrics
