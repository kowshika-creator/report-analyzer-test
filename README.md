# AXON – Local-First AI & ML Medical Report Analysis System

AXON is an intelligent, **local-first** medical laboratory and radiology report analysis platform. It processes blood test metrics, dynamic reference intervals, disease risk patterns, and radiology imaging scans **100% locally on your machine** using a **trained local Machine Learning Classifier (`backend/ml/`)** without requiring external cloud AI APIs or internet access.

> 🔒 **Privacy & Safety Disclaimer**: AXON provides informational analysis, ML probability scores, and clinical rule explanations for educational purposes. It does NOT make definitive medical diagnoses or replace a licensed physician. For emergency or critical values, seek prompt medical attention according to your healthcare provider's advice.

---

## 🏗️ Architecture Overview

```
User
  │
  ▼
AXON UI (Next.js Dashboard / React Native Mobile)
  │
  ▼
Local Processing Layer (Python Standalone Core & ML Modules)
  ├── 1. Local OCR Engine (PyPDF / Tesseract / EasyOCR / Local Text Parser)
  ├── 2. Local Medical Parser (CBC, Blood Sugar, Lipid, LFT, KFT, Thyroid)
  ├── 3. Reference Range Engine (Report Bounds / SQLite Reference DB / Standard Guidelines)
  ├── 4. Trained Local Machine Learning Predictor (Multi-Label Neural/Linear Classifier - 88-99% Acc)
  │      └── Predicts ML Probability Confidence Scores (0-100%) for 7 Clinical Patterns
  ├── 5. Emergency Panic Alert Engine (Life-Safety Threshold Monitor)
  ├── 6. Explainable Clinical Rule Engine (Rule IDs: R-CBC-001, Diagnostic Rationale)
  ├── 7. Patient Simplifier (Template-based Multilingual Explanations: EN, TA, HI, TE, ES, FR, DE)
  ├── 8. Longitudinal Trend Analysis (Delta & Percentage Tracking)
  └── 9. Local PDF Exporter (ReportLab Summary Generator)

Optional (Cloud AI Enhancement):
  └─► Google Gemini API (Only invoked if user configures key and selects Cloud AI Mode)
```

---

## 🤖 Trained Local Machine Learning Model (`backend/ml/`)

AXON features a **dedicated, trained local Machine Learning model** built using NumPy vectorization and logistic sigmoid optimization:

- **Training Script**: `backend/ml/train_ml.py`
- **Model Classifier**: `backend/ml/axon_ml_engine.py` (`AxonLocalMLClassifier`)
- **Serialized Model Weights**: `backend/ml/axon_ml_weights.json`
- **Inference Predictor**: `backend/ml/biomarker_ml_predictor.py`
- **Training Dataset**: 5,000 synthetic clinical lab biomarker samples across 18 feature parameters.
- **Model Test Evaluation Metrics**:
  - `Prediabetes / Glycemic Risk Pattern`: **88.20% Test Accuracy**
  - `Dyslipidemia / Lipid Risk Pattern`: **95.20% Test Accuracy**
  - `Anemia / Oxygen Carrier Risk Pattern`: **99.20% Test Accuracy**
  - `Subclinical / Overt Hypothyroidism`: **98.40% Test Accuracy**
  - `Hepatic Stress / Transaminitis Pattern`: **98.50% Test Accuracy**
  - `Renal Clearance Impairment Pattern`: **95.90% Test Accuracy**
  - `Acute Inflammatory Response Pattern`: **96.40% Test Accuracy**

---

## 🌟 Core Local Features

1. **Local Document Ingestion & PII Scrubbing**:
   - Accepts PDF reports, physical document photos, web/mobile camera scans, and plain text files.
   - Automatically redacts SSNs, Aadhaar numbers, phone numbers, emails, addresses, patient names, and physician names before processing.
2. **Local Deterministic Medical Parser (`backend/core/medical_parser.py`)**:
   - Parses metrics, floating-point values, measurement units, printed reference intervals, and confidence scores across 6 core panels (**CBC, Blood Sugar, Lipid Profile, LFT, KFT, Thyroid Profile**).
   - Allows unknown or custom laboratory tests to be parsed and displayed.
3. **Local Reference Range Engine (`backend/core/reference_engine.py`)**:
   - Evaluates metrics in priority order: (1) Printed report bounds, (2) Local SQLite database (`ReferenceRange`), (3) Standard clinical guidelines.
   - Explicitly displays reference source tags (`Lab Report`, `AXON Local Database`, `Standard Clinical Guidelines`) in the UI.
