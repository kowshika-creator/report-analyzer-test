import os
import json
import sys

# Ensure backend directory is in python search path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from database import SessionLocal, Base, engine
    import models
    from models import ReferenceRange
    from init_db import init_and_seed_db
    from gemini_service import extract_biomarkers_with_gemini, analyze_holistic_risks
    from main import compare_biomarkers_with_db
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please make sure you run this script from the workspace root.")
    sys.exit(1)

def run_integration_test(language: str = "English"):
    print("=" * 60)
    print(f"RUNNING AUTOMATED INTEGRATION TEST [Language: {language}]")
    print("=" * 60)
    
    # 1. Initialize and Seed the database
    print("\n[Step 1] Initializing and Seeding SQLite Clinical Reference Database...")
    init_and_seed_db()
    
    # 2. Read raw medical test report
    report_path = os.path.join(os.path.dirname(__file__), "mock_blood_report.txt")
    print(f"\n[Step 2] Reading raw test file: {report_path}...")
    if not os.path.exists(report_path):
        print(f"Error: {report_path} does not exist!")
        return
        
    with open(report_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    print("-" * 40)
    print("Raw Medical Text Sample:")
    print(raw_text[:350] + "\n...")
    print("-" * 40)

    # 3. Pipeline Step 2: Structured Data Parsing via Gemini
    print("\n[Step 3] Parsing Structured Biomarkers using AI Parser Service...")
    extracted_biomarkers = extract_biomarkers_with_gemini(raw_text)
    print(f"Extracted Biomarker JSON Payload: {json.dumps(extracted_biomarkers, indent=2)}")

    # 4. Pipeline Step 3: Database Comparison and Range Tagging
    print("\n[Step 4] Querying SQLite and Tagging Biomarkers against reference ranges...")
    db = SessionLocal()
    try:
        analyzed_metrics = compare_biomarkers_with_db(extracted_biomarkers, db)
        
        # Convert Pydantic schemas to dictionary format
        metrics_list = [m.model_dump() for m in analyzed_metrics]
        
        # 5. Pipeline Step 4: Holistic Disease Predictor & Translation
        print("\n[Step 5] Running holistic Disease Risk Predictor and Multilingual Patient Simplifier...")
        holistic_analysis = analyze_holistic_risks(metrics_list, language)
        
        # 6. Test Chat Companion router fallback contextually
        print("\n[Step 6] Testing medical chatbot companion contextually (e.g. asking about fatigue)...")
        from chat_router import run_local_chatbot_fallback
        from schemas import MetricAnalysis
        
        mock_query = "Why am I feeling so tired and weak?"
        parsed_metrics_objects = [MetricAnalysis(**m) for m in metrics_list]
        chat_reply = run_local_chatbot_fallback(mock_query, parsed_metrics_objects)
        
        print(f"User Query: '{mock_query}'")
        print(f"Chatbot Companion Response:\n{chat_reply}")
        print("-" * 50)
        
        # 7. Build Final Response Payload
        final_payload = {
            "filename": "mock_blood_report.txt",
            "status": "success",
            "language": language,
            "disease_risks": holistic_analysis.get("disease_risks", []),
            "patient_summary": holistic_analysis.get("patient_summary", ""),
            "metrics": metrics_list,
            "mock_chat_test": {
                "query": mock_query,
                "response": chat_reply
            }
        }
        
        print("\n" + "=" * 60)
        print("FINAL INTEGRATION TEST JSON RESPONSE PAYLOAD:")
        print("=" * 60)
        print(json.dumps(final_payload, indent=2, ensure_ascii=True))
        print("=" * 60)
        
        # 8. Test Image OCR Extraction Pathway
        print("\n[Step 8] Testing Image OCR pre-processing and extraction pipeline...")
        try:
            from PIL import Image, ImageDraw
            import io
            
            # Create an in-memory test image with a white background and some black text
            img = Image.new('RGB', (300, 100), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((20, 20), "Hemoglobin: 10.5 g/dL\nFasting: 145.0 mg/dL", fill=(0, 0, 0))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            from main import extract_text_from_image
            extracted_img_text = extract_text_from_image(img_bytes)
            print("Image OCR Extraction pipeline succeeded!")
            print(f"Extracted Image Text snippet:\n{extracted_img_text[:150]}")
            print("-" * 50)
            
            # Add to final payload
            final_payload["mock_image_ocr_test"] = {
                "status": "success",
                "extracted_snippet": extracted_img_text[:150]
            }
        except Exception as img_err:
            print(f"Image pipeline verification failed: {img_err}")

        # 9. Test PDF Report Generation Engine
        print("\n[Step 9] Testing ReportLab PDF Health Summary Exporter...")
        try:
            from pdf_exporter import generate_patient_summary_pdf
            pdf_bytes = generate_patient_summary_pdf(
                filename="mock_blood_report.txt",
                metrics=metrics_list,
                patient_summary=holistic_analysis.get("patient_summary", ""),
                disease_risks=holistic_analysis.get("disease_risks", []),
                language=language
            )
            pdf_out_path = os.path.join(os.path.dirname(__file__), "test_patient_summary.pdf")
            with open(pdf_out_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)
            print(f"PDF Exporter Engine succeeded! Generated {len(pdf_bytes)} bytes PDF at: {pdf_out_path}")
            final_payload["pdf_export_test"] = {
                "status": "success",
                "bytes_generated": len(pdf_bytes),
                "pdf_path": pdf_out_path
            }
        except Exception as pdf_err:
            print(f"PDF export engine verification failed: {pdf_err}")

        # 10. Test Longitudinal Trend Delta Analysis Engine
        print("\n[Step 10] Testing Longitudinal Multi-Report Delta Analysis Engine...")
        try:
            from main import compare_report_trends
            from schemas import TrendComparisonRequest
            
            # Create two test reports in DB to compare deltas
            rep_base = models.UploadedReport(user_id=1, filename="report_june_2025.pdf", patient_summary="June Report")
            db.add(rep_base)
            db.commit()
            db.refresh(rep_base)
            
            m1 = models.ReportMetric(report_id=rep_base.id, biomarker_name="Fasting Glucose", value=157.0, unit="mg/dL", min_normal=70.0, max_normal=100.0, status="High")
            m2 = models.ReportMetric(report_id=rep_base.id, biomarker_name="Hemoglobin", value=9.7, unit="g/dL", min_normal=12.0, max_normal=17.5, status="Low")
            db.add_all([m1, m2])
            db.commit()

            rep_curr = models.UploadedReport(user_id=1, filename="report_july_2025.pdf", patient_summary="July Report")
            db.add(rep_curr)
            db.commit()
            db.refresh(rep_curr)

            m3 = models.ReportMetric(report_id=rep_curr.id, biomarker_name="Fasting Glucose", value=145.0, unit="mg/dL", min_normal=70.0, max_normal=100.0, status="High")
            m4 = models.ReportMetric(report_id=rep_curr.id, biomarker_name="Hemoglobin", value=10.5, unit="g/dL", min_normal=12.0, max_normal=17.5, status="Low")
            db.add_all([m3, m4])
            db.commit()

            trend_resp = compare_report_trends(TrendComparisonRequest(baseline_report_id=rep_base.id, current_report_id=rep_curr.id), db)
            print(f"Longitudinal Delta Comparison Succeeded! Deltas computed: {len(trend_resp.deltas)}")
            for d in trend_resp.deltas:
                print(f"  • {d.insight_text}")
                
            final_payload["longitudinal_trend_test"] = {
                "status": "success",
                "summary": trend_resp.longitudinal_summary,
                "deltas_count": len(trend_resp.deltas)
            }
        except Exception as trend_err:
            print(f"Longitudinal trend test failed: {trend_err}")

        # Write test output to workspace log for user inspection
        output_log = os.path.join(os.path.dirname(__file__), "test_integration_output.json")
        with open(output_log, "w", encoding="utf-8") as out:
            json.dump(final_payload, out, indent=2, ensure_ascii=False)
        print(f"\nIntegration test results saved to: {output_log}")
        
    except Exception as e:
        print(f"Integration pipeline execution failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Support custom language input if passed
    lang = "English"
    if len(sys.argv) > 1:
        lang = sys.argv[1]
    run_integration_test(lang)
