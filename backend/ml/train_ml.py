# -*- coding: utf-8 -*-
"""
AXON Local Machine Learning Model Trainer Script (Pure NumPy Engine)
Trains the multi-label Machine Learning model on 5,000 clinical samples and saves weights artifact.
"""

import os
import sys
import numpy as np
import pandas as pd

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml.axon_ml_engine import (
    AxonLocalMLClassifier,
    FEATURE_NAMES,
    FEATURE_DEFAULTS,
    TARGET_NAMES
)

def generate_training_data(num_samples: int = 5000, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]: # type: ignore
    """
    Generates synthetic clinical dataset for training local ML classifier.
    """
    np.random.seed(seed)
    X = np.zeros((num_samples, len(FEATURE_NAMES)))

    for i, f_name in enumerate(FEATURE_NAMES):
        mean_val = FEATURE_DEFAULTS.get(f_name, 10.0)
        std_val = mean_val * 0.15
        X[:, i] = np.maximum(0.1, np.random.normal(loc=mean_val, scale=std_val, size=num_samples))

    # Induce specific clinical conditions in subset of data
    # 1. Prediabetes / Diabetes
    d_idx = np.random.choice(num_samples, size=int(num_samples * 0.3), replace=False)
    X[d_idx, FEATURE_NAMES.index("Fasting")] = np.random.uniform(105.0, 195.0, size=len(d_idx))
    X[d_idx, FEATURE_NAMES.index("HbA1c")] = np.random.uniform(5.8, 8.8, size=len(d_idx))

    # 2. Dyslipidemia
    l_idx = np.random.choice(num_samples, size=int(num_samples * 0.35), replace=False)
    X[l_idx, FEATURE_NAMES.index("Total Cholesterol")] = np.random.uniform(205.0, 310.0, size=len(l_idx))
    X[l_idx, FEATURE_NAMES.index("LDL")] = np.random.uniform(135.0, 210.0, size=len(l_idx))

    # 3. Anemia
    a_idx = np.random.choice(num_samples, size=int(num_samples * 0.25), replace=False)
    X[a_idx, FEATURE_NAMES.index("Hemoglobin")] = np.random.uniform(7.0, 11.5, size=len(a_idx))

    # 4. Hypothyroidism
    t_idx = np.random.choice(num_samples, size=int(num_samples * 0.2), replace=False)
    X[t_idx, FEATURE_NAMES.index("TSH")] = np.random.uniform(4.8, 18.0, size=len(t_idx))

    # 5. Hepatic Stress
    h_idx = np.random.choice(num_samples, size=int(num_samples * 0.2), replace=False)
    X[h_idx, FEATURE_NAMES.index("ALT")] = np.random.uniform(58.0, 220.0, size=len(h_idx))

    # 6. Renal Clearance
    r_idx = np.random.choice(num_samples, size=int(num_samples * 0.18), replace=False)
    X[r_idx, FEATURE_NAMES.index("Creatinine")] = np.random.uniform(1.3, 4.5, size=len(r_idx))

    # 7. Acute Inflammation
    i_idx = np.random.choice(num_samples, size=int(num_samples * 0.22), replace=False)
    X[i_idx, FEATURE_NAMES.index("C-Reactive Protein")] = np.random.uniform(6.5, 85.0, size=len(i_idx))

    # Compute binary target labels matrix Y
    Y = np.zeros((num_samples, len(TARGET_NAMES)))
    Y[:, 0] = ((X[:, FEATURE_NAMES.index("Fasting")] >= 100.0) | (X[:, FEATURE_NAMES.index("HbA1c")] >= 5.7)).astype(int)
    Y[:, 1] = ((X[:, FEATURE_NAMES.index("Total Cholesterol")] >= 200.0) | (X[:, FEATURE_NAMES.index("LDL")] >= 130.0) | (X[:, FEATURE_NAMES.index("Triglycerides")] >= 150.0)).astype(int)
    Y[:, 2] = (X[:, FEATURE_NAMES.index("Hemoglobin")] < 12.0).astype(int)
    Y[:, 3] = (X[:, FEATURE_NAMES.index("TSH")] > 4.5).astype(int)
    Y[:, 4] = ((X[:, FEATURE_NAMES.index("ALT")] > 56.0) | (X[:, FEATURE_NAMES.index("AST")] > 40.0)).astype(int)
    Y[:, 5] = ((X[:, FEATURE_NAMES.index("Creatinine")] > 1.2) | (X[:, FEATURE_NAMES.index("EGFR")] < 60.0)).astype(int)
    Y[:, 6] = ((X[:, FEATURE_NAMES.index("C-Reactive Protein")] > 5.0) | (X[:, FEATURE_NAMES.index("WBC")] > 11.0)).astype(int)

    return X, Y

def main():
    print("=" * 60, flush=True)
    print("TRAINING AXON LOCAL MACHINE LEARNING CLASSIFIER MODEL", flush=True)
    print("=" * 60, flush=True)

    X, Y = generate_training_data(num_samples=5000, seed=42)
    print(f"Generated {X.shape[0]} training samples across {X.shape[1]} clinical features.", flush=True)

    split = int(0.8 * X.shape[0])
    x_train, x_test = X[:split], X[split:]
    y_train, y_test = Y[:split], Y[split:]

    clf = AxonLocalMLClassifier()
    print("Training ML Neural Classifier weights via gradient optimization...", flush=True)
    clf.fit(x_train, y_train, epochs=800, lr=0.08)

    # Evaluate model
    probs = clf.predict_proba(x_test)
    preds = (probs >= 0.5).astype(int)

    print("\nLocal ML Classifier Test Evaluation:", flush=True)
    for i, t_name in enumerate(TARGET_NAMES):
        acc = np.mean(preds[:, i] == y_test[:, i]) * 100.0
        print(f"  - Target: {t_name:<35} | Test Accuracy: {acc:.2f}%", flush=True)

    model_path = os.path.join(os.path.dirname(__file__), "axon_ml_weights.json")
    clf.save_model(model_path)
    print("\n" + "=" * 60, flush=True)
    print(f"SUCCESS: Trained Local ML Model Weights saved to:\n  -> {model_path}", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    main()
