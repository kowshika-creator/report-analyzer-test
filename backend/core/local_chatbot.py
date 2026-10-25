from typing import List, Dict, Any, Optional

DISCLAIMER_TEXT = (
    "Disclaimer: This AI chatbot companion provides educational insights based on your parsed lab report. "
    "These findings do NOT replace a professional consultation, medical diagnosis, or personalized treatment plan "
    "from your licensed physician or healthcare provider."
)

FAQ_KNOWLEDGE_BASE = {
    "tired": "Feeling tired or fatigued can be associated with low hemoglobin (anemia), low thyroid hormone (TSH elevation), low Vitamin D, or insufficient sleep. Review your CBC and Thyroid panels.",
    "fatigue": "Fatigue can stem from low red blood cells (anemia), thyroid underactivity, elevated blood sugar, or inflammatory responses.",
    "sugar": "Blood sugar levels are evaluated via Fasting Glucose (normal: 70-99 mg/dL) and HbA1c (normal: < 5.7%). High levels may indicate prediabetes or diabetes.",
    "cholesterol": "Cholesterol includes LDL ('bad' cholesterol), HDL ('good' cholesterol), and Triglycerides. Elevated LDL (> 100 mg/dL) increases cardiovascular risk.",
    "thyroid": "The thyroid gland regulates metabolism. High TSH (> 4.5 uIU/mL) indicates an underactive thyroid (hypothyroidism), while low TSH (< 0.4 uIU/mL) suggests hyperthyroidism.",
    "liver": "Liver health is checked using ALT, AST, ALP, and Bilirubin enzymes. Elevated ALT or AST (> 40 U/L) signals liver cell inflammation or stress.",
    "kidney": "Kidney function is assessed via Creatinine (normal: 0.6-1.2 mg/dL), BUN, and eGFR (> 60 mL/min). Elevated creatinine suggests reduced renal filtration clearance.",
    "anemia": "Anemia occurs when your hemoglobin or red blood cell count falls below normal bounds, reducing oxygen delivery to body tissues.",
    "vitamin": "Vitamins such as Vitamin D (bone health & immunity) and Vitamin B12 (nerve function & red cells) are essential micronutrients."
}

