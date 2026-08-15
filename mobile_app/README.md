# AXON Medical Report Analyzer - Mobile Application (React Native / Expo)

This is the mobile client application for the **AI Lab Report Analyzer + Multi-Biomarker Disease Risk Predictor + Multilingual Medical Chatbot**.

---

## Features
- **Camera Document Scan**: Capture physical lab report papers directly using your phone's camera.
- **Device File Selector**: Select PDF reports or lab result images from your device gallery.
- **Dynamic Parameter Card Deck**: Displays real blood test values alongside normal reference bounds with color-coded status badges (`Low`, `Normal`, `High`).
- **Holistic Disease Risk Predictor**: Displays combined multi-metric disease risks (Prediabetes, Dyslipidemia, Hypothyroidism, Anemia, Hepatic/Renal stress).
- **Multilingual Patient Report Simplifier**: Summarizes results in simple terms in English, Tamil, Hindi, Telugu.
- **Context-Aware Medical Chatbot**: Ask questions directly about report values with 4 tone settings (*Empathetic, Clinical, Educational, Family*).

---

## Getting Started

### 1. Prerequisites
- Node.js LTS installed.
- Expo Go app on your Android/iOS phone (or an Android emulator).

### 2. Running Locally
1. Navigate to the `mobile_app` folder:
   ```bash
   cd mobile_app
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Expo development server:
   ```bash
   npx expo start
   ```
4. Scan the generated QR code with your Expo Go app or press `a` to launch in an Android Emulator.

> **Note for Android Emulator**: The app connects to the FastAPI backend at `http://10.0.2.2:8000`. If testing on a physical phone over local Wi-Fi, update `API_HOST` in `App.js` to your computer's LAN IP (e.g. `http://192.168.1.5:8000`).

---

## How to Build Standalone Android APK

To generate a downloadable `.apk` file for Android devices:

1. Install EAS CLI globally:
   ```bash
   npm install -g eas-cli
   ```
2. Log in or create a free Expo account:
   ```bash
   eas login
   ```
3. Initialize EAS configuration:
   ```bash
   eas build:configure
   ```
4. Build the standalone APK file:
   ```bash
   eas build -p android --profile preview
   ```
5. Once complete, download the `.apk` link provided by EAS Build and install it on any Android smartphone!
