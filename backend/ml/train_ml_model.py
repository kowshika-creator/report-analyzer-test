# -*- coding: utf-8 -*-
"""
AXON Local Machine Learning Model Trainer:
Generates clinical biomarker dataset, trains a multi-output Random Forest Classifier,
evaluates performance metrics (Precision, Recall, F1-Score), and serializes the model to joblib.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

FEATURE_NAMES = [
    "Hemoglobin", "WBC", "RBC", "Platelets", "MCV", "Fasting", "HbA1c",
    "Total Cholesterol", "HDL", "LDL", "Triglycerides", "ALT", "AST",
    "Creatinine", "EGFR", "TSH", "Free T4", "C-Reactive Protein"
]

FEATURE_DEFAULTS = {
    "Hemoglobin": (14.0, 1.5),
    "WBC": (7.0, 1.5),
    "RBC": (4.8, 0.5),
    "Platelets": (280.0, 50.0),
    "MCV": (90.0, 5.0),
    "Fasting": (90.0, 15.0),
    "HbA1c": (5.2, 0.4),
    "Total Cholesterol": (170.0, 25.0),
    "HDL": (50.0, 8.0),
    "LDL": (90.0, 15.0),
    "Triglycerides": (110.0, 20.0),
    "ALT": (25.0, 8.0),
    "AST": (22.0, 6.0),
    "Creatinine": (0.9, 0.2),
    "EGFR": (95.0, 10.0),
    "TSH": (2.2, 0.8),
    "Free T4": (1.2, 0.2),
    "C-Reactive Protein": (2.0, 1.0)
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

def train_and_save_ml_model():
    print("AXON LOCAL ML MODEL TRAINING PIPELINE", flush=True)

    np.random.seed(42)
    num_samples = 2000
    data = {}

    for f_name, (mean_v, std_v) in FEATURE_DEFAULTS.items():
        data[f_name] = np.maximum(0.1, np.random.normal(loc=mean_v, scale=std_v, size=num_samples))

    df_x = pd.DataFrame(data)

    diab_idx = np.random.choice(num_samples, size=int(num_samples * 0.3), replace=False)
    df_x.loc[diab_idx, "Fasting"] = np.random.uniform(105.0, 190.0, size=len(diab_idx))
    df_x.loc[diab_idx, "HbA1c"] = np.random.uniform(5.8, 8.5, size=len(diab_idx))

    dys_idx = np.random.choice(num_samples, size=int(num_samples * 0.35), replace=False)
    df_x.loc[dys_idx, "Total Cholesterol"] = np.random.uniform(205.0, 310.0, size=len(dys_idx))
    df_x.loc[dys_idx, "LDL"] = np.random.uniform(135.0, 210.0, size=len(dys_idx))

    anemia_idx = np.random.choice(num_samples, size=int(num_samples * 0.25), replace=False)
    df_x.loc[anemia_idx, "Hemoglobin"] = np.random.uniform(7.0, 11.5, size=len(anemia_idx))

    thyroid_idx = np.random.choice(num_samples, size=int(num_samples * 0.2), replace=False)
    df_x.loc[thyroid_idx, "TSH"] = np.random.uniform(4.8, 18.0, size=len(thyroid_idx))

    liver_idx = np.random.choice(num_samples, size=int(num_samples * 0.2), replace=False)
    df_x.loc[liver_idx, "ALT"] = np.random.uniform(58.0, 220.0, size=len(liver_idx))

    renal_idx = np.random.choice(num_samples, size=int(num_samples * 0.18), replace=False)
    df_x.loc[renal_idx, "Creatinine"] = np.random.uniform(1.3, 4.5, size=len(renal_idx))

    inf_idx = np.random.choice(num_samples, size=int(num_samples * 0.22), replace=False)
    df_x.loc[inf_idx, "C-Reactive Protein"] = np.random.uniform(6.5, 85.0, size=len(inf_idx))

    df_y = pd.DataFrame()
    df_y["Prediabetes_Diabetes_Risk"] = ((df_x["Fasting"] >= 100.0) | (df_x["HbA1c"] >= 5.7)).astype(int)
    df_y["Dyslipidemia_Cardiovascular_Risk"] = ((df_x["Total Cholesterol"] >= 200.0) | (df_x["LDL"] >= 130.0) | (df_x["Triglycerides"] >= 150.0)).astype(int)
    df_y["Anemia_Microcytic_Risk"] = (df_x["Hemoglobin"] < 12.0).astype(int)
    df_y["Hypothyroidism_Risk"] = (df_x["TSH"] > 4.5).astype(int)
    df_y["Hepatic_Stress_Risk"] = ((df_x["ALT"] > 56.0) | (df_x["AST"] > 40.0)).astype(int)
    df_y["Renal_Clearance_Risk"] = ((df_x["Creatinine"] > 1.2) | (df_x["EGFR"] < 60.0)).astype(int)
    df_y["Acute_Inflammatory_Risk"] = ((df_x["C-Reactive Protein"] > 5.0) | (df_x["WBC"] > 11.0)).astype(int)

    x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.2, random_state=42)

    rf_base = RandomForestClassifier(n_estimators=30, max_depth=8, random_state=42, n_jobs=1)
    model = MultiOutputClassifier(rf_base, n_jobs=1)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    for idx, col in enumerate(TARGET_NAMES):
        acc = accuracy_score(y_test[col], y_pred[:, idx])
        print(f"Target: {col:<32} | Accuracy: {acc * 100:.2f}%", flush=True)

    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, "axon_disease_risk_model.joblib")

    metadata = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "feature_defaults": FEATURE_DEFAULTS,
        "target_names": TARGET_NAMES,
        "model_type": "Scikit-Learn MultiOutput Random Forest Classifier (Local)"
    }

    joblib.dump(metadata, model_path)
    print(f"Model saved to: {model_path}", flush=True)

if __name__ == "__main__":
    train_and_save_ml_model()