def generate_local_chatbot_response(
    user_query: str,
    extracted_metrics: Optional[List[Dict[str, Any]]] = None,
    scan_context: Optional[Dict[str, Any]] = None,
    tone: str = "Empathetic",
    language: str = "English"
) -> Tuple[str, str]:
    """
    Local Knowledge-Base Chatbot Engine:
    Searches user report metrics or radiology scan findings, local biomarker definitions,
    and FAQ medical knowledge base to construct deterministic responses in 4 tones and 7 languages.
    Works 100% offline.
    """
    query_lower = user_query.lower().strip()
    extracted_metrics = extracted_metrics or []
    
    # 0. Check if this is a Radiology / Imaging Scan report query
    if scan_context:
        metadata = scan_context.get("scan_metadata", {})
        modality = metadata.get("modality", "Imaging Scan")
        region = metadata.get("body_region", "Anatomical Region")
        triage = scan_context.get("triage", {})
        headline = triage.get("summary_headline", "")
        is_emer = triage.get("is_emergency", False)
        impression = scan_context.get("radiologist_impression_summary", "")
        findings = scan_context.get("findings_breakdown", [])
        questions = scan_context.get("questions_for_doctor", [])

        # Check query intent for scan reports
        if any(w in query_lower for w in ["impression", "mean", "summary", "conclusion"]):
            response_body = (
                f"### {modality} ({region}) - Radiologist Impression:\n\n"
                f"{impression}\n\n"
                f"**Clinical Summary:** {headline}\n\n"
                f"*(Note: This AI translates the written report narrative into plain language. It does not re-interpret physical images.)*"
            )
            return response_body, DISCLAIMER_TEXT

        if any(w in query_lower for w in ["abnormal", "urgent", "critical", "issue", "problem", "finding", "concern"]):
            abnormal_items = [f for f in findings if f.get("category") in ["abnormal", "urgent"]]
            if abnormal_items:
                items_str = "\n".join([f"• **{f.get('finding_text', '')}**: {f.get('plain_english_explanation', '')} (Clinical relevance: {f.get('clinical_significance', 'Requires review')})" for f in abnormal_items])
                response_body = (
                    f"### Key Findings from your {modality} Report:\n\n"
                    f"{items_str}\n\n"
                    f"Please review these specific points with your physician during your next clinical appointment."
                )
            else:
                response_body = (
                    f"Good news: No major abnormal or urgent findings were flagged in your {modality} ({region}) report text. "
                    f"Baseline anatomy was described within expected parameters."
                )
            return response_body, DISCLAIMER_TEXT

        if any(w in query_lower for w in ["doctor", "question", "ask", "appointment"]):
            if questions:
                q_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
                response_body = (
                    f"### Suggested Questions for Your Physician:\n\n"
                    f"{q_list}\n\n"
                    f"Bringing these specific questions to your consultation will help you discuss the findings clearly."
                )
            else:
                response_body = (
                    f"When reviewing your {modality} ({region}) report with your doctor, you might ask:\n"
                    f"1. How do these scan findings correlate with my current symptoms?\n"
                    f"2. Are any follow-up imaging scans or treatments recommended?"
                )
            return response_body, DISCLAIMER_TEXT

        # General scan response
        response_body = (
            f"You are currently viewing a **{modality} of the {region}**.\n\n"
            f"• **Summary:** {headline}\n"
            f"• **Impression:** {impression}\n\n"
            f"Feel free to ask: *'What does this impression mean?'*, *'Are there any abnormal findings?'*, or *'What questions should I ask my doctor?'*"
        )
        return response_body, DISCLAIMER_TEXT

    metrics_map = {m["biomarker_name"].lower(): m for m in extracted_metrics}

    # 1. Search Extracted Report Metrics for direct context matches
    matched_metric = None
    for name, data in metrics_map.items():
        if name in query_lower:
            matched_metric = data
            break

    response_body = ""

    if matched_metric:
        name = matched_metric["biomarker_name"]
        val = matched_metric["value"]
        unit = matched_metric["unit"]
        status = matched_metric["status"]
        min_n = matched_metric["min_normal"]
        max_n = matched_metric["max_normal"]

        if tone.lower() == "clinical":
            response_body = (
                f"BIOMARKER ANALYSIS: {name}\n"
                f"- Measured Value: {val} {unit}\n"
                f"- Status Tag: {status.upper()}\n"
                f"- Reference Interval: {min_n} - {max_n} {unit}\n"
                f"- Diagnostic Finding: Value is tagged as {status} relative to standard bounds."
            )
        elif tone.lower() == "educational":
            response_body = (
                f"Biological Pathway Explanation for {name}:\n"
                f"Your measured level is {val} {unit}, which is tagged as {status} (normal range: {min_n} - {max_n} {unit}). "
                f"{name} plays a critical physiological role in cellular homeostasis. When levels are {status.lower()}, "
                f"cellular metabolic pathways adjust accordingly. Discuss specific enzyme pathways with your doctor."
            )
        elif tone.lower() == "family":
            response_body = (
                f"Here is what your test says in very simple terms:\n"
                f"Your {name} level is {val}. The normal target is between {min_n} and {max_n}. "
                f"Since it is {status.lower()}, it means your body might need a little extra care or simple food adjustments. Everything can be discussed easily with your doctor!"
            )
        else: # Empathetic (default)
            response_body = (
                f"Thank you for asking about your {name}. Your current test shows a value of {val} {unit}, which is {status.lower()} "
                f"compared to the reference range ({min_n} - {max_n} {unit}). "
                f"Please rest assured that a single lab number is best understood in context with your overall health. I recommend sharing this finding with your physician."
            )
    else:
        # Check if user asked about out-of-range or abnormal lab values
        if any(w in query_lower for w in ["out of range", "abnormal", "high", "low", "critical", "flagged"]):
            abnormal_metrics = [m for m in extracted_metrics if m.get("status", "").lower() in ["low", "high", "critical"]]
            if abnormal_metrics:
                m_list = "\n".join([f"• **{m['biomarker_name']}**: {m['value']} {m['unit']} (Tag: {m['status']}, Target: {m['min_normal']}-{m['max_normal']} {m['unit']})" for m in abnormal_metrics])
                response_body = (
                    f"### Out-of-Range Lab Values Detected ({len(abnormal_metrics)}):\n\n"
                    f"{m_list}\n\n"
                    f"I recommend sharing these specific parameters with your doctor to discuss whether lifestyle or dietary modifications are recommended."
                )
                return response_body, DISCLAIMER_TEXT
            elif extracted_metrics:
                response_body = "All extracted lab biomarkers currently fall within their standard clinical reference ranges! None are flagged as out of range."
                return response_body, DISCLAIMER_TEXT

        # 2. Search FAQ medical knowledge base
        matched_faq = None
        for keyword, faq_text in FAQ_KNOWLEDGE_BASE.items():
            if keyword in query_lower:
                matched_faq = faq_text
                break

        if matched_faq:
            response_body = f"Regarding your query about '{user_query}':\n\n{matched_faq}"
        else:
            response_body = (
                f"Thank you for your query regarding '{user_query}'.\n"
                "In AXON Local Engine Mode, I analyze your specific laboratory metrics (CBC, Blood Sugar, Lipid, LFT, KFT, Thyroid) "
                "or radiology scan findings (MRI, CT, X-Ray, Ultrasound) and explain test values, findings, reference bounds, and health patterns. "
                "If you have a specific test or finding from your report you'd like to inspect, feel free to mention its name!"
            )

    return response_body, DISCLAIMER_TEXT
