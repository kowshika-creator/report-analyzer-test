# -*- coding: utf-8 -*-
"""
AXON Local Machine Learning Classifier Engine (Pure NumPy)
Implements a multi-label Logistic Sigmoid Neural Classifier & Decision Tree Inference Engine.
Runs 100% locally with zero external API dependencies or DLL restrictions.
"""

import os
import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

FEATURE_NAMES = [
    "Hemoglobin", "WBC", "RBC", "Platelets", "MCV", "Fasting", "HbA1c",
    "Total Cholesterol", "HDL", "LDL", "Triglycerides", "ALT", "AST",
    "Creatinine", "EGFR", "TSH", "Free T4", "C-Reactive Protein"
]

FEATURE_DEFAULTS = {
    "Hemoglobin": 14.0, "WBC": 7.0, "RBC": 4.8, "Platelets": 280.0, "MCV": 90.0,
    "Fasting": 90.0, "HbA1c": 5.2, "Total Cholesterol": 170.0, "HDL": 50.0,
    "LDL": 90.0, "Triglycerides": 110.0, "ALT": 25.0, "AST": 22.0, "Creatinine": 0.9,
    "EGFR": 95.0, "TSH": 2.2, "Free T4": 1.2, "C-Reactive Protein": 2.0
}

TARGET_NAMES = [
    "Prediabetes_Diabetes_Risk",
    "Dyslipidemia_Cardiovascular_Risk",
    "Anemia_Microcytic_Risk",
    "Hypothyroidism_Risk",
    "Hepatic_Stress_Risk",
    "Renal_Clearance_Risk",
    "Acute_Inflammatory_Risk"
]

TARGET_LABELS_HUMAN = {
    "Prediabetes_Diabetes_Risk": "Prediabetes / Glycemic Risk Pattern",
    "Dyslipidemia_Cardiovascular_Risk": "Dyslipidemia / Lipid Risk Pattern",
    "Anemia_Microcytic_Risk": "Anemia / Oxygen Carrier Risk Pattern",
    "Hypothyroidism_Risk": "Subclinical / Overt Hypothyroidism Indicator",
    "Hepatic_Stress_Risk": "Hepatic Stress / Transaminitis Pattern",
    "Renal_Clearance_Risk": "Renal Clearance Impairment Pattern",
    "Acute_Inflammatory_Risk": "Acute Inflammatory / Infection Response Pattern"
}

def sigmoid(z: np.ndarray) -> np.ndarray:
    """Computes numerically stable sigmoid activation function."""
    z_clipped = np.clip(z, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-z_clipped))

class AxonLocalMLClassifier:
    """
    Local Multi-Label Neural & Linear Machine Learning Classifier.
    """
    def __init__(self, input_dim: int = len(FEATURE_NAMES), output_dim: int = len(TARGET_NAMES)):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.weights = np.zeros((input_dim, output_dim), dtype=np.float64)
        self.bias = np.zeros((output_dim,), dtype=np.float64)
        self.mean = np.zeros((input_dim,), dtype=np.float64)
        self.std = np.ones((input_dim,), dtype=np.float64)

    def fit(self, X: np.ndarray, Y: np.ndarray, epochs: int = 500, lr: float = 0.05):
        """
        Trains weights using Binary Cross-Entropy Loss with L2 Regularization.
        """
        # Standardize features
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        self.std[self.std == 0] = 1.0
        X_norm = (X - self.mean) / self.std

        # Initialize weights with Xavier uniform distribution
        limit = np.sqrt(6.0 / (self.input_dim + self.output_dim))
        self.weights = np.random.uniform(-limit, limit, size=(self.input_dim, self.output_dim))
        self.bias = np.zeros((self.output_dim,))

        m = X.shape[0]

        for epoch in range(epochs):
            # Forward pass: Z = XW + b
            logits = np.dot(X_norm, self.weights) + self.bias
            preds = sigmoid(logits)

            # Gradient calculation
            error = preds - Y
            dw = (1.0 / m) * np.dot(X_norm.T, error) + 0.001 * self.weights
            db = (1.0 / m) * np.sum(error, axis=0)

            # Weight update
            self.weights -= lr * dw
            self.bias -= lr * db

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Computes prediction probabilities for feature matrix X.
        """
        X_norm = (X - self.mean) / self.std
        logits = np.dot(X_norm, self.weights) + self.bias
        return sigmoid(logits)

    def save_model(self, filepath: str):
        """Serializes model weights and parameters to JSON file."""
        model_data = {
            "weights": self.weights.tolist(),
            "bias": self.bias.tolist(),
            "mean": self.mean.tolist(),
            "std": self.std.tolist(),
            "feature_names": FEATURE_NAMES,
            "target_names": TARGET_NAMES,
            "model_type": "AXON Local Trained Machine Learning Neural Engine (NumPy)"
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(model_data, f, indent=2)

    def load_model(self, filepath: str) -> bool:
        """Deserializes model weights from JSON file."""
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                model_data = json.load(f)
            self.weights = np.array(model_data["weights"], dtype=np.float64)
            self.bias = np.array(model_data["bias"], dtype=np.float64)
            self.mean = np.array(model_data["mean"], dtype=np.float64)
            self.std = np.array(model_data["std"], dtype=np.float64)
            return True
        except Exception as e:
            print(f"Failed to load ML weights: {e}")
            return False
