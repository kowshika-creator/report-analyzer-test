import re

def anonymize_text(text: str) -> str:
    """
    Scans the raw extracted text and immediately purges personal identifiable 
    information (PII) such as street addresses, phone numbers, emails, names, 
    or insurance/patient IDs while leaving clinical biomarkers completely intact.
    """
    if not text:
        return text
    
    anonymized = text
    
    # 1. Redact Emails
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    anonymized = re.sub(email_pattern, '[REDACTED_EMAIL]', anonymized)
    
    # 2. Redact Phone Numbers
    # Matches various standard formats: +1-123-456-7890, (123) 456-7890, 123-456-7890, 9876543210, etc.
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    anonymized = re.sub(phone_pattern, '[REDACTED_PHONE]', anonymized)
    
    # List of common medical biomarkers and keywords to protect from false-positive name/ID redactions
    biomarker_keywords = [
        "hemoglobin", "haemoglobin", "hb", "hgb", "wbc", "leukocytes", "platelets", "plt", "thrombocytes",
        "rbc", "erythrocytes", "neutrophils", "neut", "hba1c", "glycated", "fasting", "fbs", "glucose",
        "cholesterol", "hdl", "ldl", "triglycerides", "trig", "alt", "sgpt", "ast", "sgot", "bilirubin",
        "tbil", "dbil", "alkaline", "phosphatase", "alp", "albumin", "alb", "creatinine", "cre", "bun",
        "egfr", "gfr", "tsh", "thyroid", "thyroxine", "t3", "t4", "crp", "c-reactive", "protein", "cells",
        "interval", "biological", "ref", "value", "unit", "range", "normal", "low", "high", "patient summary",
        "disease risks", "analysis"
    ]
    
    # 3. Redact Patient / Insurance / Policy / Doctor IDs / UHID / MRN
    # Matches "Patient ID: 12345", "Insurance No: ABC-123", "UHID - 9812", etc.
    id_pattern = r'(?i)\b(insurance(?:[\s_-]?(?:id|no|num|number))|patient(?:[\s_-]?(?:id|no|num|number|ref))|policy(?:[\s_-]?(?:id|no|num|number))|mrn|ssn|ref(?:erence)?(?:[\s_-]?(?:id|no|num|number))?|uhid|hosp(?:ital)?(?:[\s_-]?id)?)\s*[:\-\s=]\s*([a-zA-Z0-9\-/]+)'
    def replace_id(match):
        label = match.group(1)
        # Avoid redacting biomarker headings or lines
        if any(keyword in label.lower() for keyword in biomarker_keywords):
            return match.group(0)
        return f"{label}: [REDACTED_ID]"
    anonymized = re.sub(id_pattern, replace_id, anonymized)
    
    # 4. Redact Patient Names
    # Matches "Patient Name: John Doe", "Name: Jane Smith"
    name_pattern = r'(?i)\b(patient\s*name|patient|name)\s*[:\-\s=]\s*([a-zA-Z\s\.]+)(?=\n|$)'
    def replace_name(match):
        label = match.group(1)
        name_val = match.group(2).strip()
        # Verify that we are not redacting a biomarker or standard clinical label
        name_lower = name_val.lower()
        if any(re.search(rf'\b{re.escape(k)}\b', name_lower) for k in biomarker_keywords):
            return match.group(0)
        return f"{label}: [REDACTED_NAME]"
    anonymized = re.sub(name_pattern, replace_name, anonymized)
    
    # 5. Redact Referred Physician / Doctor Names
    doc_pattern = r'(?i)\b(referred\s*by|ref\.\s*physician|doctor|physician|dr\.)\s*[:\-\s=]\s*([a-zA-Z\s\.\,\-]+)(?=\n|$)'
    def replace_doc(match):
        label = match.group(1)
        doc_val = match.group(2).strip()
        doc_lower = doc_val.lower()
        if any(re.search(rf'\b{re.escape(k)}\b', doc_lower) for k in biomarker_keywords):
            return match.group(0)
        return f"{label}: [REDACTED_PHYSICIAN]"
    anonymized = re.sub(doc_pattern, replace_doc, anonymized)
    
    # 6. Redact Street Addresses
    # Matches common formats like: 123 Main St, 456 Oak Avenue, 789 Pine Road, etc.
    address_pattern = r'(?i)\b\d+(?:\s+[a-zA-Z0-9\.\-]+){1,5}\s+(?:street|st|avenue|ave|road|rd|blvd|lane|ln|drive|dr|court|ct|plaza|plz|highway|hwy|square|sq|way)\b'
    anonymized = re.sub(address_pattern, '[REDACTED_ADDRESS]', anonymized)
    
    # 7. Redact ZIP / Postal Codes (5-digit or 5+4 digit formats)
    zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
    anonymized = re.sub(zip_pattern, '[REDACTED_ZIP]', anonymized)
    
    return anonymized
