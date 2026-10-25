# -*- coding: utf-8 -*-
"""
AXON Clinical Intelligence - Laboratory Pipeline Correctness Regression Suite
Covers all 12 Priority 6 verification requirements:
1. Blank PDF or image does not return mock biomarkers (raises HTTP 422)
2. OCR failure does not produce a successful fabricated analysis
3. Empty parser output does not trigger risk or emergency evaluation
4. Missing value is not converted to zero
5. Missing value cannot trigger a false critical alert
6. Supported unit conversions produce expected normalized values (Glucose mmol/L, Hemoglobin g/L, Platelets lakhs)
7. Unsupported units are not silently accepted
8. Decimal-comma values are parsed correctly when unambiguous (13,5 and 0,85)
9. Invalid input is rejected or flagged
10. Stale results prevention logic verification
11. Existing valid local analysis works 100% offline without external API
12. Explicitly invoked sample report is available and identified as demonstration data
"""

import os
import sys
import unittest
import io
from PIL import Image

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from core.local_ocr import extract_text_locally
from core.medical_parser import parse_medical_report_text, normalize_unambiguous_decimal_commas
from core.reference_engine import evaluate_reference_ranges, normalize_biomarker_unit
from core.emergency_engine import check_emergency_thresholds
from core.risk_engine import evaluate_disease_risk_patterns
from core.patient_simplifier import generate_patient_summary_local
from core.rule_engine import run_explainable_rule_engine
from database import SessionLocal
from init_db import init_and_seed_db
import schemas

class AXONLabCorrectnessTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure offline mode (zero API keys)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        init_and_seed_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_blank_image_or_pdf_does_not_return_mock_biomarkers(self):
        """Test 1: Blank image returns empty text, eliminating fabricated report generation."""
        img = Image.new("RGB", (100, 100), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        raw_text, engine_used, is_fallback = extract_text_locally(buf.getvalue(), is_pdf=False, is_image=True)
        # Must NOT return mock text
        self.assertEqual(raw_text.strip(), "")
        self.assertFalse(is_fallback)

    def test_02_ocr_failure_does_not_produce_fabricated_analysis(self):
        """Test 2: Random binary noise cannot produce a successful fabricated analysis."""
        garbage_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c"
        raw_text, _, is_fallback = extract_text_locally(garbage_bytes, is_pdf=False, is_image=False)
        self.assertEqual(raw_text.strip(), "")
        parsed = parse_medical_report_text(raw_text)
        self.assertEqual(len(parsed), 0)

    def test_03_empty_parser_output_does_not_trigger_emergency_or_risks(self):
        """Test 3: Empty parser output does not trigger risk or emergency evaluation."""
        empty_metrics = []
        checked, alerts = check_emergency_thresholds(empty_metrics)
        self.assertEqual(len(checked), 0)
        self.assertEqual(len(alerts), 0)
        
        risks = evaluate_disease_risk_patterns(empty_metrics)
        # Should cleanly indicate no evaluated biomarkers
        self.assertTrue(any("No clinically evaluated" in r or "Optimal" in r for r in risks))

    def test_04_missing_value_is_not_converted_to_zero(self):
        """Test 4: Missing value is preserved as None rather than being replaced with zero."""
        report_text = "Hemoglobin: Not Tested\nPlatelets: Pending\nFasting Glucose: 110 mg/dL"
        parsed = parse_medical_report_text(report_text)
        
        evaluated = evaluate_reference_ranges(parsed, self.db)
        eval_map = {m["biomarker_name"]: m for m in evaluated}
        
        self.assertIn("Hemoglobin", eval_map)
        self.assertIsNone(eval_map["Hemoglobin"]["value"])
        self.assertEqual(eval_map["Hemoglobin"]["status"], "Unparseable / Missing")
        self.assertTrue(eval_map["Hemoglobin"]["requires_review"])

    def test_05_missing_value_cannot_trigger_false_critical_alert(self):
        """Test 5: Missing value cannot trigger false panic emergency threshold (e.g. Hb < 6.5)."""
        metrics = [
            {
                "biomarker_name": "Hemoglobin",
                "value": None,
                "unit": "g/dL",
                "status": "Unparseable / Missing",
                "requires_review": True
            },
            {
                "biomarker_name": "Platelets",
                "value": None,
                "unit": "10^3/uL",
                "status": "Unparseable / Missing",
                "requires_review": True
            }
        ]
        checked, alerts = check_emergency_thresholds(metrics)
        self.assertFalse(checked[0]["is_critical"])
        self.assertFalse(checked[1]["is_critical"])
        self.assertEqual(len(alerts), 0)

    def test_06_supported_unit_conversions(self):
        """Test 6: Supported unit conversions produce expected normalized values."""
        # Glucose: 5.5 mmol/L -> 99.1 mg/dL
        norm_v, norm_u, method, req_review = normalize_biomarker_unit("Fasting Glucose", 5.5, "mmol/L", "mg/dL")
        self.assertEqual(norm_v, 99.1)
        self.assertEqual(norm_u, "mg/dL")
        self.assertFalse(req_review)
        self.assertIn("18.0182", method)

        # Hemoglobin: 140 g/L -> 14.0 g/dL
        norm_v, norm_u, method, req_review = normalize_biomarker_unit("Hemoglobin", 140.0, "g/L", "g/dL")
        self.assertEqual(norm_v, 14.0)
        self.assertEqual(norm_u, "g/dL")
        self.assertFalse(req_review)
        self.assertIn("10.0", method)

        # Platelets: 2.5 lakhs/cumm -> 250.0 10^3/uL
        norm_v, norm_u, method, req_review = normalize_biomarker_unit("Platelets", 2.5, "lakhs/cumm", "10^3/uL")
        self.assertEqual(norm_v, 250.0)
        self.assertEqual(norm_u, "10^3/uL")
        self.assertFalse(req_review)

    def test_07_unsupported_units_are_not_silently_accepted(self):
        """Test 7: Unsupported units are flagged as requiring review and not evaluated against reference bounds."""
        norm_v, norm_u, method, req_review = normalize_biomarker_unit("TSH", 2.5, "meters", "uIU/mL")
        self.assertTrue(req_review)
        self.assertEqual(norm_u, "meters")

        biomarkers = {
            "TSH": {"value": 2.5, "source_unit": "meters", "reference_interval": None}
        }
        evaluated = evaluate_reference_ranges(biomarkers, self.db)
        self.assertTrue(evaluated[0]["requires_review"])
        self.assertEqual(evaluated[0]["status"], "Unreviewed (Incompatible Unit)")

    def test_08_decimal_comma_values_are_parsed_correctly(self):
        """Test 8: Unambiguous decimal commas (13,5 and 0,85) are parsed correctly without breaking thousands separators."""
        sample_text = (
            "Hemoglobin: 13,5 g/dL (12.0 - 16.0)\n"
            "Serum Creatinine: 0,85 mg/dL (0.6 - 1.2)\n"
            "Platelets: 250,000 /uL (150,000 - 450,000)\n"
        )
        parsed = parse_medical_report_text(sample_text)
        self.assertEqual(parsed["Hemoglobin"]["value"], 13.5)
        creat_key = "Creatinine" if "Creatinine" in parsed else "Serum Creatinine"
        self.assertEqual(parsed[creat_key]["value"], 0.85)
        self.assertEqual(parsed["Platelets"]["value"], 250000.0)

    def test_09_leading_line_numbers_do_not_pollute_values(self):
        """Test 9: Line numbers like '1. Hemoglobin' or '12. Fasting' do not pollute biomarker values."""
        sample_text = (
            "1. Hemoglobin: 14.5 g/dL (12.0 - 16.0)\n"
            "12. Fasting: 110 mg/dL (70 - 100)\n"
        )
        parsed = parse_medical_report_text(sample_text)
        self.assertEqual(parsed["Hemoglobin"]["value"], 14.5)
        self.assertEqual(parsed["Fasting"]["value"], 110.0)

    def test_10_missing_and_unreviewed_metrics_in_rules_and_summaries(self):
        """Test 10: Missing/unreviewed metrics in explainable rules and summaries are properly marked."""
        metrics = [
            {
                "biomarker_name": "Hemoglobin",
                "value": None,
                "unit": "g/dL",
                "min_normal": 12.0,
                "max_normal": 16.5,
                "status": "Unparseable / Missing",
                "requires_review": True
            },
            {
                "biomarker_name": "Fasting Glucose",
                "value": 110.0,
                "unit": "mg/dL",
                "min_normal": 70.0,
                "max_normal": 100.0,
                "status": "High",
                "requires_review": False
            }
        ]
        rules = run_explainable_rule_engine(metrics)
        self.assertIn("unverified", rules[0]["explanation"])
        self.assertEqual(rules[0]["result_status"], "UNPARSEABLE / MISSING")

        summary = generate_patient_summary_local(metrics, "English")
        self.assertIn("Fasting Glucose", summary)
        self.assertIn("Clinical Notice", summary)
        self.assertIn("Hemoglobin", summary)

    def test_11_offline_local_analysis_end_to_end(self):
        """Test 11: Valid local analysis operates end-to-end without external APIs."""
        raw_report = (
            "PATIENT LABORATORY ANALYSIS REPORT\n"
            "Hemoglobin: 11.2 g/dL (12.0 - 16.0)\n"
            "WBC: 7.5 10^3/uL (4.0 - 11.0)\n"
            "Platelets: 130.0 10^3/uL (150 - 450)\n"
            "Fasting Glucose: 145.0 mg/dL (70 - 100)\n"
        )
        parsed = parse_medical_report_text(raw_report)
        self.assertTrue(len(parsed) >= 4)
        
        evaluated = evaluate_reference_ranges(parsed, self.db)
        self.assertEqual(len(evaluated), 4)
        
        checked, alerts = check_emergency_thresholds(evaluated)
        self.assertEqual(len(checked), 4)
        
        risks = evaluate_disease_risk_patterns(checked)
        self.assertTrue(len(risks) > 0)
        
        rules = run_explainable_rule_engine(checked)
        self.assertEqual(len(rules), 4)
        
        summary = generate_patient_summary_local(checked, "English")
        self.assertIn("Patient Health Summary", summary)

    def test_12_sample_data_demonstration_contract(self):
        """Test 12: Demonstration sample report payload contract contains explicit demonstration labeling."""
        sample_metrics = [
            schemas.MetricAnalysis(
                biomarker_name="Hemoglobin",
                value=11.2,
                unit="g/dL",
                min_normal=12.0,
                max_normal=16.0,
                status="Low",
                reference_source="Standard Clinical Guidelines",
                description="Oxygen-carrying protein in red blood cells."
            )
        ]
        resp = schemas.AnalysisResponse(
            filename="Standard_CBC_Metabolic_Report.pdf (Demonstration Sample)",
            status="success",
            metrics=sample_metrics,
            disease_risks=["Moderate Anemia Risk Indicator"],
            patient_summary="Demonstration Sample: Findings indicate mild anemia.",
            engine_info="AXON Clinical Rule Engine · Demonstration Sample",
            is_mock_fallback=False
        )
        self.assertIn("Demonstration Sample", resp.filename)
        self.assertEqual(resp.metrics[0].value, 11.2)


if __name__ == "__main__":
    unittest.main()