4. **Trained Local Machine Learning Predictor (`backend/ml/biomarker_ml_predictor.py`)**:
   - Runs inference on parsed biomarker features and outputs exact **ML Probability Confidence Percentages (0-100%)** for disease risk patterns.
5. **AXON Explainable Clinical Rule Engine (`backend/core/rule_engine.py`)**:
   - Generates transparent rule evaluation IDs (e.g. `R-CBC-001`, `R-GLU-002`), input values, reference bounds, result status, explanation rationale, and suggested doctor discussion points.
6. **Local Emergency Panic Threshold Monitor (`backend/core/emergency_engine.py`)**:
   - Scans values against critical panic thresholds (Platelets `< 20`, Hemoglobin `< 6.5`, Fasting Glucose `> 300` or `< 40`, Potassium `< 2.5` or `> 6.5`, Creatinine `> 5.0`, ALT/AST `> 1000`, TSH `> 50`).
7. **Local Multilingual Patient Simplifier (`backend/core/patient_simplifier.py`)**:
   - Generates empathetic patient summaries in 7 languages (**English, Tamil, Hindi, Telugu, Spanish, French, German**) without translation APIs.
8. **Local Knowledge-Base Chatbot (`backend/core/local_chatbot.py`)**:
   - Answers patient queries across 4 tone settings (*Empathetic, Clinical, Educational, Family Mode*) using local report data, biomarker definitions, and medical knowledge base JSON.

---

## 📁 Repository Structure & Local Core Modules

```
Medical report analyzer/
├── backend/
│   ├── ml/                          # Trained Local Machine Learning Engine
│   │   ├── axon_ml_engine.py        # Multi-Label Neural/Linear ML Classifier
│   │   ├── train_ml.py              # ML Training Pipeline Script
│   │   ├── axon_ml_weights.json     # Trained Model Weights & Scaling Parameters
│   │   └── biomarker_ml_predictor.py# Local ML Inference & Probability Service
│   ├── core/                        # Local Core Processing Modules
│   │   ├── local_ocr.py             # Preprocessing & Multi-Engine Local OCR
│   │   ├── medical_parser.py        # Regex & Pattern Medical Report Parser
│   │   ├── reference_engine.py      # Reference Bounds & Source Tagging
│   │   ├── emergency_engine.py      # Critical Panic Threshold Monitor
│   │   ├── risk_engine.py           # ML & Rule-Based Disease Risk Patterns
│   │   ├── rule_engine.py           # AXON Explainable Clinical Rule Engine
│   │   ├── patient_simplifier.py    # Template Multilingual Patient Simplifier
│   │   ├── trend_engine.py          # Longitudinal Trend & Delta Analysis
│   │   ├── radiology_preprocessor.py# Local Radiology Technical Preprocessor
│   │   └── local_chatbot.py         # Local Medical Knowledge Base Chatbot
│   ├── main.py                      # FastAPI REST API wrapper
│   ├── chat_router.py               # Chatbot route
│   └── pdf_exporter.py              # ReportLab Offline PDF Exporter
├── frontend/                        # Next.js Web Dashboard & Camera Scanner
├── mobile_app/                      # React Native Expo Mobile Client
├── demo_data/                       # Sample offline datasets (CBC, Lipid, Diabetes, Thyroid)
├── test_ml_model.py                 # Trained ML Model Verification Suite (5 tests)
├── test_offline_mode.py             # 100% Offline Automated Test Suite (11 tests)
├── test_axon_matrix.py              # 370-Case Enterprise Validation Suite
└── start_servers.bat                # One-click local environment launcher
```

---

## 🚀 Quick Start & Testing Commands

### 1. Re-Train Local Machine Learning Model
```bash
python backend/ml/train_ml.py
```

### 2. Verify Trained Local ML Model Predictions
```bash
python test_ml_model.py
```
Outputs:
```
Ran 5 tests in 0.003s - OK
[ML Test 1 PASS] Local ML Model loaded with weights matrix shape: (18, 7)
[ML Test 2 PASS] Diabetes Risk ML Confidence Probability: 99.9%
[ML Test 3 PASS] Dyslipidemia ML Confidence Probability: 99.8%
[ML Test 4 PASS] Anemia Risk ML Confidence Probability: 98.2%
[ML Test 5 PASS] Normal Baseline correctly predicted zero risk flags by trained ML model!
```

### 3. Run Complete 100% Offline Test Suite
```bash
python test_offline_mode.py
```

### 4. Automatic Dev Server Launcher
```cmd
start_servers.bat
```
- **Backend Server**: `http://127.0.0.1:8000`
- **Web Dashboard**: `http://localhost:3000`
