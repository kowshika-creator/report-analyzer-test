from typing import List, Dict, Any

# Local multilingual dictionaries for patient summaries
MULTILINGUAL_SUMMARY_HEADERS = {
    "English": {
        "header": "AXON Patient Health Summary (Local Engine)",
        "all_normal": "Good news! All evaluated biomarkers fall within normal standard reference bounds.",
        "abnormal_intro": "Here is a clear breakdown of your lab report results in simple terms:",
        "normal_text": "is within your normal expected range",
        "low_text": "is lower than the expected normal range",
        "high_text": "is higher than the expected normal range",
        "disclaimer": "This summary is generated for educational understanding. Please discuss these findings with your doctor for diagnostic guidance."
    },
    "Tamil": {
        "header": "AXON நோயாளி சுகாதார சுருக்கம் (உள்ளூர் இன்ஜின்)",
        "all_normal": "நற்செய்தி! அனைத்து பரிசோதனை முடிவுகளும் இயல்பான வரம்பிற்குள் உள்ளன.",
        "abnormal_intro": "உங்கள் மருத்துவ சோதனையின் எளிய விளக்கக் குறிப்பு கீழே கொடுக்கப்பட்டுள்ளது:",
        "normal_text": "இயல்பான வரம்பிற்குள் உள்ளது",
        "low_text": "எதிர்பார்க்கப்பட்ட இயல்பான வரம்பை விட குறைவாக உள்ளது",
        "high_text": "எதிர்பார்க்கப்பட்ட இயல்பான வரம்பை விட அதிகமாக உள்ளது",
        "disclaimer": "இந்த சுருக்கம் கல்வி மற்றும் விழிப்புணர்வுக்காக வழங்கப்படுகிறது. மருத்துவ ஆலோசனைக்கு உங்கள் மருத்துவரை அணுகவும்."
    },
    "Hindi": {
        "header": "AXON रोगी स्वास्थ्य सारांश (लोकल इंजन)",
        "all_normal": "अच्छी खबर! सभी जांच परिणाम सामान्य सीमा के भीतर हैं।",
        "abnormal_intro": "आपकी लैब रिपोर्ट के परिणामों का सरल विवरण नीचे दिया गया है:",
        "normal_text": "सामान्य सीमा के भीतर है",
        "low_text": "सामान्य सीमा से कम है",
        "high_text": "सामान्य सीमा से अधिक है",
        "disclaimer": "यह सारांश केवल जानकारी के लिए है। सटीक निदान के लिए अपने डॉक्टर से परामर्श करें।"
    },
    "Telugu": {
        "header": "AXON పేషెంట్ హెల్త్ సారాంశం (లోకల్ ఇంజిన్)",
        "all_normal": "మంచి వార్త! పరీక్ష ఫలితాలన్నీ సాధారణ పరిమితిలోనే ఉన్నాయి.",
        "abnormal_intro": "మీ ల్యాబ్ నివేదిక వివరాల సులభమైన వివరణ ఇక్కడ ఉంది:",
        "normal_text": "సాధారణ పరిమితిలోనే ఉంది",
        "low_text": "సాధారణ పరిమితి కంటే తక్కువగా ఉంది",
        "high_text": "సాధారణ పరిమితి కంటే ఎక్కువగా ఉంది",
        "disclaimer": "ఈ వివరాలు అవగాహన కోసం మాత్రమే. చికిత్స కోసం మీ వైద్యుడిని సంప్రదించండి."
    },
    "Spanish": {
        "header": "Resumen de Salud del Paciente AXON (Motor Local)",
        "all_normal": "¡Buenas noticias! Todos los marcadores están dentro del rango normal.",
        "abnormal_intro": "Aquí tiene una explicación sencilla de los resultados de su informe médico:",
        "normal_text": "está dentro de su rango normal esperado",
        "low_text": "está por debajo del rango normal esperado",
        "high_text": "está por encima del rango normal esperado",
        "disclaimer": "Este resumen es solo para fines educativos. Consulte a su médico para obtener un diagnóstico formal."
    },
    "French": {
        "header": "Résumé de Santé AXON (Moteur Local)",
        "all_normal": "Bonne nouvelle! Tous les biomarqueurs sont dans les limites normales.",
        "abnormal_intro": "Voici une explication simple et claire de vos résultats d'analyse:",
        "normal_text": "est dans la plage normale attendue",
        "low_text": "est inférieur à la plage normale attendue",
        "high_text": "est supérieur à la plage normale attendue",
        "disclaimer": "Ce résumé est fourni à titre éducatif. Veuillez consulter votre médecin pour un avis médical."
    },
    "German": {
        "header": "AXON Patientengesundheitszusammenfassung (Lokaler Motor)",
        "all_normal": "Gute Nachrichten! Alle gemessenen Werte liegen im normalen Referenzbereich.",
        "abnormal_intro": "Hier ist eine einfache und verständliche Erklärung Ihrer Laborergebnisse:",
        "normal_text": "liegt im erwarteten normalen Bereich",
        "low_text": "liegt unter dem normalen Bereich",
        "high_text": "liegt über dem normalen Bereich",
        "disclaimer": "Diese Zusammenfassung dient nur zu Informationszwecken. Besprechen Sie die Ergebnisse mit Ihrem Arzt."
    }
}

