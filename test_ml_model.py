# -*- coding: utf-8 -*-
"""
AXON Local Machine Learning Test Suite
Verifies trained local ML model weights loading, feature vector construction,
multi-label probability predictions, and offline execution without external APIs.
"""

import os
import sys
import unittest
import numpy as np

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from ml.axon_ml_engine import AxonLocalMLClassifier, FEATURE_NAMES, TARGET_NAMES
from ml.biomarker_ml_predictor import predict_disease_risks_ml, get_ml_classifier

class AXONMLModelTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Verify model weights file exists or trigger train."""
        weights_path = os.path.join(os.path.dirname(__file__), "backend", "ml", "axon_ml_weights.json")
        if not os.path.exists(weights_path):
            from ml.train_ml import main as train_main
            train_main()

    def test_1_ml_model_loading(self):
        """Test trained model weights JSON loading."""
        clf = get_ml_classifier()
        self.assertIsNotNone(clf.weights)
        self.assertEqual(clf.weights.shape, (len(FEATURE_NAMES), len(TARGET_NAMES)))
        print(f"\n[ML Test 1 PASS] Local ML Model loaded with weights matrix shape: {clf.weights.shape}")

    def test_2_prediabetes_ml_prediction(self):
        """Test ML prediction on high glucose and HbA1c input metrics."""
        metrics = [
            {"biomarker_name": "Fasting", "value": 155.0, "unit": "mg/dL"},
            {"biomarker_name": "HbA1c", "value": 6.8, "unit": "%"}
        ]
        risks, details = predict_disease_risks_ml(metrics)
        self.assertTrue(len(risks) > 0)
        diab_detail = next((d for d in details if "Prediabetes" in d["target_label"]), None)
        self.assertIsNotNone(diab_detail)
        self.assertTrue(diab_detail["is_positive"])
        self.assertTrue(diab_detail["probability_percent"] >= 50.0)
        print(f"\n[ML Test 2 PASS] Diabetes Risk ML Confidence Probability: {diab_detail['probability_percent']}%")

    def test_3_dyslipidemia_ml_prediction(self):
        """Test ML prediction on elevated lipid panel metrics."""
        metrics = [
            {"biomarker_name": "Total Cholesterol", "value": 260.0, "unit": "mg/dL"},
            {"biomarker_name": "LDL", "value": 165.0, "unit": "mg/dL"},
            {"biomarker_name": "Triglycerides", "value": 220.0, "unit": "mg/dL"}
        ]
        risks, details = predict_disease_risks_ml(metrics)
        dys_detail = next((d for d in details if "Dyslipidemia" in d["target_label"]), None)
        self.assertIsNotNone(dys_detail)
        self.assertTrue(dys_detail["is_positive"])
        self.assertTrue(dys_detail["probability_percent"] >= 50.0)
        print(f"\n[ML Test 3 PASS] Dyslipidemia ML Confidence Probability: {dys_detail['probability_percent']}%")

    def test_4_anemia_ml_prediction(self):
        """Test ML prediction on low hemoglobin metric."""
        metrics = [
            {"biomarker_name": "Hemoglobin", "value": 9.2, "unit": "g/dL"}
        ]
        risks, details = predict_disease_risks_ml(metrics)
        anemia_detail = next((d for d in details if "Anemia" in d["target_label"]), None)
        self.assertIsNotNone(anemia_detail)
        self.assertTrue(anemia_detail["is_positive"])
        print(f"\n[ML Test 4 PASS] Anemia Risk ML Confidence Probability: {anemia_detail['probability_percent']}%")

    def test_5_normal_baseline_ml_prediction(self):
        """Test ML prediction on completely normal report values."""
        metrics = [
            {"biomarker_name": "Hemoglobin", "value": 14.5, "unit": "g/dL"},
            {"biomarker_name": "Fasting", "value": 85.0, "unit": "mg/dL"},
            {"biomarker_name": "Total Cholesterol", "value": 160.0, "unit": "mg/dL"},
            {"biomarker_name": "TSH", "value": 2.1, "unit": "uIU/mL"}
        ]
        risks, details = predict_disease_risks_ml(metrics)
        positive_count = sum(1 for d in details if d["is_positive"])
        self.assertEqual(positive_count, 0)
        print(f"\n[ML Test 5 PASS] Normal Baseline correctly predicted zero risk flags by trained ML model!")

if __name__ == "__main__":
    unittest.main()
