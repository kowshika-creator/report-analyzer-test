import os
import sys
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from anonymizer import anonymize_text
from gemini_service import parse_reference_interval
from main import compare_biomarkers_with_db
from database import SessionLocal, Base, engine
import models

def test_pii_scrubbing():
    print("\n--- TEST 1: PII Scrubbing Verification ---")
    raw_text_sample = (
        "AXON CLINICAL LABORATORY REPORT\n"
        "Patient Name: Nigel Pearson\n"
        "Referred By: Dr. Albert Hoffman, MD\n"
        "Patient ID: PAT-99120-X\n"
        "Insurance ID: INS-POLICY-882103\n"
        "Contact Email: nigel.p@axonlabs.com\n"
        "Contact Phone: +1 (555) 019-2834\n"
        "Laboratory Address: 1204 Medical Plaza Blvd, Suite 210, Seattle, WA 98104\n"
        "Date of Analysis: 2026-05-31\n"
        "==================================================\n"
        "BIOMARKER            VALUE      UNIT\n"
        "Hemoglobin:          13.5       g/dL\n"
        "Fasting Sugar:       95.0       mg/dL\n"
    )
    
    anonymized = anonymize_text(raw_text_sample)
    print("Anonymized Output:")
    print("-" * 50)
    print(anonymized)
    print("-" * 50)
    
    # Assert PII is redacted
    assert "[REDACTED_NAME]" in anonymized or "Nigel" not in anonymized, "Patient Name not redacted!"
    assert "[REDACTED_PHYSICIAN]" in anonymized or "Hoffman" not in anonymized, "Physician Name not redacted!"
    assert "[REDACTED_ID]" in anonymized, "Patient/Insurance ID not redacted!"
    assert "[REDACTED_EMAIL]" in anonymized, "Email not redacted!"
    assert "[REDACTED_PHONE]" in anonymized, "Phone not redacted!"
    assert "[REDACTED_ADDRESS]" in anonymized, "Address not redacted!"
    assert "[REDACTED_ZIP]" in anonymized, "Zip code not redacted!"
    
    # Assert biomarkers are kept
    assert "Hemoglobin" in anonymized, "Biomarker keyword was incorrectly redacted!"
    assert "13.5" in anonymized, "Biomarker value was incorrectly redacted!"
    print("Test 1: PII Scrubbing PASSED!")

def test_dynamic_ranges():
    print("\n--- TEST 2: Dynamic Reference Ranges Parsing & Prioritization ---")
    
    # Test closed interval
    low, high = parse_reference_interval("12.0 - 17.5")
    assert low == 12.0 and high == 17.5, f"Closed interval failed: {low} - {high}"
    
    # Test open-ended low boundary
    low, high = parse_reference_interval("< 6.0 mg/L")
    assert low == 0.0 and high == 6.0, f"Open-ended low failed: {low} - {high}"
    
    # Test open-ended high boundary
    low, high = parse_reference_interval("> 40 U/L")
    assert low == 40.0 and high == float('inf'), f"Open-ended high failed: {low} - {high}"
    
    # Test database tagging prioritization
    db = SessionLocal()
    try:
        # Mock extracted biomarkers with custom intervals
        # Let's say Hemoglobin is 14.5 (which is normal inside the DB range 12.0 - 17.5)
        # But we pass a physical report interval of "15.0 - 18.0". This should evaluate as "Low"!
        mock_extracted = {
            "Hemoglobin": {
                "value": 14.5,
                "reference_interval": "15.0 - 18.0",
                "unit": "g/dL"
            }
        }
        
        analyzed = compare_biomarkers_with_db(mock_extracted, db)
        assert len(analyzed) == 1
        hemoglobin_result = analyzed[0]
        
        print(f"Biomarker: {hemoglobin_result.biomarker_name}")
        print(f"Value: {hemoglobin_result.value} {hemoglobin_result.unit}")
        print(f"Evaluated Dynamic Limits: {hemoglobin_result.min_normal} - {hemoglobin_result.max_normal}")
        print(f"Evaluated Status: {hemoglobin_result.status}")
        print(f"Description: {hemoglobin_result.description}")
        
        assert hemoglobin_result.status == "Low", f"Should be tagged Low based on dynamic interval! Got: {hemoglobin_result.status}"
        assert hemoglobin_result.min_normal == 15.0, "Did not prioritize dynamic min_normal!"
        assert hemoglobin_result.max_normal == 18.0, "Did not prioritize dynamic max_normal!"
        assert "[Dynamic Ref Interval]" in hemoglobin_result.description, "Dynamic Ref note missing in description!"
        
        print("Test 2: Dynamic Reference Ranges Prioritization PASSED!")
    finally:
        db.close()

def test_database_history():
    print("\n--- TEST 3: Chronological History Database Persistence ---")
    db = SessionLocal()
    try:
        # 1. Create a dummy test user
        test_email = "dynamic_tester@axon.com"
        # Clear if exists
        old_user = db.query(models.User).filter(models.User.email == test_email).first()
        if old_user:
            db.delete(old_user)
            db.commit()
            
        new_user = models.User(email=test_email, hashed_password="mocked_password")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 2. Insert reports with different dates
        import datetime
        report_1 = models.UploadedReport(
            user_id=new_user.id,
            filename="older_report.pdf",
            upload_date=datetime.datetime.utcnow() - datetime.timedelta(days=10),
            patient_summary="Patient summary 1",
            disease_risks=json.dumps(["Risk 1"]),
            language="English"
        )
        report_2 = models.UploadedReport(
            user_id=new_user.id,
            filename="newer_report.pdf",
            upload_date=datetime.datetime.utcnow(),
            patient_summary="Patient summary 2",
            disease_risks=json.dumps(["Risk 2"]),
            language="English"
        )
        db.add(report_1)
        db.add(report_2)
        db.commit()
        db.refresh(report_1)
        db.refresh(report_2)
        
        # 3. Add metrics
        m1 = models.ReportMetric(
            report_id=report_1.id,
            biomarker_name="Hemoglobin",
            value=13.5,
            unit="g/dL",
            min_normal=12.0,
            max_normal=17.5,
            status="Normal"
        )
        m2 = models.ReportMetric(
            report_id=report_2.id,
            biomarker_name="Hemoglobin",
            value=10.5,
            unit="g/dL",
            min_normal=12.0,
            max_normal=17.5,
            status="Low"
        )
        db.add(m1)
        db.add(m2)
        db.commit()
        
        # 4. Query chronological list
        from main import get_metrics_history
        history = get_metrics_history(user_id=new_user.id, db=db)
        
        assert len(history) == 2, f"History should contain 2 reports, got: {len(history)}"
        
        # Verify chronological order (older_report first)
        assert history[0]["filename"] == "older_report.pdf", "Chronological order failed!"
        assert history[1]["filename"] == "newer_report.pdf", "Chronological order failed!"
        
        assert history[0]["normal_count"] == 1
        assert history[0]["abnormal_count"] == 0
        assert history[1]["normal_count"] == 0
        assert history[1]["abnormal_count"] == 1
        
        print("Chronological History Array:")
        print(json.dumps(history, indent=2))
        
        # Clean up
        db.delete(new_user)
        db.commit()
        
        print("Test 3: Chronological History Database Persistence PASSED!")
    finally:
        db.close()

if __name__ == "__main__":
    test_pii_scrubbing()
    test_dynamic_ranges()
    test_database_history()
    print("\nALL DYNAMIC CLINICAL INTELLIGENCE VERIFICATIONS PASSED SUCCESSFULLY!")