# Biomarker plain English explanations database
BIOMARKER_EXPLANATIONS = {
    "Hemoglobin": "Hemoglobin is the iron-rich protein in red blood cells that carries oxygen from your lungs to your body.",
    "WBC": "White blood cells are your body's primary defense system fighting off bacterial and viral infections.",
    "Platelets": "Platelets are specialized blood cell fragments that help your blood clot to prevent bleeding.",
    "Fasting": "Fasting glucose measures the sugar level in your blood after an overnight fast.",
    "HbA1c": "HbA1c measures your average blood sugar levels over the past 2 to 3 months.",
    "Total Cholesterol": "Total cholesterol represents the overall amount of lipids circulating in your bloodstream.",
    "HDL": "HDL is known as 'good cholesterol' because it helps clear excess fat from your blood vessels.",
    "LDL": "LDL is often called 'bad cholesterol' because high levels can form plaque in blood vessels.",
    "Triglycerides": "Triglycerides are a type of fat stored in your body for energy between meals.",
    "ALT": "ALT is an enzyme found mainly in liver cells. Higher levels can indicate liver cell stress.",
    "AST": "AST is an enzyme found in the liver and heart. It helps assess tissue inflammation.",
    "Creatinine": "Creatinine is a waste product from muscle metabolism filtered out by healthy kidneys.",
    "TSH": "TSH is a brain messenger hormone that controls your thyroid gland's metabolic output.",
    "C-Reactive Protein": "CRP is a blood protein that increases when there is active inflammation or infection in your body."
}

def generate_patient_summary_local(metrics: List[Dict[str, Any]], language: str = "English") -> str:
    """
    Generates a patient-friendly summary locally using template interpolation.
    Supports English, Tamil, Hindi, Telugu, Spanish, French, and German.
    """
    lang_dict = MULTILINGUAL_SUMMARY_HEADERS.get(language, MULTILINGUAL_SUMMARY_HEADERS["English"])
    
    abnormal_metrics = [
        m for m in metrics 
        if m.get("status") in ["Low", "High"] 
        and m.get("value") is not None 
        and not m.get("requires_review")
    ]
    unreviewed_metrics = [
        m for m in metrics 
        if m.get("requires_review") or m.get("status") in ["Unreviewed (Incompatible Unit)", "Unparseable / Missing"]
    ]
    
    summary_lines = [f"### {lang_dict['header']}\n"]

    if not abnormal_metrics and not unreviewed_metrics:
        summary_lines.append(f"{lang_dict['all_normal']}\n")
    elif abnormal_metrics:
        summary_lines.append(f"{lang_dict['abnormal_intro']}\n")
        for m in abnormal_metrics:
            name = m["biomarker_name"]
            val = m["value"]
            unit = m["unit"]
            status = m["status"]
            status_text = lang_dict["low_text"] if status == "Low" else lang_dict["high_text"]
            
            expl = BIOMARKER_EXPLANATIONS.get(name, f"{name} is a key biological metric evaluated in your blood sample.")
            
            line = f"- **{name}** ({val} {unit}): {status_text}. {expl}"
            summary_lines.append(line)

    if unreviewed_metrics:
        unrev_names = ", ".join([m["biomarker_name"] for m in unreviewed_metrics])
        summary_lines.append(f"\n*Clinical Notice: The following metrics require physician review due to unverified units or unclear values: {unrev_names}.*")

    summary_lines.append(f"\n*{lang_dict['disclaimer']}*")
    return "\n".join(summary_lines)
