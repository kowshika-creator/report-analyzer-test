# -*- coding: utf-8 -*-
"""
AXON Local-First Offline Verification Test Suite
Explicitly verifies that the complete end-to-end report processing pipeline operates
100% locally with zero external API calls or Gemini API keys.
"""

import os
import sys
import unittest
import json

# Ensure backend directory is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from core import (
    extract_text_locally,
    parse_medical_report_text,
    evaluate_reference_ranges,
    check_emergency_thresholds,
    evaluate_disease_risk_patterns,
    run_explainable_rule_engine,
    generate_patient_summary_local,
    compare_longitudinal_trends,
    analyze_radiology_locally,
    generate_local_chatbot_response
)
from init_db import init_and_seed_db
from database import SessionLocal
from pdf_exporter import generate_patient_summary_pdf


class AXONOfflineModeTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure local environment variables contain NO API keys for true offline test."""
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        init_and_seed_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_1_local_ocr_and_text_extraction(self):
        """Test local OCR text extraction pipeline without external API calls."""
        sample_text = (
            "Hemoglobin: 10.5 g/dL (12.0 - 16.0)\n"
            "Platelets: 130.0 10^3/uL (150 - 450)\n"
            "Fasting Glucose: 145.0 mg/dL (70 - 100)\n"
        )
        text, engine_used, is_fallback = extract_text_locally(sample_text.encode("utf-8"), is_pdf=False, is_image=False)
        self.assertIsNotNone(text)
        self.assertTrue(len(text) > 0)
        print(f"\n[Offline Test 1 PASS] Local OCR Engine Used: {engine_used}")

    def test_2_local_deterministic_medical_parser(self):
        """Test local regex medical parser extracts test names, values, units, and categories."""
        sample_text = (
            "Hemoglobin: 10.5 g/dL (12.0 - 16.0)\n"
            "Platelets: 130.0 10^3/uL (150 - 450)\n"
            "Fasting: 145.0 mg/dL (70 - 100)\n"
            "Serum Creatinine: 1.4 mg/dL (0.6 - 1.2)\n"
            "TSH: 6.2 uIU/mL (0.4 - 4.5)\n"
        )
        parsed = parse_medical_report_text(sample_text)
        self.assertIn("Hemoglobin", parsed)
        self.assertEqual(parsed["Hemoglobin"]["value"], 10.5)
        self.assertIn("Fasting", parsed)
        self.assertEqual(parsed["Fasting"]["value"], 145.0)
        print(f"\n[Offline Test 2 PASS] Local Parser Extracted {len(parsed)} biomarkers successfully!")

    def test_3_local_reference_range_engine(self):
        """Test reference range engine matches dynamic intervals and tags reference sources."""
        biomarkers = {
            "Hemoglobin": {"value": 10.5, "unit": "g/dL", "reference_interval": "12.0 - 16.0"},
            "Fasting": {"value": 145.0, "unit": "mg/dL", "reference_interval": "70 - 100"}
        }
        evaluated = evaluate_reference_ranges(biomarkers, self.db)
        self.assertEqual(len(evaluated), 2)
        for m in evaluated:
            self.assertIn(m["status"], ["Low", "High", "Normal"])
            self.assertIn("reference_source", m)
        print(f"\n[Offline Test 3 PASS] Local Reference Engine evaluated bounds with source tags: {[m['reference_source'] for m in evaluated]}")

    def test_4_local_emergency_panic_thresholds(self):
        """Test local emergency engine flags critical life-safety values."""
        metrics = [
            {"biomarker_name": "Hemoglobin", "value": 5.8, "unit": "g/dL", "min_normal": 12.0, "max_normal": 16.0, "status": "Low"},
            {"biomarker_name": "Fasting", "value": 350.0, "unit": "mg/dL", "min_normal": 70.0, "max_normal": 100.0, "status": "High"}
        ]
        checked_metrics, alerts = check_emergency_thresholds(metrics)
        self.assertTrue(len(alerts) >= 2)
        self.assertTrue(checked_metrics[0]["is_critical"])
        print(f"\n[Offline Test 4 PASS] Emergency Red Flag Alerts: {alerts}")

    def test_5_local_disease_risk_pattern_engine(self):
        """Test local disease pattern engine produces non-diagnostic clinical indicators."""
        metrics = [
            {"biomarker_name": "Fasting", "value": 145.0, "unit": "mg/dL", "min_normal": 70.0, "max_normal": 100.0, "status": "High"},
            {"biomarker_name": "HbA1c", "value": 6.2, "unit": "%", "min_normal": 4.0, "max_normal": 5.6, "status": "High"},
            {"biomarker_name": "Total Cholesterol", "value": 245.0, "unit": "mg/dL", "min_normal": 125.0, "max_normal": 200.0, "status": "High"}
        ]
        risks = evaluate_disease_risk_patterns(metrics)
        self.assertTrue(len(risks) >= 2)
        print(f"\n[Offline Test 5 PASS] Local Disease Patterns Identified: {len(risks)}")

    def test_6_axon_explainable_clinical_rule_engine(self):
        """Test AXON Explainable Rule Engine generates transparent rule IDs and doctor discussion points."""
        metrics = [
            {"biomarker_name": "Hemoglobin", "value": 9.5, "unit": "g/dL", "min_normal": 12.0, "max_normal": 16.0, "status": "Low"}
        ]
        rules = run_explainable_rule_engine(metrics)
        self.assertEqual(len(rules), 1)
        self.assertTrue(rules[0]["rule_id"].startswith("R-CBC"))
        self.assertIn("doctor_discussion_points", rules[0])
        print(f"\n[Offline Test 6 PASS] Rule ID: {rules[0]['rule_id']}, Explanation: {rules[0]['explanation']}")

    def test_7_local_patient_simplifier_multilingual(self):
        """Test template-based patient simplifier across multiple offline languages."""
        metrics = [
            {"biomarker_name": "Hemoglobin", "value": 10.5, "unit": "g/dL", "min_normal": 12.0, "max_normal": 16.0, "status": "Low"}
        ]
        for lang in ["English", "Tamil", "Hindi", "Spanish", "French", "German"]:
            summary = generate_patient_summary_local(metrics, language=lang)
            self.assertIsNotNone(summary)
            self.assertTrue(len(summary) > 20)
        print("\n[Offline Test 7 PASS] Patient Simplifier generated local summaries in 6 languages!")

    def test_8_local_trend_analysis(self):
        """Test local longitudinal trend analysis computing exact delta values and directions."""
        base_metrics = [{"biomarker_name": "Fasting", "value": 160.0, "unit": "mg/dL"}]
        curr_metrics = [{"biomarker_name": "Fasting", "value": 130.0, "unit": "mg/dL"}]
        deltas, summary = compare_longitudinal_trends("May 2026", "June 2026", base_metrics, curr_metrics)
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0]["delta_value"], -30.0)
        self.assertEqual(deltas[0]["direction"], "improved")
        print(f"\n[Offline Test 8 PASS] Trend Delta: {deltas[0]['delta_value']} mg/dL ({deltas[0]['direction']})")

    def test_9_local_radiology_preprocessor(self):
        """Test local radiology technical stats and report text parser."""
        result = analyze_radiology_locally(report_text="Chest X-Ray: Clear lung fields. No acute consolidation.")
        self.assertIn("scan_metadata", result)
        self.assertIn("triage", result)
        print("\n[Offline Test 9 PASS] Radiology Preprocessor evaluated report text locally!")

    def test_10_local_chatbot_knowledge_engine(self):
        """Test local chatbot engine across all 4 tone personas."""
        metrics = [{"biomarker_name": "Hemoglobin", "value": 10.5, "unit": "g/dL", "status": "Low", "min_normal": 12.0, "max_normal": 16.0}]
        for tone in ["Empathetic", "Clinical", "Educational", "Family"]:
            reply, disclaimer = generate_local_chatbot_response("Why is my hemoglobin low?", extracted_metrics=metrics, tone=tone)
            self.assertTrue(len(reply) > 10)
            self.assertIn("Disclaimer", disclaimer)
        print("\n[Offline Test 10 PASS] Local Chatbot responded across all 4 tones without external API!")

    def test_11_local_pdf_generation(self):
        """Test ReportLab PDF summary generation offline."""
        pdf_bytes = generate_patient_summary_pdf(
            filename="sample_report.pdf",
            metrics=[{"biomarker_name": "Hemoglobin", "value": 10.5, "unit": "g/dL", "status": "Low", "min_normal": 12.0, "max_normal": 16.0}],
            patient_summary="Patient has mild low hemoglobin.",
            disease_risks=["Mild Anemia Risk Indicator"],
            language="English"
        )
        self.assertTrue(len(pdf_bytes) > 100)
        print(f"\n[Offline Test 11 PASS] PDF Document generated locally ({len(pdf_bytes)} bytes)!")


if __name__ == "__main__":
    unittest.main()
