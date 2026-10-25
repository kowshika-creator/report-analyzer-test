from typing import List, Dict, Any

def evaluate_disease_risk_patterns(metrics: List[Dict[str, Any]]) -> List[str]:
    """
    AXON Disease Risk Pattern Engine:
    Combines local deterministic clinical decision trees with the trained local Machine Learning model
    (`ml/axon_ml_weights.json`) to compute risk pattern predictions and probability confidence percentages.
    Outputs non-diagnostic pattern indicators with explicit recommendation to consult healthcare providers.
    """
    patterns = []

    # 1. Evaluate using Trained Local Machine Learning Classifier Engine
    try:
        from ml.biomarker_ml_predictor import predict_disease_risks_ml
        ml_patterns, _ = predict_disease_risks_ml(metrics)
        if ml_patterns:
            patterns.extend(ml_patterns)
    except Exception as e:
        print(f"Notice: Trained local ML model prediction fallback: {e}")

    # 2. Rule-based clinical verification fallback if ML predictions are empty
    if not patterns:
        valid_metrics = [
            m for m in metrics 
            if m.get("value") is not None 
            and not m.get("requires_review") 
            and m.get("status") in ["Low", "High", "Normal"]
        ]
        if not valid_metrics:
            return ["No clinically evaluated biomarkers available for pattern recognition."]

        m_map = {m["biomarker_name"].lower(): m for m in valid_metrics}

        fbs = m_map.get("fasting") or m_map.get("fasting glucose") or m_map.get("glucose")
        hba1c = m_map.get("hba1c")
        if fbs or hba1c:
            f_val = fbs["value"] if fbs else 0.0
            a_val = hba1c["value"] if hba1c else 0.0
            if f_val >= 126.0 or a_val >= 6.5:
                patterns.append(
                    "Elevated Glycemic Pattern: Fasting glucose (>= 126 mg/dL) or HbA1c (>= 6.5%) indicates diabetic range values requiring clinical evaluation with your healthcare professional."
                )
            elif (100.0 <= f_val < 126.0) or (5.7 <= a_val < 6.5):
                patterns.append(
                    "Prediabetes Risk Indicator: Measured glucose or HbA1c values fall within the prediabetes range (Fasting 100-125 mg/dL or HbA1c 5.7-6.4%). Discuss glycemic monitoring with your doctor."
                )

        chol = m_map.get("total cholesterol") or m_map.get("cholesterol")
        ldl = m_map.get("ldl")
        hdl = m_map.get("hdl")
        trig = m_map.get("triglycerides")
        if chol or ldl or trig:
            c_val = chol["value"] if chol else 0.0
            l_val = ldl["value"] if ldl else 0.0
            h_val = hdl["value"] if hdl else 99.0
            t_val = trig["value"] if trig else 0.0
            if c_val >= 200.0 or l_val >= 130.0 or t_val >= 150.0 or h_val < 40.0:
                patterns.append(
                    "Dyslipidemia / Lipid Risk Profile: Elevated cholesterol (>= 200 mg/dL), LDL (>= 130 mg/dL), or triglycerides (>= 150 mg/dL) detected. This pattern is associated with cardiovascular health risk. Review dietary and exercise plans with a physician."
                )

        hb = m_map.get("hemoglobin") or m_map.get("hb")
        mcv = m_map.get("mcv")
        if hb:
            h_val = hb["value"]
            m_val = mcv["value"] if mcv else 90.0
            if h_val < 12.0:
                sub_type = "microcytic" if m_val < 80.0 else ("macrocytic" if m_val > 100.0 else "normocytic")
                patterns.append(
                    f"Anemia Risk Pattern ({sub_type}): Hemoglobin ({h_val} g/dL) is below standard reference bounds. Low hemoglobin may cause fatigue or weakness and requires clinical review."
                )

        tsh = m_map.get("tsh")
        if tsh:
            t_val = tsh["value"]
            if t_val > 4.5:
                patterns.append(
                    "Subclinical / Overt Hypothyroidism Indicator: Elevated TSH (> 4.5 uIU/mL) suggests reduced thyroid gland hormone secretion. Discuss thyroid function testing with your doctor."
                )

        alt = m_map.get("alt") or m_map.get("sgpt")
        ast = m_map.get("ast") or m_map.get("sgot")
        if alt or ast:
            alt_v = alt["value"] if alt else 0.0
            ast_v = ast["value"] if ast else 0.0
            if alt_v > 56.0 or ast_v > 40.0:
                patterns.append(
                    "Hepatic Enzyme Elevation (Transaminitis): ALT or AST liver enzymes exceed upper reference limits, indicating possible hepatic cellular stress or fatty liver pattern. Discuss lifestyle and medications with your clinician."
                )

        cre = m_map.get("creatinine")
        egfr = m_map.get("egfr")
        if cre or egfr:
            c_v = cre["value"] if cre else 0.0
            e_v = egfr["value"] if egfr else 100.0
            if c_v > 1.2 or e_v < 60.0:
                patterns.append(
                    "Renal Clearance Risk Pattern: Elevated serum creatinine (> 1.2 mg/dL) or reduced eGFR (< 60 mL/min) indicates reduced kidney filtration capacity requiring physician evaluation."
                )

        crp = m_map.get("c-reactive protein") or m_map.get("crp")
        wbc = m_map.get("wbc")
        if crp or wbc:
            crp_v = crp["value"] if crp else 0.0
            wbc_v = wbc["value"] if wbc else 0.0
            if crp_v > 5.0 or wbc_v > 11.0:
                patterns.append(
                    "Acute Inflammatory / Immune Response Pattern: Elevated CRP (> 5.0 mg/L) or WBC count (> 11.0 10^3/uL) signals active inflammatory or immune system activation. Review with your doctor."
                )

    if not patterns:
        patterns.append(
            "Optimal Clinical Baseline: All evaluated biomarkers fall within standard reference intervals. Maintain routine annual health monitoring with your physician."
        )

    return patterns
