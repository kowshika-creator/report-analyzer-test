# AXON: AI Medical Report Analyzer + Disease Risk Predictor + Patient Simplifier

An end-to-end medical laboratory report decoder powered by **Python FastAPI**, **Next.js Web Dashboard**, **React Native / Expo Mobile App**, and **Google Gemini 1.5 Multimodal AI**.

---

## 🌟 Key Features

1. **Multi-Format Document Ingestion & PII Scrubbing**:
   - Upload PDF lab reports or photograph paper documents using a web/mobile camera.
   - Automatically scrubs Patient Identifiable Information (PII) before processing.
2. **Clinical Parameter Database & Reference Range Comparator**:
   - Matches extracted test metrics against standard clinical bounds across 6 core panels (**CBC, Blood Sugar, Lipid Profile, LFT, KFT, Thyroid Profile**).
   - Dynamically parses lab-custom reference intervals printed on physical report papers.
3. **Multi-Biomarker Disease Risk Predictor**:
   - Cross-analyzes interrelated parameters together: Prediabetes, Dyslipidemia/Cardiovascular risk, Subclinical Hypothyroidism, Mild Anemia, Hepatic Stress, Renal Stress, and Acute Inflammatory/Infectious patterns.
4. **Multilingual Patient Report Simplifier**:
   - Translates complex clinical jargon into empathetic explanations in **English, Tamil, Hindi, Telugu, Spanish, French, German**.
5. **Context-Aware Multilingual Medical Chatbot (`/api/chat`)**:
   - Answers questions comparing **real value vs. normal range** directly, with 4 tone settings (*Empathetic, Clinical, Educational, Family Mode*).

---

## 📁 Repository Structure

```
Medical report analyzer/
├── backend/            # Python FastAPI, SQLite DB, Gemini AI Engine & Chatbot Router
├── frontend/           # Next.js Web Dashboard, SVG Trend Charts & Web Camera Scanner
├── mobile_app/         # React Native Expo Mobile Client (Camera Scan & Android APK Config)
├── start_servers.bat   # Automatic local dev environment launcher
└── run_integration_test.py # Comprehensive backend integration test suite
```

---

## 🚀 Quick Start (Local Setup)

Simply run the automatic launcher script:
```cmd
start_servers.bat
```
- **Backend API Server**: `http://127.0.0.1:8000`
- **Frontend Web Dashboard**: `http://localhost:3000`

---

## 🌐 Production Deployment Guide

### 1. Deploy Frontend Web Dashboard on Vercel
1. Push your repository to **GitHub**.
2. Go to [Vercel Dashboard](https://vercel.com/new) and click **"Add New Project"**.
3. Select your repository and set **Root Directory** to `frontend`.
4. Add Environment Variable:
   ```env
   NEXT_PUBLIC_API_URL=https://your-fastapi-backend-url.com
   ```
5. Click **Deploy**. Vercel will build and assign an HTTPS domain (e.g. `axon-medical.vercel.app`).

---

### 2. Deploy Backend API on Render / Railway
1. Create a Web Service on [Render](https://render.com) or [Railway](https://railway.app).
2. Set Root Directory to `backend`.
3. Set Build Command: `pip install -r requirements.txt && python init_db.py`
4. Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configure Environment Variables:
   - `GEMINI_API_KEY`: Your Google Gemini API Key

---

### 3. Build Standalone Android `.apk` (Mobile App)
Navigate to the `mobile_app` folder and use Expo EAS Build:
```bash
cd mobile_app
npm install
npm install -g eas-cli
eas login
eas build -p android --profile preview
```
Download the resulting `.apk` file and install on any Android phone!
