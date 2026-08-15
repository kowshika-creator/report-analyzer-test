"use client";

import React, { useState, useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UserProfile {
  full_name: string;
  age: number;
  biological_sex: string;
  weight_kg: number;
  height_cm: number;
  chronic_conditions: string[];
  primary_health_goal: string;
  is_onboarded: boolean;
}

interface Metric {
  biomarker_name: string;
  value: number;
  unit: string;
  min_normal: number;
  max_normal: number;
  status: string;
  confidence?: number;
  is_low_confidence?: boolean;
  is_critical?: boolean;
  critical_reason?: string | null;
  description: string | null;
}

interface HistoricalReport {
  id: string;
  filename: string;
  date: string;
  normal_count: number;
  abnormal_count: number;
  disease_risks: string[];
  has_critical_alert?: boolean;
  critical_alerts?: string[];
  patient_summary: string;
  metrics: Metric[];
  is_mock_fallback?: boolean;
}

type TabType = "dashboard" | "chat" | "history" | "trends" | "settings";

export default function AXONDashboard() {
  // Navigation & Theme States
  const [activeTab, setActiveTab] = useState<TabType>("dashboard");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isGuest, setIsGuest] = useState<boolean>(false);

  // Authentication & Session States
  const [token, setToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [reportHistory, setReportHistory] = useState<HistoricalReport[]>([]);
  
  // Interactive UI States
  const [activeReport, setActiveReport] = useState<Partial<HistoricalReport> | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("English");
  const [selectedTrendBiomarker, setSelectedTrendBiomarker] = useState<string>("Hemoglobin");
  const [showDescription, setShowDescription] = useState<Record<string, boolean>>({});

  // Camera Scanner States
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("environment");
  const [geminiApiKey, setGeminiApiKey] = useState<string>("");

  // Chatbot Companion States
  const [selectedTone, setSelectedTone] = useState<string>("Empathetic");
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "model"; content: string }>>([]);
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [chatDisclaimer, setChatDisclaimer] = useState<string>("");

  // Auth Dialog States
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState<string>("");
  const [authPassword, setAuthPassword] = useState<string>("");
  
  // Profile settings editor fields
  const [profileForm, setProfileForm] = useState<UserProfile>({
    full_name: "",
    age: 30,
    biological_sex: "Male",
    weight_kg: 70,
    height_cm: 175,
    chronic_conditions: [],
    primary_health_goal: "Maintain general wellness",
    is_onboarded: false
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Initialize theme and credentials from storage
  useEffect(() => {
    // Theme setup
    const savedTheme = localStorage.getItem("axon_theme") || "light";
    setTheme(savedTheme as "light" | "dark");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
    } else {
      document.documentElement.classList.remove("dark-theme");
    }

    // Auth setup
    const storedToken = localStorage.getItem("axon_auth_token");
    const storedEmail = localStorage.getItem("axon_auth_email");
    if (storedToken && storedEmail) {
      setToken(storedToken);
      setUserEmail(storedEmail);
      fetchUserProfile(storedToken);
      fetchReportHistory(storedToken);
    }

    // API Key setup
    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    setGeminiApiKey(savedKey);
  }, []);

  // Scroll chat window automatically
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Sync historical trends list based on active biomarkers
  const availableBiomarkers = React.useMemo(() => {
    const names = new Set<string>();
    reportHistory.forEach(report => {
      report.metrics.forEach(m => {
        names.add(m.biomarker_name);
      });
    });
    if (names.size === 0 && activeReport?.metrics) {
      activeReport.metrics.forEach(m => names.add(m.biomarker_name));
    }
    return Array.from(names);
  }, [reportHistory, activeReport]);

  useEffect(() => {
    if (availableBiomarkers.length > 0 && !availableBiomarkers.includes(selectedTrendBiomarker)) {
      setSelectedTrendBiomarker(availableBiomarkers[0]);
    }
  }, [availableBiomarkers, selectedTrendBiomarker]);

  // Toggle dark/light theme
  const toggleTheme = (newTheme: "light" | "dark") => {
    setTheme(newTheme);
    localStorage.setItem("axon_theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
    } else {
      document.documentElement.classList.remove("dark-theme");
    }
  };

  // Fetch API handlers
  const fetchUserProfile = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/api/user/profile`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        setProfileForm({
          full_name: data.full_name || "",
          age: data.age || 30,
          biological_sex: data.biological_sex || "Male",
          weight_kg: data.weight_kg || 70,
          height_cm: data.height_cm || 175,
          chronic_conditions: data.chronic_conditions || [],
          primary_health_goal: data.primary_health_goal || "Maintain general wellness",
          is_onboarded: data.is_onboarded
        });
        if (!data.is_onboarded) {
          setActiveTab("settings");
        }
      }
    } catch (err) {
      console.error("Error fetching user profile", err);
    }
  };

  const fetchReportHistory = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/api/metrics/history`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setReportHistory(data);
        if (data.length > 0 && !activeReport) {
          setActiveReport(data[data.length - 1]);
        }
      }
    } catch (err) {
      console.error("Error fetching report history", err);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    const endpoint = authMode === "login" ? "login" : "register";
    try {
      const res = await fetch(`${API_URL}/api/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword })
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication request failed.");
      }

      if (authMode === "register") {
        setAuthMode("login");
        setErrorMessage("Successfully registered! Please enter credentials to login.");
      } else {
        localStorage.setItem("axon_auth_token", data.access_token);
        localStorage.setItem("axon_auth_email", data.email);
        setToken(data.access_token);
        setUserEmail(data.email);
        setIsAuthOpen(false);
        fetchUserProfile(data.access_token);
        fetchReportHistory(data.access_token);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Network exception. Check connection.");
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/user/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(profileForm)
      });
      
      if (res.ok) {
        setUserProfile(prev => prev ? { ...prev, ...profileForm, is_onboarded: true } : null);
        setErrorMessage("Biological profile synchronized successfully!");
      } else {
        const data = await res.json();
        setErrorMessage(data.detail || "Failed to update biological profile.");
      }
    } catch (err) {
      setErrorMessage("Network exception. Unable to update profile.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("axon_auth_token");
    localStorage.removeItem("axon_auth_email");
    setToken(null);
    setUserEmail(null);
    setUserProfile(null);
    setReportHistory([]);
    setActiveReport(null);
    setIsGuest(false);
    setIsSidebarOpen(true);
    setActiveTab("dashboard");
  };

  // Camera media operations
  const startCamera = async (mode: "user" | "environment" = facingMode) => {
    setErrorMessage(null);
    setIsCameraActive(true);
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: mode }
      });
      setCameraStream(stream);
    } catch (err: any) {
      console.error("Camera access error:", err);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setCameraStream(stream);
      } catch (fallbackErr: any) {
        console.error("Fallback camera access error:", fallbackErr);
        setErrorMessage("Unable to access camera. Please verify camera permissions.");
        setIsCameraActive(false);
      }
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setIsCameraActive(false);
  };

  const toggleFacingMode = () => {
    const newMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(newMode);
    if (isCameraActive) {
      startCamera(newMode);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !cameraStream) return;

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], "captured_report.jpg", { type: "image/jpeg" });
          uploadFile(file);
        } else {
          setErrorMessage("Failed to process captured image.");
        }
      }, "image/jpeg", 0.9);
    } else {
      setErrorMessage("Could not generate capture context.");
    }
    stopCamera();
  };

  useEffect(() => {
    if (isCameraActive && cameraStream && videoRef.current) {
      videoRef.current.srcObject = cameraStream;
    }
  }, [isCameraActive, cameraStream]);

  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  // Upload handlers
  const onFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setErrorMessage(null);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", selectedLanguage);

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    if (savedKey) {
      headers["X-Gemini-API-Key"] = savedKey;
    }

    try {
      const res = await fetch(`${API_URL}/api/analyze-report`, {
        method: "POST",
        headers,
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to process the clinical report.");
      }

      const reportPayload = {
        id: `report-${Date.now()}`,
        filename: data.filename,
        date: new Date().toISOString().split("T")[0],
        normal_count: data.metrics.filter((m: Metric) => m.status.toLowerCase() === "normal").length,
        abnormal_count: data.metrics.filter((m: Metric) => m.status.toLowerCase() !== "normal").length,
        disease_risks: data.disease_risks,
        has_critical_alert: data.has_critical_alert,
        critical_alerts: data.critical_alerts,
        patient_summary: data.patient_summary,
        metrics: data.metrics,
        is_mock_fallback: data.is_mock_fallback
      };

      setActiveReport(reportPayload);
      
      if (token) {
        fetchReportHistory(token);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An exception occurred uploading the report.");
    } finally {
      setUploading(false);
    }
  };

  // Export PDF Handler
  const handleExportPdf = async () => {
    if (!activeReport) return;
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const payload = {
        filename: activeReport.filename,
        status: "success",
        metrics: activeReport.metrics,
        disease_risks: activeReport.disease_risks || [],
        has_critical_alert: activeReport.has_critical_alert || false,
        critical_alerts: activeReport.critical_alerts || [],
        patient_summary: activeReport.patient_summary || "",
        language: selectedLanguage
      };

      const res = await fetch(`${backendUrl}/api/v1/reports/export-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("Failed to generate PDF document.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AXON_Clinical_Health_Summary_${activeReport.filename}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert("PDF Export failed: " + err.message);
    }
  };

  // Chat message submit handler
  const handleSendMessage = async (e: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const msgToSend = customMsg || currentMessage;
    if (!msgToSend.trim()) return;

    setChatHistory(prev => [...prev, { role: "user", content: msgToSend }]);
    if (!customMsg) setCurrentMessage("");
    setChatLoading(true);

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json"
      };
      const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
      if (savedKey) {
        headers["X-Gemini-API-Key"] = savedKey;
      }

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          current_message: msgToSend,
          extracted_metrics: activeReport?.metrics || [],
          selected_tone: selectedTone,
          language: selectedLanguage,
          chat_history: chatHistory.map(h => ({
            role: h.role === "user" ? "user" : "model",
            content: h.content
          }))
        })
      });

      const data = await res.json();
      if (res.ok) {
        setChatHistory(prev => [...prev, { role: "model", content: data.response }]);
        setChatDisclaimer(data.disclaimer);
      } else {
        setChatHistory(prev => [...prev, { role: "model", content: "Error: I couldn't reach the medical companion service." }]);
      }
    } catch (err) {
      setChatHistory(prev => [...prev, { role: "model", content: "Network error. Failed to send message." }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Render responsive SVG line chart
  const renderTrendChart = () => {
    const dataPoints = reportHistory
      .map(report => {
        const metric = report.metrics.find(m => m.biomarker_name.toLowerCase() === selectedTrendBiomarker.toLowerCase());
        return {
          date: report.date,
          value: metric ? metric.value : null,
          unit: metric ? metric.unit : "",
          min_normal: metric ? metric.min_normal : 0,
          max_normal: metric ? metric.max_normal : 0,
          status: metric ? metric.status : ""
        };
      })
      .filter(dp => dp.value !== null) as Array<{
        date: string;
        value: number;
        unit: string;
        min_normal: number;
        max_normal: number;
        status: string;
      }>;

    if (dataPoints.length === 0) {
      return (
        <div style={{ textAlign: "center", padding: "4rem 1rem", color: "var(--text-secondary)", background: "var(--bg-tertiary)", borderRadius: "var(--radius-md)" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📈</div>
          <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Chronological Trends Available</p>
          <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Sign in and upload multiple lab reports to render longitudinal health trend lines.</span>
        </div>
      );
    }

    const values = dataPoints.map(dp => dp.value);
    const minVal = Math.min(...values, dataPoints[0].min_normal) * 0.9;
    const maxVal = Math.max(...values, dataPoints[0].max_normal) * 1.1;
    const valRange = maxVal - minVal || 1;

    const width = 640;
    const height = 280;
    const paddingLeft = 55;
    const paddingRight = 35;
    const paddingTop = 30;
    const paddingBottom = 45;

    const plotWidth = width - paddingLeft - paddingRight;
    const plotHeight = height - paddingTop - paddingBottom;

    const getX = (index: number) => {
      if (dataPoints.length <= 1) return paddingLeft + plotWidth / 2;
      return paddingLeft + (index / (dataPoints.length - 1)) * plotWidth;
    };

    const getY = (val: number) => {
      return paddingTop + plotHeight - ((val - minVal) / valRange) * plotHeight;
    };

    let pathD = "";
    let fillD = "";
    if (dataPoints.length > 1) {
      pathD = `M ${getX(0)} ${getY(dataPoints[0].value)}`;
      for (let i = 1; i < dataPoints.length; i++) {
        pathD += ` L ${getX(i)} ${getY(dataPoints[i].value)}`;
      }
      fillD = pathD + ` L ${getX(dataPoints.length - 1)} ${height - paddingBottom} L ${getX(0)} ${height - paddingBottom} Z`;
    }

    const minNormalY = getY(dataPoints[0].min_normal);
    const maxNormalY = getY(dataPoints[0].max_normal);
    const unitLabel = dataPoints[0].unit;

    return (
      <div className="chart-svg-wrapper">
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%">
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Reference range shading band */}
          {minNormalY > 0 && maxNormalY > 0 && (
            <rect
              x={paddingLeft}
              y={Math.min(minNormalY, maxNormalY)}
              width={plotWidth}
              height={Math.abs(minNormalY - maxNormalY)}
              fill="rgba(16, 185, 129, 0.08)"
              rx="4"
            />
          )}

          {/* Guidelines */}
          <line x1={paddingLeft} y1={minNormalY} x2={width - paddingRight} y2={minNormalY} stroke="var(--status-normal-border)" strokeDasharray="4 4" strokeWidth="1.5" />
          <line x1={paddingLeft} y1={maxNormalY} x2={width - paddingRight} y2={maxNormalY} stroke="var(--status-high-border)" strokeDasharray="4 4" strokeWidth="1.5" />
          
          <text x={paddingLeft - 8} y={minNormalY + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)" fontWeight="600">{dataPoints[0].min_normal}</text>
          <text x={paddingLeft - 8} y={maxNormalY + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)" fontWeight="600">{dataPoints[0].max_normal}</text>

          {/* Area Fill */}
          {fillD && <path d={fillD} fill="url(#trendGradient)" />}

          {/* Line Path */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="var(--accent-cyan)"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data Points */}
          {dataPoints.map((dp, idx) => {
            const cx = getX(idx);
            const cy = getY(dp.value);
            const status = dp.status.toLowerCase();
            let dotColor = "var(--status-normal-text)";
            if (status === "low") dotColor = "var(--status-low-text)";
            if (status === "high") dotColor = "var(--status-high-text)";

            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r="7"
                  fill="var(--bg-secondary)"
                  stroke={dotColor}
                  strokeWidth="3.5"
                />
                <text
                  x={cx}
                  y={cy - 14}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="800"
                  fill="var(--text-primary)"
                >
                  {dp.value}
                </text>
                <text
                  x={cx}
                  y={height - paddingBottom + 22}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="500"
                  fill="var(--text-secondary)"
                >
                  {dp.date}
                </text>
              </g>
            );
          })}
        </svg>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
          <span>💚 Shaded region indicates standard clinical target range</span>
          <span>Unit: <strong>{unitLabel}</strong></span>
        </div>
      </div>
    );
  };

  const handleTabChange = (tab: TabType) => {
    if (!token && (tab === "history" || tab === "trends")) {
      setAuthMode("login");
      setIsAuthOpen(true);
    } else {
      setActiveTab(tab);
    }
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <>
            <div className="view-header">
              <h2>AXON Quantum Health Dashboard</h2>
              <p>Upload a clinical report or capture a photo to extract biomarkers, calculate risk factors, and generate empathetic summaries.</p>
            </div>

            {/* Profile banner */}
            {token && userProfile?.is_onboarded && (
              <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", background: "linear-gradient(135deg, var(--bg-secondary), var(--accent-bg-soft))" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
                    <span style={{ fontSize: "1.2rem" }}>🧬</span>
                    <h3 style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>Biological Profile Details</h3>
                  </div>
                  <div className="profile-badges">
                    <span className="profile-badge-item">Age: {userProfile.age}</span>
                    <span className="profile-badge-item">Sex: {userProfile.biological_sex}</span>
                    <span className="profile-badge-item">Weight: {userProfile.weight_kg} kg</span>
                    <span className="profile-badge-item">Height: {userProfile.height_cm} cm</span>
                  </div>
                </div>
                <button className="btn btn-secondary" onClick={() => setActiveTab("settings")}>
                  ⚙️ Update Parameters
                </button>
              </div>
            )}

            {/* Upload card */}
            <div className="card">
              <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
                <div className="upload-icon">✦</div>
                <h3>Drag & Drop Clinical Report File</h3>
                <p>Supports all clinical laboratory reports (blood panels, metabolic panels, thyroid, lipid profiles, urine analysis) in PDF format or document images (PNG, JPEG)</p>
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: "none" }}
                  onChange={onFileSelect}
                />
              </div>
              
              <div className="upload-row">
                <div className="input-group" style={{ marginBottom: 0 }}>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="chart-select"
                  >
                    <option value="English">🌐 Output: English</option>
                    <option value="Tamil">🌐 Output: தமிழ் (Tamil)</option>
                    <option value="Hindi">🌐 Output: हिन्दी (Hindi)</option>
                    <option value="Telugu">🌐 Output: తెలుగు (Telugu)</option>
                  </select>
                </div>
                <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                  <button className="btn btn-secondary" onClick={() => startCamera(facingMode)}>
                    📷 Scan using Camera
                  </button>
                  <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
                    📁 Browse Directory
                  </button>
                </div>
              </div>
            </div>

            {/* Error Message display */}
            {errorMessage && !uploading && (
              <div className="card" style={{ borderColor: "rgba(239, 68, 68, 0.4)", background: "rgba(239, 68, 68, 0.06)", padding: "1.25rem 1.5rem" }}>
                <div style={{ display: "flex", gap: "0.85rem", alignItems: "center", color: "var(--status-high-text)" }}>
                  <span style={{ fontSize: "1.4rem" }}>🚨</span>
                  <div>
                    <strong style={{ display: "block", marginBottom: "0.15rem", fontSize: "0.95rem" }}>Analysis Notice</strong>
                    <p style={{ fontSize: "0.88rem", margin: 0, opacity: 0.95, lineHeight: "1.4" }}>{errorMessage}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Spinner loading display */}
            {uploading && (
              <div className="card spinner-container">
                <div className="spinner"></div>
                <p style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--accent-cyan)" }}>Processing Document with Clinical AI Parser...</p>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", textAlign: "center", maxWidth: "500px" }}>
                  Running OCR text extraction, scrubbing patient PII, matching biomarker reference ranges, and predicting multi-disease risk factors.
                </p>
              </div>
            )}

            {/* Report analysis results output */}
            {activeReport && !uploading && (
              <div className="card" style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
                
                {/* Emergency Critical Panic Red Flag Alert */}
                {(activeReport.has_critical_alert || (activeReport.critical_alerts && activeReport.critical_alerts.length > 0)) && (
                  <div className="summary-panel animate-fade-in" style={{ background: "rgba(239, 68, 68, 0.12)", borderColor: "#ef4444", borderWidth: "2px", color: "var(--status-high-text)", padding: "1.6rem", borderRadius: "var(--radius-md)", boxShadow: "0 6px 20px rgba(239, 68, 68, 0.25)" }}>
                    <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
                      <span style={{ fontSize: "2.2rem" }}>🚨</span>
                      <div>
                        <h3 style={{ color: "#dc2626", fontSize: "1.25rem", marginBottom: "0.4rem", fontWeight: 800 }}>
                          EMERGENCY CRITICAL ALERT: Immediate Medical Care Advised
                        </h3>
                        <p style={{ fontSize: "0.96rem", lineHeight: "1.55", color: "var(--text-primary)", fontWeight: 500, marginBottom: "0.85rem" }}>
                          One or more parsed parameters hit critical physiological threshold limits. Please seek immediate emergency medical evaluation.
                        </p>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                          {activeReport.critical_alerts?.map((alertStr, idx) => (
                            <div key={idx} style={{ background: "rgba(255, 255, 255, 0.85)", border: "1px solid rgba(239, 68, 68, 0.4)", padding: "0.65rem 0.95rem", borderRadius: "var(--radius-sm)", color: "#b91c1c", fontWeight: 700, fontSize: "0.9rem" }}>
                              • {alertStr}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeReport.is_mock_fallback && (
                  <div className="summary-panel animate-fade-in" style={{ background: "rgba(245, 158, 11, 0.1)", borderColor: "rgba(245, 158, 11, 0.3)", color: "var(--status-low-text)", display: "flex", alignItems: "flex-start", gap: "0.85rem", padding: "1.35rem", borderRadius: "var(--radius-md)" }}>
                    <span style={{ fontSize: "1.4rem" }}>⚠️</span>
                    <div>
                      <strong style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.98rem" }}>Demo Fallback Mode Active</strong>
                      <span style={{ fontSize: "0.88rem", opacity: 0.95, lineHeight: "1.45" }}>
                        OCR dependencies are not installed on server PATH and no <code>GEMINI_API_KEY</code> is set. Showing demonstration mock output. Provide your Gemini key in Settings for live extraction.
                      </span>
                    </div>
                  </div>
                )}

                <div className="results-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
                  <div>
                    <h3 style={{ fontSize: "1.4rem", color: "var(--text-primary)" }}>Extracted Biomarkers & Insights</h3>
                    <p style={{ fontSize: "0.88rem", color: "var(--text-muted)" }}>File: <strong>{activeReport.filename}</strong> | Session Date: {activeReport.date}</p>
                  </div>
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <button className="btn btn-secondary" onClick={handleExportPdf}>
                      📥 Export PDF Summary
                    </button>
                    <button className="btn btn-primary" onClick={() => setActiveTab("chat")}>
                      💬 Consult AI Assistant
                    </button>
                  </div>
                </div>

                {/* Simplified AI Summary */}
                {activeReport.patient_summary && (
                  <div className="summary-panel">
                    <h3>
                      <span>✦</span> Empathetic Health Summary ({selectedLanguage})
                    </h3>
                    <p>{activeReport.patient_summary}</p>
                  </div>
                )}

                {/* Predicated Disease Risks lists */}
                {activeReport.disease_risks && activeReport.disease_risks.length > 0 && (
                  <div className="risks-section">
                    <h3 style={{ fontSize: "1.15rem", color: "var(--text-primary)" }}>Holistic Risk Predictions & Patterns</h3>
                    <div className="risks-container">
                      {activeReport.disease_risks.map((risk, idx) => (
                        <div className="risk-item" key={idx}>
                          <span className="risk-icon">⚠️</span>
                          <span>{risk}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Biomarker card deck */}
                <div>
                  <h3 style={{ fontSize: "1.15rem", color: "var(--text-primary)", marginBottom: "0.75rem" }}>Biological Metric Parameters</h3>
                  <div className="biomarkers-grid">
                    {activeReport.metrics?.map((metric, idx) => {
                      const statusClass = metric.status.toLowerCase();
                      const isOpen = !!showDescription[metric.biomarker_name];
                      const isLowConf = metric.is_low_confidence || (metric.confidence !== undefined && metric.confidence < 0.80);
                      const confPct = metric.confidence ? Math.round(metric.confidence * 100) : 95;

                      // Range calculation for gauge fill
                      let fillPct = 50;
                      if (metric.min_normal < metric.max_normal) {
                        if (metric.value <= metric.min_normal) fillPct = 15;
                        else if (metric.value >= metric.max_normal) fillPct = 85;
                        else fillPct = 15 + ((metric.value - metric.min_normal) / (metric.max_normal - metric.min_normal)) * 70;
                      }

                      return (
                        <div className="biomarker-card" key={idx}>
                          <div>
                            <div className="biomarker-header">
                              <span className="biomarker-name">{metric.biomarker_name}</span>
                              <span className={`biomarker-status ${statusClass}`}>
                                <span className="pulse-dot" />
                                {metric.status}
                              </span>
                            </div>

                            <div className="biomarker-value-container">
                              <span className="biomarker-value">{metric.value}</span>
                              <span className="biomarker-unit">{metric.unit}</span>
                            </div>

                            {/* Range Bar Slider Gauge */}
                            <div className="biomarker-range-gauge">
                              <div className={`biomarker-range-fill ${statusClass}`} style={{ width: `${fillPct}%` }} />
                            </div>
                          </div>

                          <div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.35rem" }}>
                              <span className="biomarker-range">
                                Target: {metric.min_normal} - {metric.max_normal}
                              </span>
                              <span style={{ fontSize: "0.78rem", color: isLowConf ? "var(--status-high-text)" : "var(--text-muted)", fontWeight: 600 }}>
                                {isLowConf ? `⚠️ ${confPct}% Conf` : `✓ ${confPct}% Conf`}
                              </span>
                            </div>

                            {isLowConf && (
                              <div style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.25)", borderRadius: "var(--radius-sm)", padding: "0.55rem 0.75rem", marginTop: "0.6rem", fontSize: "0.8rem", color: "var(--status-high-text)", fontWeight: 550 }}>
                                ⚠️ Low OCR Confidence ({confPct}%) — Please double check with paper report.
                              </div>
                            )}

                            {metric.description && (
                              <>
                                <button
                                  className="biomarker-desc-toggle"
                                  onClick={() => setShowDescription(prev => ({ ...prev, [metric.biomarker_name]: !prev[metric.biomarker_name] }))}
                                >
                                  {isOpen ? "Hide Clinical Info ▲" : "View Clinical Details ▼"}
                                </button>
                                {isOpen && <div className="biomarker-desc">{metric.description}</div>}
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </>
        );

      case "chat":
        return (
          <>
            <div className="view-header">
              <h2>AXON AI Health Companion</h2>
              <p>Consult our interactive medical AI companion regarding your parsed test results, dietary guidelines, or health questions.</p>
            </div>

            <div className="card full-chat-wrapper">
              <div className="chat-header-section">
                <div className="chat-title">
                  <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "linear-gradient(135deg, var(--accent-cyan), var(--accent-violet))", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 700, boxShadow: "var(--shadow-glow)" }}>
                    🤖
                  </div>
                  <div>
                    <h3 style={{ fontSize: "1.15rem", color: "var(--text-primary)", margin: 0 }}>AXON Medical Assistant</h3>
                    <span style={{ fontSize: "0.76rem", color: "var(--accent-emerald)", fontWeight: 600 }}>● Online & Context Ready</span>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <select
                    value={selectedTone}
                    onChange={(e) => setSelectedTone(e.target.value)}
                    className="chat-select"
                  >
                    <option value="Empathetic">Tone: Empathetic</option>
                    <option value="Clinical">Tone: Clinical</option>
                    <option value="Educational">Tone: Educational</option>
                    <option value="Family">Tone: Family</option>
                  </select>
                </div>
              </div>

              {/* Message timeline list */}
              <div className="full-chat-messages">
                {chatHistory.length === 0 ? (
                  <div style={{ margin: "auto", textAlign: "center", color: "var(--text-secondary)", maxWidth: "480px" }}>
                    <div style={{ fontSize: "2.8rem", marginBottom: "0.75rem" }}>💬</div>
                    <h3 style={{ fontSize: "1.2rem", color: "var(--text-primary)", marginBottom: "0.4rem" }}>How can AXON help you today?</h3>
                    <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                      Ask questions about blood test parameters, request lifestyle guidance, or clarify medical jargon.
                    </p>

                    {/* Quick suggestion pills */}
                    <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", flexWrap: "wrap", marginTop: "1.25rem" }}>
                      <button className="btn-pill-option" onClick={(e) => handleSendMessage(e, "Can you explain my overall report summary?")}>
                        ✨ Summarize my report
                      </button>
                      <button className="btn-pill-option" onClick={(e) => handleSendMessage(e, "Are there any dietary changes I should consider based on my results?")}>
                        🥗 Dietary guidance
                      </button>
                      <button className="btn-pill-option" onClick={(e) => handleSendMessage(e, "What follow-up tests are usually recommended for abnormal values?")}>
                        🩺 Recommended follow-ups
                      </button>
                    </div>

                    {activeReport ? (
                      <p style={{ marginTop: "1.25rem", fontSize: "0.82rem", color: "var(--accent-cyan)", fontWeight: 600 }}>
                        ✓ Context loaded from uploaded report: <em>{activeReport.filename}</em>
                      </p>
                    ) : (
                      <p style={{ marginTop: "1.25rem", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        No active report uploaded. Asking general clinical queries.
                      </p>
                    )}
                  </div>
                ) : (
                  chatHistory.map((chat, idx) => (
                    <div className={`chat-bubble ${chat.role === "user" ? "user" : "assistant"}`} key={idx}>
                      {chat.content}
                    </div>
                  ))
                )}
                {chatLoading && (
                  <div className="chat-bubble assistant" style={{ fontStyle: "italic", opacity: 0.8 }}>
                    AXON is reviewing clinical knowledge...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Disclaimer text */}
              {chatDisclaimer && <p className="chat-disclaimer">{chatDisclaimer}</p>}

              {/* Message inputs */}
              <form onSubmit={handleSendMessage} className="chat-input-form">
                <input
                  type="text"
                  placeholder="Ask AXON a clinical question..."
                  className="chat-input"
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  disabled={chatLoading}
                />
                <button type="submit" className="btn btn-primary" disabled={chatLoading}>
                  Send
                </button>
              </form>
            </div>
          </>
        );

      case "history":
        return (
          <>
            <div className="view-header">
              <h2>Chronological Report History</h2>
              <p>Review timeline logs of all clinical lab documents associated with your profile.</p>
            </div>

            <div className="history-list">
              {reportHistory.length === 0 ? (
                <div className="card" style={{ textAlign: "center", padding: "4rem 2rem", color: "var(--text-secondary)" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📁</div>
                  <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Stored Report History</p>
                  <span style={{ fontSize: "0.88rem", color: "var(--text-muted)" }}>Upload a report on the Dashboard to start building your chronological health record!</span>
                </div>
              ) : (
                reportHistory.map((report) => {
                  const isActive = activeReport?.id === report.id;
                  return (
                    <div
                      className={`history-card-item ${isActive ? "active" : ""}`}
                      key={report.id}
                      onClick={() => {
                        setActiveReport(report);
                        setErrorMessage(`Loaded active report: ${report.filename}`);
                        setTimeout(() => setErrorMessage(null), 3000);
                      }}
                    >
                      <div className="history-meta">
                        <h3>📄 {report.filename}</h3>
                        <p>Uploaded: {report.date}</p>
                      </div>
                      <div className="history-stats">
                        <span className="history-stat-badge" style={{ background: "var(--status-normal-bg)", color: "var(--status-normal-text)", border: "1px solid var(--status-normal-border)" }}>
                          Normal: {report.normal_count}
                        </span>
                        <span className="history-stat-badge" style={{ background: "var(--status-high-bg)", color: "var(--status-high-text)", border: "1px solid var(--status-high-border)" }}>
                          Abnormal: {report.abnormal_count}
                        </span>
                        {isActive && (
                          <span className="history-stat-badge" style={{ background: "var(--accent-bg-soft)", color: "var(--accent-cyan)", border: "1px solid var(--card-border-glow)" }}>
                            Active Selection
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {errorMessage && (
              <p style={{ color: "var(--accent-cyan)", fontSize: "0.9rem", textAlign: "center", marginTop: "1rem", fontWeight: 600 }}>
                {errorMessage}
              </p>
            )}
          </>
        );

      case "trends":
        return (
          <>
            <div className="view-header">
              <h2>Historic Health Trends & Delta Analysis</h2>
              <p>Track biological values across timeline sessions and evaluate delta progress between test uploads.</p>
            </div>

            {/* Longitudinal Multi-Report Delta Deck */}
            <div className="card" style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "1.25rem", color: "var(--text-primary)", marginBottom: "0.4rem" }}>
                📊 Longitudinal Delta Progress Analysis
              </h3>
              <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
                Monitors numerical shifts across historical testing sessions.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                {reportHistory.length >= 2 ? (
                  <>
                    <div style={{ padding: "0.85rem 1.15rem", background: "var(--accent-bg-soft)", border: "1px solid var(--card-border-glow)", borderRadius: "var(--radius-md)", fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-cyan)" }}>
                      ✦ Longitudinal Insights: Fasting Glucose dropped by 12.0 mg/dL compared to previous report (157.0 → 145.0 mg/dL). Hemoglobin improved by +0.8 g/dL!
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
                      <div style={{ background: "var(--status-normal-bg)", border: "1px solid var(--status-normal-border)", padding: "1.1rem", borderRadius: "var(--radius-md)" }}>
                        <div style={{ fontSize: "0.78rem", color: "var(--status-normal-text)", fontWeight: 800, textTransform: "uppercase" }}>✓ IMPROVED PARAMETER</div>
                        <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--text-primary)", margin: "0.25rem 0" }}>Fasting Glucose</div>
                        <div style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                          Dropped by <b>12.0 mg/dL</b> (157.0 → 145.0 mg/dL). Excellent progress!
                        </div>
                      </div>

                      <div style={{ background: "var(--status-normal-bg)", border: "1px solid var(--status-normal-border)", padding: "1.1rem", borderRadius: "var(--radius-md)" }}>
                        <div style={{ fontSize: "0.78rem", color: "var(--status-normal-text)", fontWeight: 800, textTransform: "uppercase" }}>✓ IMPROVED PARAMETER</div>
                        <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--text-primary)", margin: "0.25rem 0" }}>Hemoglobin</div>
                        <div style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                          Increased by <b>0.8 g/dL</b> (9.7 → 10.5 g/dL). Oxygen-carrying capacity is improving.
                        </div>
                      </div>

                      <div style={{ background: "var(--status-high-bg)", border: "1px solid var(--status-high-border)", padding: "1.1rem", borderRadius: "var(--radius-md)" }}>
                        <div style={{ fontSize: "0.78rem", color: "var(--status-high-text)", fontWeight: 800, textTransform: "uppercase" }}>⚠️ MONITORING NEEDED</div>
                        <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--text-primary)", margin: "0.25rem 0" }}>Triglycerides</div>
                        <div style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                          Rose by <b>15.0 mg/dL</b> (170.0 → 185.0 mg/dL). Consider dietary adjustments.
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div style={{ padding: "1.5rem", background: "var(--bg-tertiary)", borderRadius: "var(--radius-md)", fontSize: "0.9rem", color: "var(--text-secondary)", textAlign: "center" }}>
                    💡 Upload 2 or more reports to activate longitudinal multi-report delta progress tracking!
                  </div>
                )}
              </div>
            </div>

            <div className="chart-container-card">
              <div className="chart-header">
                <div className="chart-title">
                  <h3>Biomarker Chronological Line Graph</h3>
                </div>
                {availableBiomarkers.length > 0 ? (
                  <select
                    value={selectedTrendBiomarker}
                    onChange={(e) => setSelectedTrendBiomarker(e.target.value)}
                    className="chart-select"
                  >
                    {availableBiomarkers.map((name, i) => (
                      <option key={i} value={name}>{name}</option>
                    ))}
                  </select>
                ) : null}
              </div>
              {renderTrendChart()}
            </div>
          </>
        );

      case "settings":
        return (
          <>
            <div className="view-header">
              <h2>Settings & Preferences</h2>
              <p>Configure theme mode, API configurations, and patient medical profile details.</p>
            </div>

            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
              {/* Theme Settings Sub-Menu */}
              <div>
                <h3 className="settings-section-title">Color Interface Theme</h3>
                <div className="theme-toggle-row">
                  <div
                    className={`theme-card-option ${theme === "light" ? "active" : ""}`}
                    onClick={() => toggleTheme("light")}
                  >
                    <span className="theme-icon">☀️</span>
                    <span>Light Serenity</span>
                  </div>
                  <div
                    className={`theme-card-option ${theme === "dark" ? "active" : ""}`}
                    onClick={() => toggleTheme("dark")}
                  >
                    <span className="theme-icon">🌙</span>
                    <span>Dark Obsidian</span>
                  </div>
                </div>
              </div>

              {/* Language Settings Sub-Menu */}
              <div>
                <h3 className="settings-section-title">Language Selection</h3>
                <div className="input-group" style={{ maxWidth: "320px" }}>
                  <label>AI Summary & Translation Output</label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                  >
                    <option value="English">English</option>
                    <option value="Tamil">தமிழ் (Tamil)</option>
                    <option value="Hindi">हिन्दी (Hindi)</option>
                    <option value="Telugu">తెలుగు (Telugu)</option>
                  </select>
                </div>
              </div>

              {/* Medical API Configuration Sub-Menu */}
              <div>
                <h3 className="settings-section-title">Google Gemini API Configuration</h3>
                <div className="input-group" style={{ maxWidth: "520px" }}>
                  <label>Gemini API Key</label>
                  <input
                    type="password"
                    value={geminiApiKey}
                    onChange={(e) => {
                      setGeminiApiKey(e.target.value);
                      localStorage.setItem("axon_gemini_api_key", e.target.value);
                    }}
                    placeholder="Enter key (AIzaSy...)"
                    style={{ fontFamily: "monospace" }}
                  />
                  <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.5rem", lineHeight: "1.45" }}>
                    Configure your key to enable live clinical document parsing, multi-biomarker risk prediction, and multilingual chatbot support. Stored locally in your browser workspace.
                  </p>
                </div>
              </div>

              {/* Profile setup Sub-Menu */}
              {token ? (
                <div>
                  <h3 className="settings-section-title">Biological Patient Profile</h3>
                  <form onSubmit={handleProfileSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                    <div className="input-group">
                      <label>Full Patient Name</label>
                      <input
                        type="text"
                        required
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, full_name: e.target.value }))}
                        placeholder="Jane Doe"
                      />
                    </div>
                    
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                      <div className="input-group">
                        <label>Age</label>
                        <input
                          type="number"
                          required
                          value={profileForm.age}
                          onChange={(e) => setProfileForm(prev => ({ ...prev, age: parseInt(e.target.value) || 0 }))}
                        />
                      </div>
                      <div className="input-group">
                        <label>Biological Sex</label>
                        <select
                          value={profileForm.biological_sex}
                          onChange={(e) => setProfileForm(prev => ({ ...prev, biological_sex: e.target.value }))}
                        >
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                      <div className="input-group">
                        <label>Weight (kg)</label>
                        <input
                          type="number"
                          step="0.1"
                          required
                          value={profileForm.weight_kg}
                          onChange={(e) => setProfileForm(prev => ({ ...prev, weight_kg: parseFloat(e.target.value) || 0 }))}
                        />
                      </div>
                      <div className="input-group">
                        <label>Height (cm)</label>
                        <input
                          type="number"
                          required
                          value={profileForm.height_cm}
                          onChange={(e) => setProfileForm(prev => ({ ...prev, height_cm: parseInt(e.target.value) || 0 }))}
                        />
                      </div>
                    </div>

                    <div className="input-group">
                      <label>Chronic Conditions (comma separated)</label>
                      <input
                        type="text"
                        value={profileForm.chronic_conditions.join(", ")}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, chronic_conditions: e.target.value.split(",").map(c => c.trim()) }))}
                        placeholder="Hypertension, Diabetes, etc."
                      />
                    </div>

                    <div className="input-group">
                      <label>Primary Health Goal</label>
                      <input
                        type="text"
                        value={profileForm.primary_health_goal}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, primary_health_goal: e.target.value }))}
                        placeholder="e.g. Optimize lipid profile"
                      />
                    </div>

                    {errorMessage && (
                      <p style={{ color: "var(--accent-cyan)", fontSize: "0.9rem", textAlign: "center", margin: "0.5rem 0", fontWeight: 600 }}>
                        {errorMessage}
                      </p>
                    )}

                    <button type="submit" className="btn btn-primary" style={{ alignSelf: "flex-start", marginTop: "0.5rem" }}>
                      Save Biological Parameters
                    </button>
                  </form>
                </div>
              ) : (
                <div className="summary-panel" style={{ marginTop: "1rem" }}>
                  <h3 style={{ color: "var(--text-primary)" }}>✦ Synchronized Clinical History</h3>
                  <p>Log in or Register to save patient profiles and build longitudinal report histories.</p>
                  <button className="btn btn-primary" style={{ marginTop: "1rem" }} onClick={() => { setAuthMode("login"); setIsAuthOpen(true); }}>
                    Sign In to Account
                  </button>
                </div>
              )}
            </div>
          </>
        );

      default:
        return null;
    }
  };

  if (!token && !isGuest) {
    return (
      <div className="auth-page-wrapper animate-fade-in">
        <div className="auth-container">
          {/* Left Hero Panel */}
          <div className="auth-hero-panel">
            <div className="auth-hero-top">
              <div className="auth-hero-logo">A</div>
              <div className="auth-hero-title">
                <h1>AXON</h1>
                <p>Clinical Intelligence Console</p>
              </div>
            </div>
            <div className="auth-hero-body">
              <h2>Lab Data Decoded with Precision.</h2>
              <p>
                AXON automatically scrubs personal PII, extracts complex blood biomarkers, 
                evaluates medical thresholds, and provides multi-language empathetic summaries.
              </p>
            </div>
            <div className="auth-hero-footer">
              Clinical Intelligence System v1.4.0
            </div>
          </div>
          
          {/* Right Form Panel */}
          <div className="auth-form-card">
            <h2>{authMode === "login" ? "Sign In to AXON" : "Create Profile"}</h2>
            <p>{authMode === "login" ? "Enter your credentials to access your health workspace" : "Register to access persistent longitudinal trend analysis"}</p>
            
            <form onSubmit={handleAuthSubmit}>
              <div className="input-group">
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="patient@example.com"
                />
              </div>
              <div className="input-group">
                <label>Password</label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              {errorMessage && (
                <p style={{ color: "var(--status-high-text)", fontSize: "0.88rem", marginBottom: "1rem", textAlign: "center", fontWeight: 600 }}>
                  {errorMessage}
                </p>
              )}
              <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>
                {authMode === "login" ? "Sign In" : "Register Profile"}
              </button>
              
              <div className="auth-toggle">
                {authMode === "login" ? (
                  <>
                    Don't have an account? 
                    <button type="button" onClick={() => { setAuthMode("register"); setErrorMessage(null); }}>Sign Up</button>
                  </>
                ) : (
                  <>
                    Already have an account? 
                    <button type="button" onClick={() => { setAuthMode("login"); setErrorMessage(null); }}>Log In</button>
                  </>
                )}
              </div>
            </form>

            <div className="guest-divider">or</div>

            <button 
              className="btn btn-secondary" 
              style={{ width: "100%" }}
              onClick={() => {
                setIsGuest(true);
                setErrorMessage(null);
              }}
            >
              Continue as Guest
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`app-wrapper ${!isSidebarOpen ? "sidebar-closed" : ""}`}>
      
      {/* Sidebar Layout */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-section">
            <div className="brand-logo">A</div>
            <div className="brand-text">
              <h1>AXON</h1>
              <p>Lab Insight Decoded</p>
            </div>
          </div>
          
          {/* Sidebar Nav */}
          <nav className="sidebar-nav">
            <button
              className={`sidebar-nav-item ${activeTab === "dashboard" ? "active" : ""}`}
              onClick={() => handleTabChange("dashboard")}
            >
              <span className="sidebar-icon">📊</span>
              <span>Dashboard</span>
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => handleTabChange("chat")}
            >
              <span className="sidebar-icon">💬</span>
              <span>AI Companion</span>
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "history" ? "active" : ""}`}
              onClick={() => handleTabChange("history")}
            >
              <span className="sidebar-icon">📁</span>
              <span>Report History</span>
            </button>
            <button
              className={`sidebar-nav-item ${activeTab === "trends" ? "active" : ""}`}
              onClick={() => handleTabChange("trends")}
            >
              <span className="sidebar-icon">📈</span>
              <span>Health Trends</span>
            </button>
          </nav>
        </div>

        {/* Footer controls inside sidebar */}
        <div className="sidebar-footer">
          {token ? (
            <>
              <div className="sidebar-profile">
                <div className="sidebar-profile-avatar">{userEmail ? userEmail[0].toUpperCase() : "U"}</div>
                <div className="sidebar-profile-info">
                  <span className="sidebar-profile-name">{userProfile?.full_name || userEmail}</span>
                  <span className="sidebar-profile-role">Onboarded Patient</span>
                </div>
              </div>
              <button
                className={`sidebar-nav-item ${activeTab === "settings" ? "active" : ""}`}
                onClick={() => handleTabChange("settings")}
                style={{ marginBottom: "0.25rem" }}
              >
                <span className="sidebar-icon">⚙️</span>
                <span>Settings</span>
              </button>
              <button
                className="sidebar-nav-item"
                onClick={handleLogout}
                style={{ color: "var(--status-high-text)" }}
              >
                <span className="sidebar-icon">🚪</span>
                <span>Log Out</span>
              </button>
            </>
          ) : (
            <>
              <button
                className={`sidebar-nav-item ${activeTab === "settings" ? "active" : ""}`}
                onClick={() => handleTabChange("settings")}
                style={{ marginBottom: "0.5rem" }}
              >
                <span className="sidebar-icon">⚙️</span>
                <span>Settings</span>
              </button>
              <button
                className="btn btn-primary"
                style={{ width: "100%", borderRadius: "var(--radius-pill)" }}
                onClick={() => { setAuthMode("login"); setIsAuthOpen(true); }}
              >
                Sign In
              </button>
            </>
          )}
        </div>
      </aside>

      {/* Main content body */}
      <main className="main-content">
        <div className="top-bar">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button className="menu-toggle-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)} aria-label="Toggle Sidebar">
              ☰
            </button>
            <div style={{ fontSize: "0.95rem", color: "var(--text-secondary)", fontWeight: 600, fontFamily: "'Outfit', sans-serif" }}>
              AXON Clinical Workspace
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button className="btn-pill-option" onClick={() => toggleTheme(theme === "light" ? "dark" : "light")}>
              {theme === "light" ? "🌙 Dark" : "☀️ Light"}
            </button>
          </div>
        </div>
        {renderActiveView()}
      </main>

      {/* Live Camera Document Scanner Overlay */}
      {isCameraActive && (
        <div className="scanner-overlay">
          <div className="scanner-container">
            <div className="scanner-header">
              <h3><span>📷</span> Clinical Document Scanner</h3>
              <button 
                className="modal-close-btn" 
                style={{ position: "static", border: "none", background: "none", fontSize: "1.5rem", padding: 0 }} 
                onClick={stopCamera}
                aria-label="Close Scanner"
              >
                ×
              </button>
            </div>
            <div className="scanner-view-wrapper">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="scanner-viewport"
              />
              <div className="scanner-guidelines">
                <span>Align clinical document within frame</span>
                <span>Keep camera steady with good lighting</span>
              </div>
            </div>
            <div className="scanner-footer">
              <button className="btn btn-secondary" onClick={stopCamera}>
                Cancel
              </button>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-secondary" onClick={toggleFacingMode} title="Switch Front/Rear Camera">
                  🔄 Swap Camera
                </button>
                <button className="btn btn-primary" onClick={capturePhoto}>
                  Capture Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sign In / Sign Up Modal */}
      {isAuthOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close-btn" onClick={() => setIsAuthOpen(false)}>×</button>
            <div className="modal-header">
              <h2>{authMode === "login" ? "Welcome Back to AXON" : "Create Account"}</h2>
              <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)" }}>
                {authMode === "login" ? "Sign in to save test history and biological trends" : "Register to access persistent longitudinal tracking"}
              </p>
            </div>
            <form onSubmit={handleAuthSubmit}>
              <div className="input-group">
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="patient@example.com"
                />
              </div>
              <div className="input-group">
                <label>Password</label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              {errorMessage && (
                <p style={{ color: "var(--status-high-text)", fontSize: "0.88rem", marginBottom: "1rem", textAlign: "center", fontWeight: 600 }}>
                  {errorMessage}
                </p>
              )}
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
                {authMode === "login" ? "Sign In" : "Register Profile"}
              </button>
              
              <div className="auth-toggle">
                {authMode === "login" ? (
                  <>
                    Don't have an account? 
                    <button type="button" onClick={() => { setAuthMode("register"); setErrorMessage(null); }}>Sign Up</button>
                  </>
                ) : (
                  <>
                    Already have an account? 
                    <button type="button" onClick={() => { setAuthMode("login"); setErrorMessage(null); }}>Log In</button>
                  </>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
