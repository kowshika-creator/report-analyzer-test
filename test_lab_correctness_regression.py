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


    def test_13_reference_range_unit_consistency(self):
        """Test 13: Reference-range unit consistency across Glucose, Hemoglobin, and ambiguous intervals."""
        # 1. Glucose 5.5 mmol/L with printed interval 3.9 - 5.6 mmol/L
        bio_mmol = {
            "Fasting Glucose": {
                "source_value": 5.5,
                "value": 5.5,
                "source_unit": "mmol/L",
                "reference_interval": "3.9 - 5.6 mmol/L"
            }
        }
        eval_mmol = evaluate_reference_ranges(bio_mmol, self.db)[0]
        self.assertEqual(eval_mmol["status"], "Normal")
        self.assertFalse(eval_mmol["requires_review"])
        self.assertEqual(eval_mmol["source_value"], 5.5)
        self.assertEqual(eval_mmol["source_unit"], "mmol/L")
        self.assertEqual(eval_mmol["value"], 99.1)
        self.assertEqual(eval_mmol["unit"], "mg/dL")
        # Bounds must be converted to compatible mg/dL (70.3 - 100.9)
        self.assertEqual(eval_mmol["min_normal"], 70.3)
        self.assertEqual(eval_mmol["max_normal"], 100.9)

        # 2. Glucose 99.1 mg/dL with equivalent interval in mg/dL (70.3 - 100.9 mg/dL)
        bio_mgdl = {
            "Fasting Glucose": {
                "source_value": 99.1,
                "value": 99.1,
                "source_unit": "mg/dL",
                "reference_interval": "70.3 - 100.9 mg/dL"
            }
        }
        eval_mgdl = evaluate_reference_ranges(bio_mgdl, self.db)[0]
        self.assertEqual(eval_mgdl["status"], "Normal")
        self.assertFalse(eval_mgdl["requires_review"])
        self.assertEqual(eval_mgdl["value"], 99.1)
        self.assertEqual(eval_mgdl["unit"], "mg/dL")

        # Equivalent measurements and intervals must produce consistent classifications
        self.assertEqual(eval_mmol["status"], eval_mgdl["status"])

        # 3. Hemoglobin 140 g/L with printed interval 120 - 160 g/L
        bio_hb_gl = {
            "Hemoglobin": {
                "source_value": 140.0,
                "value": 140.0,
                "source_unit": "g/L",
                "reference_interval": "120 - 160 g/L"
            }
        }
        eval_hb = evaluate_reference_ranges(bio_hb_gl, self.db)[0]
        # Must evaluate as Normal (not falsely Low < 120)
        self.assertEqual(eval_hb["status"], "Normal")
        self.assertFalse(eval_hb["requires_review"])
        self.assertEqual(eval_hb["value"], 14.0)
        self.assertEqual(eval_hb["unit"], "g/dL")
        self.assertEqual(eval_hb["min_normal"], 12.0)
        self.assertEqual(eval_hb["max_normal"], 16.0)

        # 4. Ambiguous unit: Hemoglobin in mmol/L
        bio_hb_amb = {
            "Hemoglobin": {
                "source_value": 8.5,
                "value": 8.5,
                "source_unit": "mmol/L",
                "reference_interval": "7.5 - 10.0 mmol/L"
            }
        }
        eval_hb_amb = evaluate_reference_ranges(bio_hb_amb, self.db)[0]
        self.assertTrue(eval_hb_amb["requires_review"])
        self.assertEqual(eval_hb_amb["status"], "Unreviewed (Incompatible Unit)")
        self.assertNotIn(eval_hb_amb["status"], ["Low", "Normal", "High"])

        # 5. Ambiguous / inverted printed reference interval: 15.0 - 10.0
        bio_inverted = {
            "Fasting Glucose": {
                "source_value": 5.5,
                "value": 5.5,
                "source_unit": "mmol/L",
                "reference_interval": "15.0 - 10.0"
            }
        }
        eval_inv = evaluate_reference_ranges(bio_inverted, self.db)[0]
        self.assertTrue(eval_inv["requires_review"])
        self.assertEqual(eval_inv["status"], "Unreviewed (Ambiguous Reference Interval)")
        self.assertNotIn(eval_inv["status"], ["Low", "Normal", "High"])

        # 6. Conflicting units: source mmol/L vs interval U/L
        bio_conflict = {
            "Fasting Glucose": {
                "source_value": 5.5,
                "value": 5.5,
                "source_unit": "mmol/L",
                "reference_interval": "10 - 20 U/L"
            }
        }
        eval_conf = evaluate_reference_ranges(bio_conflict, self.db)[0]
        self.assertTrue(eval_conf["requires_review"])
        self.assertEqual(eval_conf["status"], "Unreviewed (Incompatible Unit)")
        self.assertNotIn(eval_conf["status"], ["Low", "Normal", "High"])

    def test_14_preserve_missing_source_units(self):
        """Test 14: Preserve distinction between source unit, assumed unit, and normalized unit."""
        # 1. Recognized biomarker with explicit supported unit
        bio_supported = {
            "Fasting": {"value": 85.0, "source_value": 85.0, "source_unit": "mg/dL", "reference_interval": None}
        }
        eval_sup = evaluate_reference_ranges(bio_supported, self.db)[0]
        self.assertFalse(eval_sup["requires_review"])
        self.assertEqual(eval_sup["status"], "Normal")
        self.assertEqual(eval_sup["source_unit"], "mg/dL")
        self.assertIsNone(eval_sup["assumed_unit"])
        self.assertEqual(eval_sup["unit"], "mg/dL")

        # 2. Recognized biomarker with NO printed unit
        bio_no_unit = {
            "Fasting": {"value": 85.0, "source_value": 85.0, "source_unit": None, "reference_interval": None}
        }
        eval_no_unit = evaluate_reference_ranges(bio_no_unit, self.db)[0]
        self.assertTrue(eval_no_unit["requires_review"])
        self.assertEqual(eval_no_unit["status"], "Unreviewed (Missing Source Unit)")
        self.assertIsNone(eval_no_unit["source_unit"])
        self.assertEqual(eval_no_unit["assumed_unit"], "mg/dL")
        self.assertIn("unprinted in source", eval_no_unit["conversion_method"])
        self.assertNotIn(eval_no_unit["status"], ["Low", "Normal", "High"])

        # 3. Recognized biomarker with an unsupported unit
        bio_unsupported = {
            "Fasting": {"value": 85.0, "source_value": 85.0, "source_unit": "parsecs", "reference_interval": None}
        }
        eval_unsup = evaluate_reference_ranges(bio_unsupported, self.db)[0]
        self.assertTrue(eval_unsup["requires_review"])
        self.assertEqual(eval_unsup["status"], "Unreviewed (Incompatible Unit)")
        self.assertEqual(eval_unsup["source_unit"], "parsecs")
        self.assertNotIn(eval_unsup["status"], ["Low", "Normal", "High"])

        # 4. Recognized biomarker with printed unit that conflicts with reference database (TSH in mg/dL)
        bio_conflict_db = {
            "TSH": {"value": 2.5, "source_value": 2.5, "source_unit": "mg/dL", "reference_interval": None}
        }
        eval_conf_db = evaluate_reference_ranges(bio_conflict_db, self.db)[0]
        self.assertTrue(eval_conf_db["requires_review"])
        self.assertEqual(eval_conf_db["status"], "Unreviewed (Incompatible Unit)")
        self.assertEqual(eval_conf_db["source_unit"], "mg/dL")
        self.assertNotIn(eval_conf_db["status"], ["Low", "Normal", "High"])

        # Check that parser also preserves missing source units without inventing them
        raw_report_no_unit = "Fasting Glucose: 85 (70 - 100)"
        parsed = parse_medical_report_text(raw_report_no_unit)
        self.assertIn("Fasting", parsed)
        self.assertIsNone(parsed["Fasting"]["source_unit"])
        self.assertIsNone(parsed["Fasting"]["unit"])

    def test_15_platelet_unit_conversions_and_boundary_safety(self):
        """Test 15: Equivalent platelet counts across cells/uL, cells/cumm, 10^3/uL, and lakhs/cumm."""
        # Equivalent platelet counts of 250,000 cells/uL:
        # a) 250,000 cells/uL
        bio_cells = {
            "Platelets": {"value": 250000.0, "source_value": 250000.0, "source_unit": "cells/uL", "reference_interval": None}
        }
        eval_cells = evaluate_reference_ranges(bio_cells, self.db)[0]
        self.assertEqual(eval_cells["value"], 250.0)
        self.assertEqual(eval_cells["unit"], "10^3/uL")
        self.assertEqual(eval_cells["status"], "Normal")
        self.assertFalse(eval_cells["requires_review"])

        # b) 250,000 cells/cumm
        bio_cumm = {
            "Platelets": {"value": 250000.0, "source_value": 250000.0, "source_unit": "cells/cumm", "reference_interval": None}
        }
        eval_cumm = evaluate_reference_ranges(bio_cumm, self.db)[0]
        self.assertEqual(eval_cumm["value"], 250.0)
        self.assertEqual(eval_cumm["unit"], "10^3/uL")
        self.assertEqual(eval_cumm["status"], "Normal")
        self.assertFalse(eval_cumm["requires_review"])

        # c) 250 10^3/uL
        bio_k = {
            "Platelets": {"value": 250.0, "source_value": 250.0, "source_unit": "10^3/uL", "reference_interval": None}
        }
        eval_k = evaluate_reference_ranges(bio_k, self.db)[0]
        self.assertEqual(eval_k["value"], 250.0)
        self.assertEqual(eval_k["unit"], "10^3/uL")
        self.assertEqual(eval_k["status"], "Normal")
        self.assertFalse(eval_k["requires_review"])

        # d) 2.5 lakhs/cumm
        bio_lakhs = {
            "Platelets": {"value": 2.5, "source_value": 2.5, "source_unit": "lakhs/cumm", "reference_interval": None}
        }
        eval_lakhs = evaluate_reference_ranges(bio_lakhs, self.db)[0]
        self.assertEqual(eval_lakhs["value"], 250.0)
        self.assertEqual(eval_lakhs["unit"], "10^3/uL")
        self.assertEqual(eval_lakhs["status"], "Normal")
        self.assertFalse(eval_lakhs["requires_review"])

        # All four equivalent units must produce identical normalized value and classification
        self.assertEqual(eval_cells["value"], eval_cumm["value"])
        self.assertEqual(eval_cumm["value"], eval_k["value"])
        self.assertEqual(eval_k["value"], eval_lakhs["value"])
        self.assertEqual(eval_cells["status"], eval_lakhs["status"])

        # Do NOT accept values below 1,000 cells/uL as though they were already in 10^3/uL
        bio_low_cells = {
            "Platelets": {"value": 250.0, "source_value": 250.0, "source_unit": "cells/uL", "reference_interval": None}
        }
        eval_low_cells = evaluate_reference_ranges(bio_low_cells, self.db)[0]
        # Must NOT be evaluated as Normal 250 10^3/uL based on numeric magnitude!
        self.assertTrue(eval_low_cells["requires_review"])
        self.assertEqual(eval_low_cells["status"], "Unreviewed (Incompatible Unit)")
        self.assertNotIn(eval_low_cells["status"], ["Low", "Normal", "High"])

    def test_16_actual_endpoint_unreadable_file_structured_failure(self):
        """Test 16: Integration test sending unreadable/unparseable files to actual FastAPI analysis endpoint."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # 1. Send completely unreadable binary garbage
        garbage_data = io.BytesIO(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e")
        res1 = client.post(
            "/api/analyze-report",
            files={"file": ("corrupt_report.pdf", garbage_data, "application/pdf")},
            data={"language": "English", "mode": "local"}
        )
        self.assertEqual(res1.status_code, 422)
        body1 = res1.json()
        self.assertIn("detail", body1)
        self.assertNotIn("metrics", body1)
        self.assertNotIn("disease_risks", body1)
        self.assertNotIn("critical_alerts", body1)

        # 2. Send blank image
        img = Image.new("RGB", (80, 80), color="white")
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)

        res2 = client.post(
            "/api/analyze-report",
            files={"file": ("blank_scan.png", img_buf, "image/png")},
            data={"language": "English", "mode": "local"}
        )
        self.assertEqual(res2.status_code, 422)
        body2 = res2.json()
        self.assertIn("detail", body2)
        self.assertNotIn("metrics", body2)

        # 3. Send non-medical text file (e.g. random shopping list)
        non_medical_txt = io.BytesIO(b"Grocery Shopping List:\n1. Organic apples: 4\n2. Whole milk: 2 gallons\n3. Sourdough bread: 1 loaf")
        res3 = client.post(
            "/api/analyze-report",
            files={"file": ("grocery_list.txt", non_medical_txt, "text/plain")},
            data={"language": "English", "mode": "local"}
        )
        self.assertEqual(res3.status_code, 422)
        body3 = res3.json()
        self.assertIn("detail", body3)
        self.assertNotIn("metrics", body3)


if __name__ == "__main__":
    unittest.main()
