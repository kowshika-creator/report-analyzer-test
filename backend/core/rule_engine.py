from typing import List, Dict, Any

def run_explainable_rule_engine(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    AXON Explainable Clinical Rule Engine:
    Evaluates explicit, deterministic clinical decision trees across extracted biomarkers.
    Provides transparent step-by-step diagnostic reasoning, rule identifiers, triggered thresholds,
    and doctor discussion points.
    """
    explainable_results = []
    rule_counter = 1

    for m in metrics:
        name = m["biomarker_name"]
        val = m["value"]
        unit = m["unit"]
        min_n = m["min_normal"]
        max_n = m["max_normal"]
        status = m["status"]
        name_lower = name.lower()

        # Rule ID Prefix generation
        if any(k in name_lower for k in ["hemoglobin", "wbc", "rbc", "platelet", "mcv", "mch"]):
            prefix = "R-CBC"
        elif any(k in name_lower for k in ["fasting", "hba1c", "glucose"]):
            prefix = "R-GLU"
        elif any(k in name_lower for k in ["cholesterol", "ldl", "hdl", "triglycerides"]):
            prefix = "R-LIP"
        elif any(k in name_lower for k in ["alt", "ast", "alp", "bilirubin"]):
            prefix = "R-LFT"
        elif any(k in name_lower for k in ["creatinine", "urea", "bun", "egfr", "potassium"]):
            prefix = "R-KFT"
        elif any(k in name_lower for k in ["tsh", "t3", "t4"]):
            prefix = "R-THY"
        else:
            prefix = "R-GEN"

        rule_id = f"{prefix}-{rule_counter:03d}"
        rule_counter += 1

        ref_str = f"{min_n} - {max_n} {unit}" if max_n < 99990.0 else f"{min_n}+ {unit}"

        # Build explainable rationale based on status
        if status == "Low":
            explanation = (
                f"Rule '{rule_id}' triggered: Measured {name} ({val} {unit}) is below the configured clinical minimum threshold ({min_n} {unit}). "
                f"Physiologically, sub-optimal levels of {name} may indicate reduced biosynthesis, increased consumption, or deficiency."
            )
            discussion_points = [
                f"Ask doctor: What potential underlying factors might cause my {name} to fall below {min_n} {unit}?",
                f"Ask doctor: Should we re-test {name} or check related co-factors in 4 to 6 weeks?"
            ]
        elif status == "High":
            explanation = (
                f"Rule '{rule_id}' triggered: Measured {name} ({val} {unit}) exceeds the configured upper limit ({max_n} {unit}). "
                f"Elevated levels of {name} trigger clinical review for metabolic stress, inflammatory activity, or organ clearance changes."
            )
            discussion_points = [
                f"Ask doctor: Does my elevated {name} ({val} {unit}) require dietary modification, lifestyle intervention, or medication?",
                f"Ask doctor: Are there additional diagnostic panels recommended to further evaluate this finding?"
            ]
        else: # Normal
            explanation = (
                f"Rule '{rule_id}' satisfied: Measured {name} ({val} {unit}) lies comfortably within the expected normative reference interval ({ref_str}). "
                f"This indicates stable biological function for this parameter."
            )
            discussion_points = [
                f"Ask doctor: How frequently should I maintain routine screening for {name} based on my overall health profile?"
            ]

        explainable_results.append({
            "rule_id": rule_id,
            "title": f"Clinical Evaluation Rule for {name}",
            "input_param": name,
            "input_value": val,
            "unit": unit,
            "reference_range": ref_str,
            "result_status": status.upper(),
            "explanation": explanation,
            "doctor_discussion_points": discussion_points
        })

    return explainable_results
