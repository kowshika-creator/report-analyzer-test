# AXON Medical Report Analyzer - Frontend Web Dashboard

This is the Next.js frontend web dashboard for the **AI Lab Report Analyzer + Multi-Biomarker Disease Risk Predictor + Multilingual Medical Chatbot**.

---

## Getting Started

### 1. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to view the application.

---

## Deploying on Vercel (Step-by-Step Guide)

Vercel is the official zero-configuration platform built by the creators of Next.js for instant production deployment.

### Step 1: Set Environment Variables
Before deploying, ensure you configure the URL of your live Python FastAPI backend:

1. Create a `.env.production` file or set environment variables in your Vercel Project Settings:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-api.onrender.com
   ```

---

### Step 2: Deploy via Vercel Dashboard (Recommended)

1. Push your project code to **GitHub**, **GitLab**, or **Bitbucket**.
2. Go to [Vercel Dashboard](https://vercel.com/new) and log in.
3. Click **"Add New"** $\to$ **"Project"** and import your Git repository.
4. Set the **Root Directory** to `frontend` (if deploying from a monorepo structure).
5. In **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL` = `https://your-fastapi-backend.com`
6. Click **Deploy**. Vercel will automatically build and assign a free production domain with HTTPS (e.g., `axon-medical-analyzer.vercel.app`).

---

### Step 3: Deploy via Vercel CLI

Alternatively, you can deploy directly from your terminal using the Vercel CLI:

1. Install the Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```
2. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
3. Run the initial deployment command:
   ```bash
   vercel
   ```
4. Follow the interactive prompts, then deploy to production:
   ```bash
   vercel --prod
   ```

---

## Useful Links

- [Next.js Deployment Documentation](https://nextjs.org/docs/app/building-your-application/deploying)
- [Vercel Project Settings & Environment Variables](https://vercel.com/docs/projects/environment-variables)
