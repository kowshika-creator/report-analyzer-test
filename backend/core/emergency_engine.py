from typing import List, Dict, Any, Tuple

# Default local emergency panic thresholds
DEFAULT_CRITICAL_THRESHOLDS = {
    "platelets": {"min": 20.0, "reason": "CRITICAL BLEEDING RISK: Platelet count is below emergency threshold (< 20.0 10^3/uL)."},
    "hemoglobin": {"min": 6.5, "reason": "CRITICAL ANEMIA EMERGENCY: Hemoglobin is below life-safety threshold (< 6.5 g/dL)."},
    "fasting": {
        "max": 300.0, "max_reason": "CRITICAL HYPERGLYCEMIA ALERT: Fasting Glucose exceeds emergency limit (> 300 mg/dL).",
        "min": 40.0, "min_reason": "CRITICAL HYPOGLYCEMIA ALERT: Fasting Glucose is below emergency limit (< 40 mg/dL)."
    },
    "potassium": {
        "min": 2.5, "min_reason": "CRITICAL HYPOKALEMIA ALERT: Serum Potassium is below cardiac safety threshold (< 2.5 mEq/L).",
        "max": 6.5, "max_reason": "CRITICAL HYPERKALEMIA ALERT: Serum Potassium exceeds cardiac safety threshold (> 6.5 mEq/L)."
    },
    "creatinine": {"max": 5.0, "reason": "CRITICAL RENAL CRISIS ALERT: Serum Creatinine exceeds acute renal safety limit (> 5.0 mg/dL)."},
    "alt": {"max": 1000.0, "reason": "CRITICAL HEPATIC INJURY ALERT: ALT enzyme exceeds acute injury limit (> 1000 U/L)."},
    "ast": {"max": 1000.0, "reason": "CRITICAL HEPATIC INJURY ALERT: AST enzyme exceeds acute injury limit (> 1000 U/L)."},
    "tsh": {"max": 50.0, "reason": "CRITICAL THYROID CRISIS: TSH indicates severe endocrine crisis (> 50 uIU/mL)."}
}

SAFETY_DISCLAIMER_SUFFIX = " This is not a diagnosis. Seek prompt medical attention according to your healthcare provider's advice."

def check_emergency_thresholds(metrics: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Scans evaluated metric dictionaries for critical panic thresholds.
    Annotates metrics with `is_critical` and `critical_reason`.
    Returns updated metrics and list of active critical alert messages.
    """
    critical_alerts = []

    for m in metrics:
        name_lower = m["biomarker_name"].lower()
        val = m["value"]
        is_crit = False
        crit_msg = None

        # Check platelets
        if any(k in name_lower for k in ["platelet", "plt"]):
            rule = DEFAULT_CRITICAL_THRESHOLDS["platelets"]
            if val < rule["min"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check hemoglobin
        elif any(k in name_lower for k in ["hemoglobin", "hb", "hgb"]):
            rule = DEFAULT_CRITICAL_THRESHOLDS["hemoglobin"]
            if val < rule["min"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check fasting glucose
        elif any(k in name_lower for k in ["fasting", "fbs", "glucose"]):
            rule = DEFAULT_CRITICAL_THRESHOLDS["fasting"]
            if val > rule["max"]:
                is_crit = True
                crit_msg = rule["max_reason"] + SAFETY_DISCLAIMER_SUFFIX
            elif val < rule["min"]:
                is_crit = True
                crit_msg = rule["min_reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check potassium
        elif any(k in name_lower for k in ["potassium", "k+"]):
            rule = DEFAULT_CRITICAL_THRESHOLDS["potassium"]
            if val < rule["min"]:
                is_crit = True
                crit_msg = rule["min_reason"] + SAFETY_DISCLAIMER_SUFFIX
            elif val > rule["max"]:
                is_crit = True
                crit_msg = rule["max_reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check creatinine
        elif "creatinine" in name_lower or "cre" in name_lower:
            rule = DEFAULT_CRITICAL_THRESHOLDS["creatinine"]
            if val > rule["max"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check ALT / AST
        elif "alt" in name_lower or "sgpt" in name_lower:
            rule = DEFAULT_CRITICAL_THRESHOLDS["alt"]
            if val > rule["max"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX
        elif "ast" in name_lower or "sgot" in name_lower:
            rule = DEFAULT_CRITICAL_THRESHOLDS["ast"]
            if val > rule["max"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX

        # Check TSH
        elif "tsh" in name_lower:
            rule = DEFAULT_CRITICAL_THRESHOLDS["tsh"]
            if val > rule["max"]:
                is_crit = True
                crit_msg = rule["reason"] + SAFETY_DISCLAIMER_SUFFIX

        m["is_critical"] = is_crit
        m["critical_reason"] = crit_msg
        if is_crit and crit_msg:
            critical_alerts.append(crit_msg)

    return metrics, critical_alerts
