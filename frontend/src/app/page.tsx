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
  status: string; // "Normal", "Low", "High", "Critical"
  confidence?: number;
  is_low_confidence?: boolean;
  is_critical?: boolean;
  critical_reason?: string | null;
  description: string | null;
  reference_source?: string;
  panel_category?: string;
}

interface ExplainableRule {
  rule_id: string;
  title: string;
  input_param: string;
  input_value: number;
  unit: string;
  reference_range: string;
  result_status: string;
  explanation: string;
  doctor_discussion_points?: string[];
}

interface FindingItem {
  finding_text: string;
  category: "normal" | "incidental" | "abnormal" | "urgent";
  plain_english_explanation: string;
  clinical_significance: string;
}

interface ScanReportAnalysisData {
  id?: string;
  filename?: string;
  upload_date?: string;
  report_type?: "scan";
  scan_metadata: {
    modality: string;
    body_region: string;
    indication?: string | null;
    technique_notes?: string | null;
  };
  triage: {
    is_emergency: boolean;
    emergency_message?: string | null;
    summary_headline: string;
  };
  findings_breakdown: FindingItem[];
  radiologist_impression_summary: string;
  questions_for_doctor: string[];
  image_preview?: string | null;
  analysis_mode?: string;
}

interface HistoricalReport {
  id: string;
  filename: string;
  date: string;
  report_type?: "lab" | "scan";
  normal_count: number;
  abnormal_count: number;
  disease_risks: string[];
  has_critical_alert?: boolean;
  critical_alerts?: string[];
  patient_summary: string;
  metrics: Metric[];
  analysis_mode?: string;
  engine_info?: string;
  explainable_rules?: ExplainableRule[];
  is_mock_fallback?: boolean;
  scan_data?: ScanReportAnalysisData | null;
}

type TabType = "lab-reports" | "scan-reports" | "chat" | "history" | "trends" | "settings";

export default function AXONDashboard() {
  // Navigation & Theme States
  const [activeTab, setActiveTab] = useState<TabType>("lab-reports");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isGuest, setIsGuest] = useState<boolean>(false);

  // Authentication & Session States
  const [token, setToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [reportHistory, setReportHistory] = useState<HistoricalReport[]>([]);

  // Engine configuration (Local Offline vs Cloud AI)
  const [engineMode, setEngineMode] = useState<"local" | "cloud">("local");
  const [geminiApiKey, setGeminiApiKey] = useState<string>("" );

  // ==========================================
  // LAB REPORTS STATE (PERSISTENT & SEPARATE)
  // ==========================================
  const [activeLabReport, setActiveLabReport] = useState<Partial<HistoricalReport> | null>(null);
  const [labUploading, setLabUploading] = useState<boolean>(false);
  const [labErrorMessage, setLabErrorMessage] = useState<string | null>(null);
  const [labLanguage, setLabLanguage] = useState<string>("English");
  const [labViewMode, setLabViewMode] = useState<"table" | "cards">("table");
  const [showDescription, setShowDescription] = useState<Record<string, boolean>>({});
  const [labDragOver, setLabDragOver] = useState<boolean>(false);
  const [labMismatchNotice, setLabMismatchNotice] = useState<{ message: string; file: File } | null>(null);

  // ==========================================
  // SCAN REPORTS STATE (PERSISTENT & SEPARATE)
  // ==========================================
  const [activeScanResult, setActiveScanResult] = useState<ScanReportAnalysisData | null>(null);
  const [scanUploading, setScanUploading] = useState<boolean>(false);
  const [scanErrorMessage, setScanErrorMessage] = useState<string | null>(null);
  const [scanLanguage, setScanLanguage] = useState<string>("English");
  const [scanInputMode, setScanInputMode] = useState<"image" | "text">("image");
  const [scanImagePreview, setScanImagePreview] = useState<string | null>(null);
  const [scanReportText, setScanReportText] = useState<string>("");
  const [scanFindingTab, setScanFindingTab] = useState<"abnormal" | "incidental" | "normal">("abnormal");
  const [expandedScanFindings, setExpandedScanFindings] = useState<Record<string, boolean>>({});
  const [scanDragOver, setScanDragOver] = useState<boolean>(false);
  const [scanMismatchNotice, setScanMismatchNotice] = useState<{ message: string; file: File } | null>(null);

  // ==========================================
  // CHATBOT & HISTORY FILTER STATES
  // ==========================================
  const [chatContextType, setChatContextType] = useState<"lab" | "scan">("lab");
  const [selectedTone, setSelectedTone] = useState<string>("Empathetic");
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "model"; content: string }>>([]);
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [chatDisclaimer, setChatDisclaimer] = useState<string>("");
  const [historyFilter, setHistoryFilter] = useState<"all" | "lab" | "scan">("all");
  const [selectedTrendBiomarker, setSelectedTrendBiomarker] = useState<string>("Hemoglobin");

  // Camera Scanner States
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraTarget, setCameraTarget] = useState<"lab" | "scan">("lab");
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("environment");

  // Auth Dialog States
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState<string>("");
  const [authPassword, setAuthPassword] = useState<string>("");

  // Profile Form
  const [profileForm, setProfileForm] = useState<UserProfile>({
    full_name: "",
    age: 30,
    biological_sex: "Male",
    weight_kg: 70,
    height_cm: 175,
    chronic_conditions: [],
    primary_health_goal: "Maintain general wellness",
    is_onboarded: false,
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const labFileInputRef = useRef<HTMLInputElement>(null);
  const scanFileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Initialize theme & stored credentials
  useEffect(() => {
    const savedTheme = localStorage.getItem("axon_theme") || "light";
    setTheme(savedTheme as "light" | "dark");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
    } else {
      document.documentElement.classList.remove("dark-theme");
    }

    const storedToken = localStorage.getItem("axon_auth_token");
    const storedEmail = localStorage.getItem("axon_auth_email");
    if (storedToken && storedEmail) {
      setToken(storedToken);
      setUserEmail(storedEmail);
      fetchUserProfile(storedToken);
      fetchReportHistory(storedToken);
    }

    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    setGeminiApiKey(savedKey);
  }, []);

  useEffect(() => {
    if (activeTab === "lab-reports") {
      setChatContextType("lab");
    } else if (activeTab === "scan-reports") {
      setChatContextType("scan");
    }
  }, [activeTab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const availableBiomarkers = React.useMemo(() => {
    const names = new Set<string>();
    reportHistory
      .filter((r) => r.report_type !== "scan")
      .forEach((report) => {
        report.metrics?.forEach((m) => names.add(m.biomarker_name));
      });
    if (names.size === 0 && activeLabReport?.metrics) {
      activeLabReport.metrics.forEach((m) => names.add(m.biomarker_name));
    }
    return Array.from(names);
  }, [reportHistory, activeLabReport]);

  useEffect(() => {
    if (availableBiomarkers.length > 0 && !availableBiomarkers.includes(selectedTrendBiomarker)) {
      setSelectedTrendBiomarker(availableBiomarkers[0]);
    }
  }, [availableBiomarkers, selectedTrendBiomarker]);

  const toggleTheme = (newTheme: "light" | "dark") => {
    setTheme(newTheme);
    localStorage.setItem("axon_theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
    } else {
      document.documentElement.classList.remove("dark-theme");
    }
  };

  const fetchUserProfile = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/api/user/profile`, {
        headers: { Authorization: `Bearer ${authToken}` },
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
          is_onboarded: data.is_onboarded,
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
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setReportHistory(data);
      }
    } catch (err) {
      console.error("Error fetching report history", err);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLabErrorMessage(null);
    setScanErrorMessage(null);

    const endpoint = authMode === "login" ? `${API_URL}/api/auth/login` : `${API_URL}/api/auth/register`;
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication request failed.");
      }

      setToken(data.access_token);
      setUserEmail(authEmail);
      localStorage.setItem("axon_auth_token", data.access_token);
      localStorage.setItem("axon_auth_email", authEmail);

      setIsAuthOpen(false);
      setIsGuest(false);
      fetchUserProfile(data.access_token);
      fetchReportHistory(data.access_token);
    } catch (err: any) {
      setLabErrorMessage(err.message || "Failed to complete authentication.");
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/user/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profileForm),
      });
      if (res.ok) {
        fetchUserProfile(token);
        alert("Biological parameters synchronized successfully.");
      }
    } catch (err) {
      alert("Failed to update profile.");
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUserEmail(null);
    setUserProfile(null);
    setReportHistory([]);
    localStorage.removeItem("axon_auth_token");
    localStorage.removeItem("axon_auth_email");
    setIsGuest(false);
    setActiveTab("lab-reports");
  };

  // Camera Handlers
  const startCamera = async (target: "lab" | "scan", mode: "user" | "environment" = facingMode) => {
    setCameraTarget(target);
    try {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: mode, width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      setCameraStream(stream);
      setIsCameraActive(true);
    } catch (err: any) {
      const msg = "Camera access denied or device not supported: " + err.message;
      if (target === "lab") setLabErrorMessage(msg);
      else setScanErrorMessage(msg);
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    setIsCameraActive(false);
  };

  const toggleFacingMode = () => {
    const newMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(newMode);
    startCamera(cameraTarget, newMode);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const fileName = cameraTarget === "lab" ? "photographed_lab_report.jpg" : "photographed_scan_film.jpg";
            const file = new File([blob], fileName, { type: "image/jpeg" });
            if (cameraTarget === "lab") {
              uploadLabFile(file);
            } else {
              handleUploadScanFile(file);
            }
          }
        },
        "image/jpeg",
        0.92
      );
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
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  // ==========================================
  // LAB REPORTS LOGIC
  // ==========================================
  const isLikelyScanReport = (fileName: string): boolean => {
    const lower = fileName.toLowerCase();
    const scanKeywords = ["mri", "ct", "x-ray", "xray", "ultrasound", "scan", "radiology", "dicom", "mammogram", "spine", "axial"];
    return scanKeywords.some((kw) => lower.includes(kw));
  };

  const onLabFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (isLikelyScanReport(file.name)) {
        setLabMismatchNotice({
          message: `"${file.name}" appears to be a radiology imaging report (MRI, CT, X-Ray, Ultrasound). Scan reports are evaluated via findings and impressions rather than reference ranges.`,
          file,
        });
        return;
      }
      await uploadLabFile(file);
    }
  };

  const handleLabDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setLabDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (isLikelyScanReport(file.name)) {
        setLabMismatchNotice({
          message: `"${file.name}" appears to be a radiology scan report. Would you like to analyze it on the Scan Reports page?`,
          file,
        });
        return;
      }
      await uploadLabFile(file);
    }
  };

  const uploadLabFile = async (file: File) => {
    setLabUploading(true);
    setLabErrorMessage(null);
    setLabMismatchNotice(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", labLanguage);
    formData.append("mode", engineMode);

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    if (savedKey) headers["X-Gemini-API-Key"] = savedKey;

    try {
      const res = await fetch(`${API_URL}/api/analyze-report`, {
        method: "POST",
        headers,
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        const detail = data.detail || "";
        if (detail.includes("MISMATCH_SCAN_REPORT")) {
          setLabMismatchNotice({
            message: detail.replace("MISMATCH_SCAN_REPORT:", "").trim(),
            file,
          });
          return;
        }
        throw new Error(detail || "Failed to process the clinical laboratory report.");
      }

      const reportPayload: HistoricalReport = {
        id: `report-${Date.now()}`,
        filename: data.filename,
        date: new Date().toISOString().split("T")[0],
        report_type: "lab",
        normal_count: data.metrics.filter((m: Metric) => m.status.toLowerCase() === "normal").length,
        abnormal_count: data.metrics.filter((m: Metric) => m.status.toLowerCase() !== "normal").length,
        disease_risks: data.disease_risks || [],
        has_critical_alert: data.has_critical_alert || false,
        critical_alerts: data.critical_alerts || [],
        patient_summary: data.patient_summary || "",
        metrics: data.metrics || [],
        analysis_mode: data.analysis_mode || "local",
        engine_info: data.engine_info || "AXON Local Analysis Engine",
        explainable_rules: data.explainable_rules || [],
        is_mock_fallback: data.is_mock_fallback,
      };

      setActiveLabReport(reportPayload);
      setChatContextType("lab");

      if (token) {
        fetchReportHistory(token);
      }
    } catch (err: any) {
      setLabErrorMessage(err.message || "An error occurred while uploading the laboratory report.");
    } finally {
      setLabUploading(false);
    }
  };

  const loadSampleLabReport = () => {
    const samplePayload: HistoricalReport = {
      id: `report-sample-cbc`,
      filename: "Standard_CBC_Metabolic_Report.pdf",
      date: new Date().toISOString().split("T")[0],
      report_type: "lab",
      normal_count: 5,
      abnormal_count: 3,
      disease_risks: [
        "Moderate Anemia Risk: Hemoglobin is below optimal bounds, indicating reduced oxygen-carrying capacity.",
        "Impaired Fasting Glucose: Fasting blood sugar level is mildly elevated, suggesting potential prediabetic pattern.",
        "Cardiovascular Lipid Flag: Total Cholesterol exceeds clinical guidelines (> 200 mg/dL).",
      ],
      has_critical_alert: false,
      critical_alerts: [],
      patient_summary:
        "Your laboratory panel indicates mild anemia (Hemoglobin 11.2 g/dL) and elevated fasting blood glucose (145.0 mg/dL). White blood cell count, platelets, and kidney filtration markers remain within healthy target bounds. Discuss dietary adjustments and glycemic evaluation with your physician.",
      engine_info: "AXON Clinical Rule Engine · Available Offline",
      analysis_mode: "local",
      explainable_rules: [
        {
          rule_id: "RULE-GLU-01",
          title: "Fasting Blood Glucose Elevation",
          input_param: "Fasting Glucose",
          input_value: 145.0,
          unit: "mg/dL",
          reference_range: "70.0 - 100.0",
          result_status: "High",
          explanation: "Fasting blood sugar of 145.0 mg/dL exceeds normal fasting targets (70.0 - 100.0 mg/dL).",
          doctor_discussion_points: [
            "Would you recommend checking an HbA1c to assess 90-day glycemic trends?",
            "Are there specific dietary carbohydrate modifications indicated?",
          ],
        },
        {
          rule_id: "RULE-HEM-02",
          title: "Microcytic Anemia Indicator",
          input_param: "Hemoglobin",
          input_value: 11.2,
          unit: "g/dL",
          reference_range: "12.0 - 17.5",
          result_status: "Low",
          explanation: "Hemoglobin is below standard reference range. Suggests mild reduction in red blood cell oxygenation.",
          doctor_discussion_points: ["Would a serum ferritin or iron profile test be useful?"],
        },
      ],
      metrics: [
        {
          biomarker_name: "Hemoglobin",
          value: 11.2,
          unit: "g/dL",
          min_normal: 12.0,
          max_normal: 17.5,
          status: "Low",
          confidence: 0.98,
          description: "Protein in red blood cells that transports oxygen to body tissues.",
        },
        {
          biomarker_name: "WBC",
          value: 7.5,
          unit: "10^3/uL",
          min_normal: 4.5,
          max_normal: 11.0,
          status: "Normal",
          confidence: 0.96,
          description: "White blood cells essential for immune defense against infection.",
        },
        {
          biomarker_name: "Platelets",
          value: 235.0,
          unit: "10^3/uL",
          min_normal: 150.0,
          max_normal: 450.0,
          status: "Normal",
          confidence: 0.95,
          description: "Cell fragments required for proper blood coagulation and clotting.",
        },
        {
          biomarker_name: "Fasting Glucose",
          value: 145.0,
          unit: "mg/dL",
          min_normal: 70.0,
          max_normal: 100.0,
          status: "High",
          confidence: 0.99,
          description: "Blood sugar level measured following an overnight fast.",
        },
        {
          biomarker_name: "HbA1c",
          value: 6.2,
          unit: "%",
          min_normal: 4.0,
          max_normal: 5.6,
          status: "High",
          confidence: 0.97,
          description: "Glycated hemoglobin reflecting average blood glucose control over past 2-3 months.",
        },
        {
          biomarker_name: "Total Cholesterol",
          value: 238.0,
          unit: "mg/dL",
          min_normal: 125.0,
          max_normal: 200.0,
          status: "High",
          confidence: 0.96,
          description: "Total circulating cholesterol level. Values above 200 warrant lifestyle management.",
        },
        {
          biomarker_name: "Serum Creatinine",
          value: 0.9,
          unit: "mg/dL",
          min_normal: 0.6,
          max_normal: 1.2,
          status: "Normal",
          confidence: 0.98,
          description: "Primary biological filtration indicator reflecting normal renal clearance.",
        },
        {
          biomarker_name: "TSH",
          value: 2.8,
          unit: "uIU/mL",
          min_normal: 0.4,
          max_normal: 4.5,
          status: "Normal",
          confidence: 0.95,
          description: "Thyroid-stimulating hormone reflecting balanced metabolic regulation.",
        },
      ],
    };
    setActiveLabReport(samplePayload);
    setChatContextType("lab");
  };

  // ==========================================
  // SCAN REPORTS LOGIC
  // ==========================================
  const isLikelyLabReport = (fileName: string): boolean => {
    const lower = fileName.toLowerCase();
    const labKeywords = ["cbc", "blood", "lipid", "glucose", "urine", "thyroid", "hba1c", "hemoglobin", "cholesterol", "metabolic"];
    return labKeywords.some((kw) => lower.includes(kw));
  };

  const onScanFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (isLikelyLabReport(file.name)) {
        setScanMismatchNotice({
          message: `"${file.name}" appears to be a clinical laboratory report (blood/urine tests). Lab reports are numeric tables evaluated against reference bounds.`,
          file,
        });
        return;
      }
      await handleUploadScanFile(file);
    }
  };

  const handleScanDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setScanDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (isLikelyLabReport(file.name)) {
        setScanMismatchNotice({
          message: `"${file.name}" appears to be a clinical laboratory report. Would you like to switch to the Lab Reports page?`,
          file,
        });
        return;
      }
      await handleUploadScanFile(file);
    }
  };

  const handleUploadScanFile = async (file: File) => {
    setScanUploading(true);
    setScanErrorMessage(null);
    setScanMismatchNotice(null);

    if (file.type.startsWith("image/")) {
      setScanImagePreview(URL.createObjectURL(file));
    } else {
      setScanImagePreview(null);
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", scanLanguage);

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    if (savedKey) headers["X-Gemini-API-Key"] = savedKey;

    try {
      const res = await fetch(`${API_URL}/api/analyze-scan-image`, {
        method: "POST",
        headers,
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        const detail = data.detail || "";
        if (detail.includes("MISMATCH_LAB_REPORT")) {
          setScanMismatchNotice({
            message: detail.replace("MISMATCH_LAB_REPORT:", "").trim(),
            file,
          });
          return;
        }
        throw new Error(detail || "Failed to analyze the radiology scan report.");
      }

      data.image_preview = file.type.startsWith("image/") ? URL.createObjectURL(file) : null;
      data.report_type = "scan";
      setActiveScanResult(data);
      setChatContextType("scan");

      if (token) {
        fetchReportHistory(token);
      }
    } catch (err: any) {
      setScanErrorMessage(err.message || "Failed to parse radiology imaging scan document.");
    } finally {
      setScanUploading(false);
    }
  };

  const handleAnalyzeRadiologyScan = async (overrideText?: string) => {
    const textToAnalyze = overrideText || scanReportText;
    if (!textToAnalyze.trim()) {
      setScanErrorMessage("Please enter or paste a radiology report narrative.");
      return;
    }

    setScanUploading(true);
    setScanErrorMessage(null);
    setScanMismatchNotice(null);
    setScanImagePreview(null);

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
    if (savedKey) headers["X-Gemini-API-Key"] = savedKey;

    try {
      const res = await fetch(`${API_URL}/api/analyze-scan`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          report_text: textToAnalyze,
          language: scanLanguage,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        const detail = data.detail || "";
        if (detail.includes("MISMATCH_LAB_REPORT")) {
          setScanErrorMessage(detail);
          return;
        }
        throw new Error(detail || "Failed to parse radiology report.");
      }

      data.report_type = "scan";
      setActiveScanResult(data);
      setChatContextType("scan");

      if (token) {
        fetchReportHistory(token);
      }
    } catch (err: any) {
      setScanErrorMessage(err.message || "Failed to parse radiology imaging report.");
    } finally {
      setScanUploading(false);
    }
  };

  const loadSampleMriReport = () => {
    const sample = `EXAMINATION: MRI LUMBAR SPINE WITHOUT CONTRAST
INDICATION: Chronic low back pain with left-sided L5/S1 radiculopathy and radiating pain to foot.
TECHNIQUE: Multiplanar multi-echo T1 and T2 weighted sequences acquired through lumbar spine.
FINDINGS:
Conus medullaris terminates normally at the L1-L2 junction with no spinal cord compression.
L1-L2 through L3-L4: Normal disc height and signal. Neural foramina are patent.
L4-L5: Mild diffuse disc desiccation with a minor 2 mm circumferential disc bulge. No significant canal stenosis.
L5-S1: Left paracentral disc protrusion measuring 4.5 mm, resulting in mild impingement on the traversing left S1 nerve root. No acute vertebral bone fracture or subluxation.
IMPRESSION:
1. L5-S1 left paracentral disc protrusion contacting the left S1 nerve root, correlating with patient's left leg pain.
2. Mild degenerative disc changes at L4-L5 without high-grade canal stenosis.
3. No acute fracture or spinal cord compression.`;
    setScanReportText(sample);
    setScanInputMode("text");
    handleAnalyzeRadiologyScan(sample);
  };

  const loadSampleChestXrayReport = () => {
    const sample = `EXAMINATION: CHEST RADIOGRAPH 2 VIEWS (PA AND LATERAL)
INDICATION: Productive cough, low-grade fever, and pleuritic right-sided chest discomfort for 4 days.
FINDINGS:
LUNGS: Patchy airspace opacity in the right lower lobe consistent with focal pneumonia/consolidation. No pleural effusion or pneumothorax identified. Left lung clear.
HEART & MEDIASTINUM: Cardiomediastinal silhouette is within normal limits for size and contour. Great vessels and hilar structures normal.
BONES: Intact osseous framework. No rib fractures or focal lytic lesions.
IMPRESSION:
1. Right lower lobe consolidation consistent with community-acquired pneumonia.
2. No pneumothorax or acute pleural effusion. Clinical correlation and antibiotic therapy follow-up recommended.`;
    setScanReportText(sample);
    setScanInputMode("text");
    handleAnalyzeRadiologyScan(sample);
  };

  // PDF Export
  const handleExportPdf = async () => {
    if (!activeLabReport) return;
    try {
      const payload = {
        filename: activeLabReport.filename,
        status: "success",
        metrics: activeLabReport.metrics,
        disease_risks: activeLabReport.disease_risks || [],
        has_critical_alert: activeLabReport.has_critical_alert || false,
        critical_alerts: activeLabReport.critical_alerts || [],
        patient_summary: activeLabReport.patient_summary || "",
        language: labLanguage,
      };

      const res = await fetch(`${API_URL}/api/v1/reports/export-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to generate PDF summary document.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AXON_Clinical_Lab_Summary_${activeLabReport.filename}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert("PDF Export failed: " + err.message);
    }
  };

  // Chat message submit handler
  const handleSendMessage = async (e?: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const msgToSend = customMsg || currentMessage;
    if (!msgToSend.trim()) return;

    setChatHistory((prev) => [...prev, { role: "user", content: msgToSend }]);
    if (!customMsg) setCurrentMessage("");
    setChatLoading(true);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const savedKey = localStorage.getItem("axon_gemini_api_key") || "";
      if (savedKey) headers["X-Gemini-API-Key"] = savedKey;

      const payload = {
        current_message: msgToSend,
        report_type: chatContextType,
        extracted_metrics: chatContextType === "lab" ? activeLabReport?.metrics || [] : [],
        scan_context: chatContextType === "scan" ? activeScanResult : null,
        selected_tone: selectedTone,
        language: chatContextType === "lab" ? labLanguage : scanLanguage,
        chat_history: chatHistory.map((h) => ({
          role: h.role === "user" ? "user" : "model",
          content: h.content,
        })),
      };

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (res.ok) {
        setChatHistory((prev) => [...prev, { role: "model", content: data.response }]);
        setChatDisclaimer(data.disclaimer);
      } else {
        setChatHistory((prev) => [...prev, { role: "model", content: "Error: I couldn't reach the medical companion service." }]);
      }
    } catch (err) {
      setChatHistory((prev) => [...prev, { role: "model", content: "Network error. Failed to send message." }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Render SVG Trend Chart
  const renderTrendChart = () => {
    const dataPoints = reportHistory
      .filter((r) => r.report_type !== "scan")
      .map((report) => {
        const metric = report.metrics?.find((m) => m.biomarker_name.toLowerCase() === selectedTrendBiomarker.toLowerCase());
        return {
          date: report.date,
          value: metric ? metric.value : null,
          unit: metric ? metric.unit : "",
          min_normal: metric ? metric.min_normal : 0,
          max_normal: metric ? metric.max_normal : 0,
          status: metric ? metric.status : "",
        };
      })
      .filter((dp) => dp.value !== null) as Array<{
      date: string;
      value: number;
      unit: string;
      min_normal: number;
      max_normal: number;
      status: string;
    }>;

    if (dataPoints.length === 0) {
      return (
        <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--text-secondary)", background: "var(--bg-tertiary)", borderRadius: "var(--radius-md)" }}>
          <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Chronological Lab Trends Available</p>
          <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>Sign in and upload multiple lab reports to render longitudinal health trend lines.</span>
        </div>
      );
    }

    const values = dataPoints.map((dp) => dp.value);
    const minVal = Math.min(...values, dataPoints[0].min_normal) * 0.9;
    const maxVal = Math.max(...values, dataPoints[0].max_normal) * 1.1;
    const valRange = maxVal - minVal || 1;

    const width = 640;
    const height = 260;
    const paddingLeft = 50;
    const paddingRight = 30;
    const paddingTop = 25;
    const paddingBottom = 40;

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
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", minWidth: "480px", height: "auto" }}>
          <rect
            x={paddingLeft}
            y={Math.min(minNormalY, maxNormalY)}
            width={plotWidth}
            height={Math.abs(minNormalY - maxNormalY)}
            fill="rgba(62, 155, 104, 0.08)"
            stroke="rgba(62, 155, 104, 0.25)"
            strokeDasharray="4 4"
          />

          {fillD && <path d={fillD} fill="rgba(13, 155, 138, 0.12)" />}
          {pathD && <path d={pathD} fill="none" stroke="var(--accent-primary)" strokeWidth="2.5" strokeLinecap="round" />}

          {dataPoints.map((dp, idx) => {
            const cx = getX(idx);
            const cy = getY(dp.value);
            const status = dp.status.toLowerCase();
            let dotColor = "var(--status-normal-text)";
            if (status === "low") dotColor = "var(--status-low-text)";
            if (status === "high") dotColor = "var(--status-high-text)";

            return (
              <g key={idx}>
                <circle cx={cx} cy={cy} r="5.5" fill="var(--bg-secondary)" stroke={dotColor} strokeWidth="3" />
                <text x={cx} y={cy - 10} textAnchor="middle" fontSize="10" fontWeight="600" fill="var(--text-primary)">
                  {dp.value}
                </text>
                <text x={cx} y={height - paddingBottom + 18} textAnchor="middle" fontSize="9" fontWeight="500" fill="var(--text-secondary)">
                  {dp.date}
                </text>
              </g>
            );
          })}
        </svg>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.76rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
          <span>Shaded band represents clinical reference boundary</span>
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

  const handleSwitchToScan = (file: File) => {
    setLabMismatchNotice(null);
    setActiveTab("scan-reports");
    handleUploadScanFile(file);
  };

  const handleSwitchToLab = (file: File) => {
    setScanMismatchNotice(null);
    setActiveTab("lab-reports");
    uploadLabFile(file);
  };

  const historicalLabReports = reportHistory.filter((r) => r.report_type !== "scan");
  const historicalScanReports = reportHistory.filter((r) => r.report_type === "scan");

  // ==========================================
  // RENDER ACTIVE VIEW
  // ==========================================
  const renderActiveView = () => {
    switch (activeTab) {
      // ----------------------------------------------------
      // PAGE 1: LAB REPORTS (REDESIGNED PASS 1)
      // ----------------------------------------------------
      case "lab-reports":
        return (
          <div className="content-gutter">
            {/* Page Introduction: Savana Clinical Clarity & Editorial Rhythm */}
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Laboratory Biomarker Intelligence</h2>
                <p>Understand your laboratory results with clear biomarker explanations and reference-range insights.</p>
              </div>

              {/* Engine Status & Offline Indicator */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                <div className="engine-status-bar" title="Analysis executes locally on-device without cloud dependence">
                  <span className="status-dot-pip" />
                  <span>Local Analysis Engine · Available Offline</span>
                </div>

                <div className="engine-segment-toggle">
                  <button
                    className={`engine-segment-btn ${engineMode === "local" ? "active" : ""}`}
                    onClick={() => setEngineMode("local")}
                  >
                    Local Mode
                  </button>
                  <button
                    className={`engine-segment-btn ${engineMode === "cloud" ? "active" : ""}`}
                    onClick={() => setEngineMode("cloud")}
                  >
                    Cloud AI
                  </button>
                </div>
              </div>
            </div>

            {/* Mismatch Alert Banner if a Scan Report was detected */}
            {labMismatchNotice && (
              <div className="mismatch-alert-banner">
                <div className="mismatch-alert-content">
                  <div className="mismatch-alert-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <path d="M7 7h10M7 12h10M7 17h6" />
                    </svg>
                  </div>
                  <div className="mismatch-alert-text">
                    <h4>Radiology / Imaging Scan Document Detected</h4>
                    <p>{labMismatchNotice.message}</p>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => handleSwitchToScan(labMismatchNotice.file)}>
                    Switch to Scan Reports & Analyze
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setLabMismatchNotice(null)}>
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {/* COMPACT, RESTRAINED LAB REPORT UPLOADER */}
            <div className="lab-uploader-card">
              <div
                className={`lab-drop-target ${labDragOver ? "drag-active" : ""}`}
                onClick={() => labFileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setLabDragOver(true);
                }}
                onDragLeave={() => setLabDragOver(false)}
                onDrop={handleLabDrop}
              >
                <div className="upload-icon-circle">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10 2v7.31L4.15 19.3A2 2 0 0 0 5.86 22h12.28a2 2 0 0 0 1.71-2.7L14 9.31V2" />
                    <line x1="8" y1="2" x2="16" y2="2" />
                    <line x1="7" y1="16" x2="17" y2="16" />
                  </svg>
                </div>
                <div className="lab-drop-meta">
                  <h3>Upload your laboratory report</h3>
                  <p>Drag & drop your clinical lab document, or browse your device</p>
                </div>
                <input
                  type="file"
                  ref={labFileInputRef}
                  style={{ display: "none" }}
                  accept="application/pdf,image/png,image/jpeg,image/jpg,image/webp"
                  onChange={onLabFileSelect}
                />
              </div>

              {/* Upload Action Hierarchy */}
              <div className="lab-uploader-controls">
                <div className="upload-format-tags">
                  <span>Accepted: <strong>PDF, PNG, JPG</strong></span>
                  <span>•</span>
                  <span>Max: <strong>15MB</strong></span>
                  <span>•</span>
                  <span>Summary Language:</span>
                  <select
                    value={labLanguage}
                    onChange={(e) => setLabLanguage(e.target.value)}
                    className="select-input"
                    style={{ padding: "0.25rem 0.5rem", fontSize: "0.78rem" }}
                  >
                    <option value="English">English</option>
                    <option value="Tamil">தமிழ் (Tamil)</option>
                    <option value="Hindi">हिन्दी (Hindi)</option>
                    <option value="Telugu">తెలుగు (Telugu)</option>
                    <option value="Spanish">Español (Spanish)</option>
                    <option value="French">Français (French)</option>
                    <option value="German">Deutsch (German)</option>
                  </select>
                </div>

                <div className="upload-action-group">
                  <button className="btn btn-ghost btn-sm" onClick={loadSampleLabReport}>
                    Load Sample CBC Report
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => startCamera("lab")}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                    Photograph Report
                  </button>
                  <button className="btn btn-primary btn-sm" onClick={() => labFileInputRef.current?.click()}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                    Browse Files
                  </button>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {labUploading && (
              <div className="card" style={{ textAlign: "center", padding: "2.5rem 1rem" }}>
                <div style={{ display: "inline-block", width: "24px", height: "24px", border: "2px solid var(--card-border)", borderTopColor: "var(--accent-primary)", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                <h4 style={{ fontSize: "1rem", marginTop: "0.85rem", color: "var(--text-primary)" }}>Processing Laboratory Report...</h4>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                  Extracting numerical values, validating clinical reference intervals, and evaluating panic thresholds.
                </p>
                <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
              </div>
            )}

            {/* Error Message */}
            {labErrorMessage && !labUploading && (
              <div className="card" style={{ borderLeft: "3px solid var(--status-critical-text)", background: "var(--status-critical-bg)", padding: "1rem 1.25rem" }}>
                <p style={{ color: "var(--status-critical-text)", fontSize: "0.86rem", fontWeight: 500 }}>{labErrorMessage}</p>
              </div>
            )}

            {/* EMPTY STATE / SUPPORTING CONTENT WHEN NO ACTIVE LAB REPORT */}
            {!activeLabReport && !labUploading && (
              <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h3 style={{ fontSize: "0.98rem", fontWeight: 600 }}>Supported Clinical Laboratory Panels</h3>
                    <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                      AXON local deterministic rules engine supports automatic normalization for standardized diagnostic tests:
                    </p>
                  </div>
                  {historicalLabReports.length > 0 && (
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      {historicalLabReports.length} past record{historicalLabReports.length > 1 ? "s" : ""} in profile
                    </span>
                  )}
                </div>

                <div className="supported-panels-grid">
                  <div className="panel-card-item">
                    <h4>Complete Blood Count (CBC)</h4>
                    <p>Hemoglobin, Hematocrit, RBC, Platelet Count, Total WBC, and Differential metrics.</p>
                  </div>
                  <div className="panel-card-item">
                    <h4>Comprehensive Metabolic (CMP)</h4>
                    <p>Fasting Blood Sugar, Serum Electrolytes (Sodium, Potassium), and Renal parameters.</p>
                  </div>
                  <div className="panel-card-item">
                    <h4>Lipid & Cardiovascular Panel</h4>
                    <p>Total Cholesterol, Triglycerides, High-Density Lipoprotein (HDL), and LDL particles.</p>
                  </div>
                  <div className="panel-card-item">
                    <h4>Thyroid Function Panel</h4>
                    <p>Thyroid-Stimulating Hormone (TSH), Free T3, and Free T4 endocrine boundaries.</p>
                  </div>
                  <div className="panel-card-item">
                    <h4>Hepatic & Liver Function</h4>
                    <p>Alanine Aminotransferase (ALT/SGPT), Aspartate Aminotransferase (AST), and Bilirubin.</p>
                  </div>
                  <div className="panel-card-item">
                    <h4>Renal & Kidney Markers</h4>
                    <p>Serum Creatinine, Blood Urea Nitrogen (BUN), and estimated GFR bounds.</p>
                  </div>
                </div>

                {/* Recent Reports in History */}
                {historicalLabReports.length > 0 && (
                  <div style={{ marginTop: "0.5rem", borderTop: "1px solid var(--card-border-subtle)", paddingTop: "0.85rem" }}>
                    <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Recently Analyzed Lab Reports
                    </div>
                    <div className="recent-strip">
                      {historicalLabReports.slice(0, 4).map((rep) => (
                        <div
                          key={rep.id}
                          className="recent-strip-item"
                          onClick={() => {
                            setActiveLabReport(rep);
                            setChatContextType("lab");
                          }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                          </svg>
                          <div>
                            <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-primary)" }}>{rep.filename}</div>
                            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{rep.date} • {rep.metrics.length} biomarkers</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* LAB RESULTS PRESENTATION (SAVANA CLINICAL CLARITY) */}
            {activeLabReport && !labUploading && (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {/* Critical Panic Alert if triggered */}
                {(activeLabReport.has_critical_alert || (activeLabReport.critical_alerts && activeLabReport.critical_alerts.length > 0)) && (
                  <div className="emergency-alert-banner">
                    <h3>Critical Threshold Alert: Clinical Evaluation Advised</h3>
                    <p>One or more biological values exceed standard clinical safety margins:</p>
                    <ul style={{ margin: "0.4rem 0 0 1.25rem", padding: 0 }}>
                      {activeLabReport.critical_alerts?.map((alertStr, idx) => (
                        <li key={idx} style={{ fontWeight: 600, fontSize: "0.86rem" }}>{alertStr}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Results Action Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
                  <div>
                    <h3 style={{ fontSize: "1.15rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Biomarker Analysis Results
                    </h3>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Report: <strong>{activeLabReport.filename}</strong> • Analyzed via {activeLabReport.engine_info || "AXON Local Engine"}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <div className="engine-segment-toggle">
                      <button
                        className={`engine-segment-btn ${labViewMode === "table" ? "active" : ""}`}
                        onClick={() => setLabViewMode("table")}
                      >
                        Table View
                      </button>
                      <button
                        className={`engine-segment-btn ${labViewMode === "cards" ? "active" : ""}`}
                        onClick={() => setLabViewMode("cards")}
                      >
                        Gauges
                      </button>
                    </div>

                    <button className="btn btn-secondary btn-sm" onClick={handleExportPdf}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export PDF
                    </button>

                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        setChatContextType("lab");
                        setActiveTab("chat");
                      }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                      Ask Companion
                    </button>
                  </div>
                </div>

                {/* Plain-Language Summary */}
                {activeLabReport.patient_summary && (
                  <div className="summary-panel">
                    <h3>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2">
                        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                      </svg>
                      Plain-Language Summary ({labLanguage})
                    </h3>
                    <p style={{ whiteSpace: "pre-line" }}>{activeLabReport.patient_summary}</p>
                  </div>
                )}

                {/* VIEW 1: STRUCTURED CLINICAL TABLE */}
                {labViewMode === "table" && (
                  <div className="table-responsive-container">
                    <table className="clinical-results-table">
                      <thead>
                        <tr>
                          <th>Biomarker / Test Name</th>
                          <th>Measured Value</th>
                          <th>Unit</th>
                          <th>Reference Range</th>
                          <th>Status</th>
                          <th>Clinical Guidance & Interpretation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeLabReport.metrics?.map((metric, idx) => {
                          const statusLower = metric.status.toLowerCase();
                          const isCrit = metric.is_critical || statusLower === "critical";

                          let badgeClass = "normal";
                          let labelText = "Normal";
                          if (statusLower === "low") {
                            badgeClass = "low";
                            labelText = "Low";
                          } else if (statusLower === "high") {
                            badgeClass = "high";
                            labelText = "High";
                          }
                          if (isCrit) {
                            badgeClass = "critical";
                            labelText = "Critical";
                          }

                          return (
                            <tr key={idx}>
                              <td>
                                <div className="table-biomarker-cell">
                                  <span className="table-biomarker-title">{metric.biomarker_name}</span>
                                  {metric.reference_source && (
                                    <span className="table-biomarker-subtitle">Ref: {metric.reference_source}</span>
                                  )}
                                </div>
                              </td>
                              <td>
                                <span className="table-val-pill">{metric.value}</span>
                              </td>
                              <td style={{ color: "var(--text-secondary)", fontWeight: 500 }}>{metric.unit}</td>
                              <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                                {metric.min_normal} – {metric.max_normal} {metric.unit}
                              </td>
                              <td>
                                <span className={`status-badge-pill ${badgeClass}`}>
                                  {labelText}
                                </span>
                              </td>
                              <td style={{ maxWidth: "360px", fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                                {metric.critical_reason ? (
                                  <span style={{ color: "var(--status-critical-text)", fontWeight: 600 }}>{metric.critical_reason}</span>
                                ) : metric.description ? (
                                  metric.description
                                ) : (
                                  statusLower === "normal"
                                    ? "Result falls comfortably within normal clinical reference range."
                                    : "Value deviates from standard guidelines. Review with your physician."
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* VIEW 2: BIOMARKER GAUGES */}
                {labViewMode === "cards" && (
                  <div className="biomarkers-grid">
                    {activeLabReport.metrics?.map((metric, idx) => {
                      const statusClass = metric.status.toLowerCase();
                      const isOpen = !!showDescription[metric.biomarker_name];
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
                              <span className={`status-badge-pill ${statusClass}`}>{metric.status}</span>
                            </div>

                            <div className="biomarker-value-container">
                              <span className="biomarker-value">{metric.value}</span>
                              <span className="biomarker-unit">{metric.unit}</span>
                            </div>

                            <div className="biomarker-range-gauge">
                              <div className={`biomarker-range-fill ${statusClass}`} style={{ width: `${fillPct}%` }} />
                            </div>
                          </div>

                          <div>
                            <div className="biomarker-range">
                              Target: {metric.min_normal} – {metric.max_normal} {metric.unit}
                            </div>
                            {metric.description && (
                              <>
                                <button
                                  className="biomarker-desc-toggle"
                                  onClick={() => setShowDescription((prev) => ({ ...prev, [metric.biomarker_name]: !prev[metric.biomarker_name] }))}
                                >
                                  {isOpen ? "Hide details" : "View clinical details"}
                                </button>
                                {isOpen && <div className="biomarker-desc">{metric.description}</div>}
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Explainable Clinical Rules (Savana Structured Presentation) */}
                {activeLabReport.explainable_rules && activeLabReport.explainable_rules.length > 0 && (
                  <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                      </svg>
                      <h4 style={{ fontSize: "0.96rem", fontWeight: 600 }}>Explainable Clinical Rule Engine</h4>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {activeLabReport.explainable_rules.map((rule, idx) => (
                        <div key={idx} style={{ background: "var(--bg-tertiary)", border: "1px solid var(--card-border-subtle)", padding: "0.85rem 1rem", borderRadius: "var(--radius-sm)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                            <span style={{ fontWeight: 600, fontSize: "0.86rem", color: "var(--text-primary)" }}>
                              {rule.rule_id}: {rule.title}
                            </span>
                            <span className={`status-badge-pill ${rule.result_status.toLowerCase()}`}>{rule.result_status}</span>
                          </div>
                          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.45, marginBottom: "0.4rem" }}>
                            {rule.explanation}
                          </p>
                          {rule.doctor_discussion_points && rule.doctor_discussion_points.length > 0 && (
                            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", background: "var(--bg-card)", padding: "0.4rem 0.65rem", borderRadius: "var(--radius-xs)" }}>
                              <strong style={{ color: "var(--text-primary)" }}>Suggested Doctor Discussion:</strong>
                              <ul style={{ margin: "0.2rem 0 0 1rem", padding: 0 }}>
                                {rule.doctor_discussion_points.map((pt, pIdx) => (
                                  <li key={pIdx}>{pt}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Holistic Disease Risk Predictions */}
                {activeLabReport.disease_risks && activeLabReport.disease_risks.length > 0 && (
                  <div className="risks-section">
                    <h3>Risk Pattern Indications</h3>
                    <div className="risks-container">
                      {activeLabReport.disease_risks.map((risk, idx) => (
                        <div className="risk-item" key={idx}>
                          <span style={{ color: "var(--status-low-text)" }}>•</span>
                          <span>{risk}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      // ----------------------------------------------------
      // PAGE 2: SCAN REPORTS (PRESERVED)
      // ----------------------------------------------------
      case "scan-reports":
        return (
          <div className="content-gutter">
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Radiology & Scan Reports Intelligence</h2>
                <p>Upload or paste imaging scan reports (MRI, CT, X-Ray, Ultrasound) to decode findings, categories, and radiologist impressions.</p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-ghost btn-sm" onClick={loadSampleMriReport}>
                  Sample Spine MRI
                </button>
                <button className="btn btn-ghost btn-sm" onClick={loadSampleChestXrayReport}>
                  Sample Chest X-Ray
                </button>
              </div>
            </div>

            <div className="ai-disclaimer-callout">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0, marginTop: "2px" }}>
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <div>
                <strong>AI Clinical Scope Notice:</strong> AXON AI extracts, classifies, and translates the <em>written text</em> and radiologist impressions from diagnostic imaging reports. It summarizes the written findings and does <strong>not</strong> re-interpret physical imaging scans or radiographs themselves. Always consult your attending radiologist and ordering physician.
              </div>
            </div>

            {scanMismatchNotice && (
              <div className="mismatch-alert-banner">
                <div className="mismatch-alert-content">
                  <div className="mismatch-alert-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M10 2v7.31L4.15 19.3A2 2 0 0 0 5.86 22h12.28a2 2 0 0 0 1.71-2.7L14 9.31V2" />
                    </svg>
                  </div>
                  <div className="mismatch-alert-text">
                    <h4>Laboratory Biomarker Document Detected</h4>
                    <p>{scanMismatchNotice.message}</p>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => handleSwitchToLab(scanMismatchNotice.file)}>
                    Switch to Lab Reports & Analyze
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setScanMismatchNotice(null)}>
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
                <div className="engine-segment-toggle">
                  <button
                    className={`engine-segment-btn ${scanInputMode === "image" ? "active" : ""}`}
                    onClick={() => setScanInputMode("image")}
                  >
                    Upload Scan File (PDF / Image)
                  </button>
                  <button
                    className={`engine-segment-btn ${scanInputMode === "text" ? "active" : ""}`}
                    onClick={() => setScanInputMode("text")}
                  >
                    Paste Narrative Text
                  </button>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Translate:</span>
                  <select
                    value={scanLanguage}
                    onChange={(e) => setScanLanguage(e.target.value)}
                    className="select-input"
                    style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                  >
                    <option value="English">English</option>
                    <option value="Tamil">தமிழ் (Tamil)</option>
                    <option value="Hindi">हिन्दी (Hindi)</option>
                    <option value="Telugu">తెలుగు (Telugu)</option>
                    <option value="Spanish">Español (Spanish)</option>
                    <option value="French">Français (French)</option>
                    <option value="German">Deutsch (German)</option>
                  </select>
                </div>
              </div>

              {scanInputMode === "image" && (
                <div>
                  <div
                    className={`lab-drop-target ${scanDragOver ? "drag-active" : ""}`}
                    onClick={() => scanFileInputRef.current?.click()}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setScanDragOver(true);
                    }}
                    onDragLeave={() => setScanDragOver(false)}
                    onDrop={handleScanDrop}
                  >
                    <div className="upload-icon-circle">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" />
                        <path d="M7 7h10M7 12h10M7 17h6" />
                      </svg>
                    </div>
                    <div className="lab-drop-meta">
                      <h3>Upload medical scan document</h3>
                      <p>Supports X-Ray, CT, MRI, Ultrasound, Mammogram reports as PDF, JPG, PNG, or DICOM exports</p>
                    </div>
                    <input
                      type="file"
                      ref={scanFileInputRef}
                      style={{ display: "none" }}
                      accept="application/pdf,image/png,image/jpeg,image/jpg,image/webp"
                      onChange={onScanFileSelect}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.85rem", flexWrap: "wrap", gap: "0.5rem" }}>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Accepts lightbox film photos, digital radiologist PDFs, or scan captures
                    </span>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => startCamera("scan")}>
                        Photograph Film
                      </button>
                      <button className="btn btn-primary btn-sm" onClick={() => scanFileInputRef.current?.click()}>
                        Browse Device
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {scanInputMode === "text" && (
                <div>
                  <textarea
                    rows={6}
                    value={scanReportText}
                    onChange={(e) => setScanReportText(e.target.value)}
                    placeholder="Paste radiology examination report text here..."
                    style={{
                      width: "100%",
                      padding: "0.85rem",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--card-border)",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      fontFamily: "monospace",
                      fontSize: "0.85rem",
                      lineHeight: 1.5,
                      marginBottom: "0.75rem",
                    }}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <button className="btn btn-primary btn-sm" onClick={() => handleAnalyzeRadiologyScan()} disabled={scanUploading}>
                      {scanUploading ? "Analyzing..." : "Analyze Narrative"}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {scanUploading && (
              <div className="card" style={{ textAlign: "center", padding: "2.5rem 1rem" }}>
                <div style={{ display: "inline-block", width: "24px", height: "24px", border: "2px solid var(--card-border)", borderTopColor: "var(--accent-primary)", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                <h4 style={{ fontSize: "1rem", marginTop: "0.85rem", color: "var(--text-primary)" }}>Analyzing Radiology Scan Findings...</h4>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                  Classifying incidental vs. actionable observations, analyzing impressions, and identifying acute risks.
                </p>
              </div>
            )}

            {scanErrorMessage && !scanUploading && (
              <div className="card" style={{ borderLeft: "3px solid var(--status-critical-text)", background: "var(--status-critical-bg)", padding: "1rem 1.25rem" }}>
                <p style={{ color: "var(--status-critical-text)", fontSize: "0.86rem", fontWeight: 500 }}>{scanErrorMessage}</p>
              </div>
            )}

            {activeScanResult && !scanUploading && (
              <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {activeScanResult.triage.is_emergency && (
                  <div className="emergency-alert-banner">
                    <h3>Urgent Clinical Finding Detected</h3>
                    <p>{activeScanResult.triage.emergency_message || "Immediate clinical evaluation is advised."}</p>
                  </div>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
                  <div style={{ background: "var(--bg-tertiary)", padding: "0.75rem 1rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--card-border-subtle)" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Modality</span>
                    <p style={{ fontWeight: 600, color: "var(--accent-primary)", fontSize: "0.95rem", marginTop: 2 }}>{activeScanResult.scan_metadata.modality}</p>
                  </div>
                  <div style={{ background: "var(--bg-tertiary)", padding: "0.75rem 1rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--card-border-subtle)" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Anatomical Body Region</span>
                    <p style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.95rem", marginTop: 2 }}>{activeScanResult.scan_metadata.body_region}</p>
                  </div>
                  {activeScanResult.scan_metadata.indication && (
                    <div style={{ background: "var(--bg-tertiary)", padding: "0.75rem 1rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--card-border-subtle)" }}>
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Clinical Indication</span>
                      <p style={{ fontWeight: 500, color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: 2 }}>{activeScanResult.scan_metadata.indication}</p>
                    </div>
                  )}
                </div>

                <div className="summary-panel">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
                    <h3>Plain-Language Summary ({scanLanguage})</h3>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        setChatContextType("scan");
                        setActiveTab("chat");
                      }}
                    >
                      Consult AI Companion
                    </button>
                  </div>
                  <p style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-primary)", marginBottom: "0.75rem" }}>
                    {activeScanResult.triage.summary_headline}
                  </p>
                  <div style={{ background: "var(--bg-secondary)", padding: "0.85rem", borderRadius: "var(--radius-xs)", border: "1px solid var(--card-border-subtle)" }}>
                    <strong style={{ fontSize: "0.82rem", color: "var(--accent-primary)", display: "block", marginBottom: "0.25rem" }}>
                      Radiologist Impression Synthesis:
                    </strong>
                    <span style={{ fontSize: "0.86rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
                      {activeScanResult.radiologist_impression_summary}
                    </span>
                  </div>
                </div>

                {/* Findings-focused cards */}
                <div>
                  <div className="engine-segment-toggle" style={{ marginBottom: "1rem" }}>
                    <button
                      className={`engine-segment-btn ${scanFindingTab === "abnormal" ? "active" : ""}`}
                      onClick={() => setScanFindingTab("abnormal")}
                    >
                      Key Findings ({activeScanResult.findings_breakdown.filter((f) => f.category === "abnormal" || f.category === "urgent").length})
                    </button>
                    <button
                      className={`engine-segment-btn ${scanFindingTab === "incidental" ? "active" : ""}`}
                      onClick={() => setScanFindingTab("incidental")}
                    >
                      Incidental ({activeScanResult.findings_breakdown.filter((f) => f.category === "incidental").length})
                    </button>
                    <button
                      className={`engine-segment-btn ${scanFindingTab === "normal" ? "active" : ""}`}
                      onClick={() => setScanFindingTab("normal")}
                    >
                      Normal / Ruled Out ({activeScanResult.findings_breakdown.filter((f) => f.category === "normal").length})
                    </button>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {scanFindingTab === "abnormal" && (
                      activeScanResult.findings_breakdown.filter((f) => f.category === "abnormal" || f.category === "urgent").length > 0 ? (
                        activeScanResult.findings_breakdown
                          .filter((f) => f.category === "abnormal" || f.category === "urgent")
                          .map((item, idx) => (
                            <div key={idx} style={{ background: "var(--bg-card)", border: "1px solid var(--card-border)", borderLeft: "3px solid var(--status-high-text)", borderRadius: "var(--radius-sm)", padding: "1rem" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                  <span className={`status-badge-pill ${item.category === "urgent" ? "critical" : "high"}`}>
                                    {item.category === "urgent" ? "Urgent" : "Actionable"}
                                  </span>
                                  <strong style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>{item.finding_text}</strong>
                                </div>
                                <button
                                  className="biomarker-desc-toggle"
                                  onClick={() => setExpandedScanFindings((prev) => ({ ...prev, [`ab-${idx}`]: !prev[`ab-${idx}`] }))}
                                >
                                  {expandedScanFindings[`ab-${idx}`] === false ? "View" : "Hide"}
                                </button>
                              </div>
                              {expandedScanFindings[`ab-${idx}`] !== false && (
                                <div style={{ marginTop: "0.5rem", fontSize: "0.82rem", lineHeight: 1.5, color: "var(--text-secondary)" }}>
                                  <p><strong>Plain English:</strong> {item.plain_english_explanation}</p>
                                  <p style={{ color: "var(--accent-primary)", marginTop: "0.2rem" }}>
                                    <strong>Clinical Significance:</strong> {item.clinical_significance}
                                  </p>
                                </div>
                              )}
                            </div>
                          ))
                      ) : (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontStyle: "italic" }}>No abnormal findings detected.</p>
                      )
                    )}

                    {scanFindingTab === "incidental" && (
                      activeScanResult.findings_breakdown.filter((f) => f.category === "incidental").length > 0 ? (
                        activeScanResult.findings_breakdown
                          .filter((f) => f.category === "incidental")
                          .map((item, idx) => (
                            <div key={idx} style={{ background: "var(--bg-tertiary)", border: "1px solid var(--card-border-subtle)", borderRadius: "var(--radius-sm)", padding: "0.85rem 1rem" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                                <span className="status-badge-pill low">Incidental</span>
                                <strong style={{ fontSize: "0.88rem", color: "var(--text-primary)" }}>{item.finding_text}</strong>
                              </div>
                              <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>{item.plain_english_explanation}</p>
                            </div>
                          ))
                      ) : (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontStyle: "italic" }}>No incidental notes noted.</p>
                      )
                    )}

                    {scanFindingTab === "normal" && (
                      activeScanResult.findings_breakdown.filter((f) => f.category === "normal").length > 0 ? (
                        activeScanResult.findings_breakdown
                          .filter((f) => f.category === "normal")
                          .map((item, idx) => (
                            <div key={idx} style={{ background: "var(--bg-tertiary)", border: "1px solid var(--card-border-subtle)", borderRadius: "var(--radius-sm)", padding: "0.75rem 1rem", fontSize: "0.84rem" }}>
                              <span className="status-badge-pill normal" style={{ marginRight: "0.5rem" }}>Normal</span>
                              <strong>{item.finding_text}:</strong> {item.plain_english_explanation}
                            </div>
                          ))
                      ) : (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontStyle: "italic" }}>No specific normal entries recorded.</p>
                      )
                    )}
                  </div>
                </div>

                {activeScanResult.questions_for_doctor && activeScanResult.questions_for_doctor.length > 0 && (
                  <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--card-border-subtle)" }}>
                    <h4 style={{ fontSize: "0.9rem", color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                      Targeted Questions for Your Doctor
                    </h4>
                    <ul style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.35rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                      {activeScanResult.questions_for_doctor.map((q, idx) => (
                        <li key={idx}>{q}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      // ----------------------------------------------------
      // PAGE 3: AI COMPANION (PRESERVED)
      // ----------------------------------------------------
      case "chat":
        return (
          <div className="content-gutter">
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Clinical AI Health Companion</h2>
                <p>Discuss your laboratory test values or imaging scan impressions with deterministic, empathetic clinical assistance.</p>
              </div>
            </div>

            <div className="chat-container-card">
              <div className="chat-header">
                <div>
                  <h3 style={{ fontSize: "0.96rem", fontWeight: 600 }}>AXON Medical Dialogue</h3>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
                    <span style={{ fontSize: "0.75rem", background: "var(--accent-bg-soft)", color: "var(--accent-primary)", padding: "0.15rem 0.5rem", borderRadius: "var(--radius-pill)", fontWeight: 600 }}>
                      {chatContextType === "lab"
                        ? `Lab Context: ${activeLabReport ? activeLabReport.filename : "General (No Report)"}`
                        : `Scan Context: ${activeScanResult ? `${activeScanResult.scan_metadata.modality} (${activeScanResult.scan_metadata.body_region})` : "General (No Scan)"}`}
                    </span>
                    {(activeLabReport || activeScanResult) && (
                      <button
                        className="btn-pill-option"
                        onClick={() => setChatContextType(chatContextType === "lab" ? "scan" : "lab")}
                        style={{ padding: "0.1rem 0.45rem", fontSize: "0.72rem" }}
                      >
                        Switch to {chatContextType === "lab" ? "Scan Context" : "Lab Context"}
                      </button>
                    )}
                  </div>
                </div>

                <select
                  value={selectedTone}
                  onChange={(e) => setSelectedTone(e.target.value)}
                  className="select-input"
                  style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                >
                  <option value="Empathetic">Tone: Empathetic</option>
                  <option value="Clinical">Tone: Clinical</option>
                  <option value="Educational">Tone: Educational</option>
                  <option value="Family">Tone: Family</option>
                </select>
              </div>

              <div className="full-chat-messages">
                {chatHistory.length === 0 ? (
                  <div style={{ margin: "auto", textAlign: "center", color: "var(--text-secondary)", maxWidth: "480px" }}>
                    <h3 style={{ fontSize: "1.1rem", color: "var(--text-primary)", marginBottom: "0.4rem" }}>
                      {chatContextType === "lab" ? "Ask About Your Laboratory Values" : "Ask About Your Radiology Scan"}
                    </h3>
                    <p style={{ fontSize: "0.84rem", color: "var(--text-secondary)" }}>
                      {chatContextType === "lab"
                        ? "Query biomarker normal ranges, out-of-range indicators, or dietary adjustments."
                        : "Query radiologist impression interpretations, abnormal findings, or questions for your doctor."}
                    </p>

                    <div style={{ display: "flex", gap: "0.4rem", justifyContent: "center", flexWrap: "wrap", marginTop: "1rem" }}>
                      {chatContextType === "lab" ? (
                        <>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "Which values are out of range?")}>
                            Which values are out of range?
                          </button>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "What do my abnormal numbers mean?")}>
                            Explain abnormal numbers
                          </button>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "Are there dietary or lifestyle changes to consider?")}>
                            Dietary guidance
                          </button>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "Can you explain my overall summary in simple terms?")}>
                            Explain summary simply
                          </button>
                        </>
                      ) : (
                        <>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "What does this radiologist impression mean?")}>
                            What does this impression mean?
                          </button>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "Are there any urgent or abnormal findings in this scan?")}>
                            Are there abnormal findings?
                          </button>
                          <button className="btn-pill-option" onClick={() => handleSendMessage(undefined, "What questions should I ask my doctor about this scan?")}>
                            Questions for doctor
                          </button>
                        </>
                      )}
                    </div>
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
                    AXON is reviewing clinical data...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {chatDisclaimer && <p className="chat-disclaimer">{chatDisclaimer}</p>}

              <form onSubmit={(e) => handleSendMessage(e)} className="chat-input-form">
                <input
                  type="text"
                  placeholder={
                    chatContextType === "lab"
                      ? "Ask about Hemoglobin, Glucose, Cholesterol, or reference ranges..."
                      : "Ask about scan impression, spine, lungs, or radiologist notes..."
                  }
                  className="chat-input"
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  disabled={chatLoading}
                />
                <button type="submit" className="btn btn-primary btn-sm" disabled={chatLoading}>
                  Send
                </button>
              </form>
            </div>
          </div>
        );

      // ----------------------------------------------------
      // PAGE 4: REPORT HISTORY (PRESERVED)
      // ----------------------------------------------------
      case "history":
        const filteredHistory = reportHistory.filter((r) => {
          if (historyFilter === "lab") return r.report_type !== "scan";
          if (historyFilter === "scan") return r.report_type === "scan";
          return true;
        });

        return (
          <div className="content-gutter">
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Chronological Report History</h2>
                <p>Access your past laboratory and radiology scan document timelines.</p>
              </div>

              <div className="engine-segment-toggle">
                <button
                  className={`engine-segment-btn ${historyFilter === "all" ? "active" : ""}`}
                  onClick={() => setHistoryFilter("all")}
                >
                  All ({reportHistory.length})
                </button>
                <button
                  className={`engine-segment-btn ${historyFilter === "lab" ? "active" : ""}`}
                  onClick={() => setHistoryFilter("lab")}
                >
                  Lab Reports ({historicalLabReports.length})
                </button>
                <button
                  className={`engine-segment-btn ${historyFilter === "scan" ? "active" : ""}`}
                  onClick={() => setHistoryFilter("scan")}
                >
                  Scan Reports ({historicalScanReports.length})
                </button>
              </div>
            </div>

            <div className="history-list">
              {filteredHistory.length === 0 ? (
                <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem", color: "var(--text-secondary)" }}>
                  <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Stored Reports</p>
                  <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                    Upload a report on either the Lab Reports or Scan Reports page to build your health record.
                  </span>
                </div>
              ) : (
                filteredHistory.map((report) => {
                  const isScan = report.report_type === "scan";
                  const isActive = isScan ? activeScanResult?.id === report.id : activeLabReport?.id === report.id;

                  return (
                    <div
                      className={`history-card-item ${isActive ? "active" : ""}`}
                      key={report.id}
                      onClick={() => {
                        if (isScan && report.scan_data) {
                          setActiveScanResult(report.scan_data);
                          setChatContextType("scan");
                          setActiveTab("scan-reports");
                        } else {
                          setActiveLabReport(report);
                          setChatContextType("lab");
                          setActiveTab("lab-reports");
                        }
                      }}
                    >
                      <div className="history-meta">
                        <h3>{report.filename}</h3>
                        <p>{report.date} • {isScan ? "Radiology Scan Report" : "Laboratory Biomarker Report"}</p>
                      </div>

                      <div className="history-stats">
                        {isScan ? (
                          <span className="status-badge-pill" style={{ background: "var(--bg-tertiary)" }}>
                            Radiology
                          </span>
                        ) : (
                          <>
                            <span className="status-badge-pill normal">
                              Normal: {report.normal_count}
                            </span>
                            <span className="status-badge-pill high">
                              Abnormal: {report.abnormal_count}
                            </span>
                          </>
                        )}
                        <span className="btn btn-ghost btn-sm">Open</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );

      // ----------------------------------------------------
      // PAGE 5: HEALTH TRENDS (PRESERVED)
      // ----------------------------------------------------
      case "trends":
        return (
          <div className="content-gutter">
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Health Trends & Longitudinal Delta</h2>
                <p>Track biological values across historical test uploads to visualize trends.</p>
              </div>
            </div>

            <div className="chart-container-card">
              <div className="chart-header">
                <div>
                  <h3 style={{ fontSize: "0.98rem", fontWeight: 600 }}>Biomarker Chronological Graph</h3>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Plotting longitudinal data across recorded lab panels</span>
                </div>
                {availableBiomarkers.length > 0 ? (
                  <select
                    value={selectedTrendBiomarker}
                    onChange={(e) => setSelectedTrendBiomarker(e.target.value)}
                    className="select-input"
                  >
                    {availableBiomarkers.map((name, i) => (
                      <option key={i} value={name}>{name}</option>
                    ))}
                  </select>
                ) : null}
              </div>
              {renderTrendChart()}
            </div>
          </div>
        );

      // ----------------------------------------------------
      // PAGE 6: SETTINGS (PRESERVED)
      // ----------------------------------------------------
      case "settings":
        return (
          <div className="content-gutter">
            <div className="page-intro">
              <div className="page-intro-titles">
                <h2>Settings & Preferences</h2>
                <p>Configure theme interface, Google Gemini API parameters, and patient biological profile.</p>
              </div>
            </div>

            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div>
                <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.6rem" }}>Theme Appearance</h4>
                <div style={{ display: "flex", gap: "0.75rem" }}>
                  <button
                    className={`btn ${theme === "light" ? "btn-primary" : "btn-secondary"} btn-sm`}
                    onClick={() => toggleTheme("light")}
                  >
                    Light Theme
                  </button>
                  <button
                    className={`btn ${theme === "dark" ? "btn-primary" : "btn-secondary"} btn-sm`}
                    onClick={() => toggleTheme("dark")}
                  >
                    Dark Theme
                  </button>
                </div>
              </div>

              <div style={{ borderTop: "1px solid var(--card-border-subtle)", paddingTop: "1rem" }}>
                <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.6rem" }}>Gemini API Key (Optional)</h4>
                <div style={{ maxWidth: "480px" }}>
                  <input
                    type="password"
                    value={geminiApiKey}
                    onChange={(e) => {
                      setGeminiApiKey(e.target.value);
                      localStorage.setItem("axon_gemini_api_key", e.target.value);
                    }}
                    placeholder="AIzaSy..."
                    className="chat-input"
                    style={{ width: "100%", fontFamily: "monospace" }}
                  />
                  <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
                    Stored locally in your browser. Enables cloud vision analysis and multilingual conversational depth.
                  </p>
                </div>
              </div>

              {token ? (
                <div style={{ borderTop: "1px solid var(--card-border-subtle)", paddingTop: "1rem" }}>
                  <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>Patient Biological Profile</h4>
                  <form onSubmit={handleProfileSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.85rem", maxWidth: "480px" }}>
                    <div className="input-group">
                      <label>Full Patient Name</label>
                      <input
                        type="text"
                        required
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm((prev) => ({ ...prev, full_name: e.target.value }))}
                      />
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                      <div className="input-group">
                        <label>Age</label>
                        <input
                          type="number"
                          required
                          value={profileForm.age}
                          onChange={(e) => setProfileForm((prev) => ({ ...prev, age: parseInt(e.target.value) || 0 }))}
                        />
                      </div>
                      <div className="input-group">
                        <label>Biological Sex</label>
                        <select
                          value={profileForm.biological_sex}
                          onChange={(e) => setProfileForm((prev) => ({ ...prev, biological_sex: e.target.value }))}
                        >
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                    </div>
                    <button type="submit" className="btn btn-primary btn-sm" style={{ alignSelf: "flex-start" }}>
                      Save Parameters
                    </button>
                  </form>
                </div>
              ) : (
                <div style={{ borderTop: "1px solid var(--card-border-subtle)", paddingTop: "1rem" }}>
                  <p style={{ fontSize: "0.84rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                    Sign in to associate biological parameters with your account.
                  </p>
                  <button className="btn btn-primary btn-sm" onClick={() => { setAuthMode("login"); setIsAuthOpen(true); }}>
                    Sign In
                  </button>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Auth gate if user not signed in and hasn't selected guest
  if (!token && !isGuest) {
    return (
      <div className="auth-page-wrapper">
        <div className="auth-container">
          <div className="auth-hero-panel">
            <div className="auth-hero-top">
              <div className="brand-emblem" style={{ width: "32px", height: "32px", background: "#FFFFFF", color: "var(--accent-deep)" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2v20M2 12h20" />
                </svg>
              </div>
              <div style={{ fontWeight: 700, fontSize: "1.05rem", letterSpacing: "0.05em" }}>AXON</div>
            </div>
            <div className="auth-hero-body">
              <h2>Clinical Intelligence with Clarity.</h2>
              <p>
                De-identifies patient information, normalizes complex clinical biomarkers, evaluates emergency thresholds, and synthesizes clear medical explanations.
              </p>
            </div>
            <div className="auth-hero-footer">
              AXON Clinical Architecture · Offline First
            </div>
          </div>

          <div className="auth-form-card">
            <h2>{authMode === "login" ? "Sign In" : "Register Profile"}</h2>
            <p>{authMode === "login" ? "Enter your clinical credentials" : "Create an account for longitudinal tracking"}</p>

            <form onSubmit={handleAuthSubmit}>
              <div className="input-group">
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="clinician@example.com"
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
              {labErrorMessage && (
                <p style={{ color: "var(--status-critical-text)", fontSize: "0.82rem", marginBottom: "0.75rem", fontWeight: 500 }}>
                  {labErrorMessage}
                </p>
              )}
              <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>
                {authMode === "login" ? "Sign In" : "Create Account"}
              </button>

              <div className="auth-toggle">
                {authMode === "login" ? (
                  <>
                    No account?{" "}
                    <button type="button" onClick={() => { setAuthMode("register"); setLabErrorMessage(null); }}>Sign Up</button>
                  </>
                ) : (
                  <>
                    Have an account?{" "}
                    <button type="button" onClick={() => { setAuthMode("login"); setLabErrorMessage(null); }}>Sign In</button>
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
                setLabErrorMessage(null);
              }}
            >
              Continue in Demonstration Mode
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`app-wrapper ${!isSidebarOpen ? "sidebar-closed" : ""}`}>
      {/* SIDEBAR NAVIGATION SHELL */}
      <aside className="sidebar">
        <div className="sidebar-header">
          {/* Refined Brand Emblem */}
          <div className="brand-section">
            <div className="brand-emblem">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2v20M2 12h20" />
              </svg>
            </div>
            <div className="brand-text">
              <h1>AXON</h1>
              <p>Clinical Intelligence</p>
            </div>
          </div>

          {/* Clean Medical Navigation with Consistent SVGs */}
          <nav className="sidebar-nav">
            <button
              className={`sidebar-nav-item ${activeTab === "lab-reports" ? "active" : ""}`}
              onClick={() => handleTabChange("lab-reports")}
              id="nav-lab-reports"
            >
              <span className="sidebar-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10 2v7.31L4.15 19.3A2 2 0 0 0 5.86 22h12.28a2 2 0 0 0 1.71-2.7L14 9.31V2" />
                  <line x1="8" y1="2" x2="16" y2="2" />
                  <line x1="7" y1="16" x2="17" y2="16" />
                </svg>
              </span>
              <span>Lab Reports</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "scan-reports" ? "active" : ""}`}
              onClick={() => handleTabChange("scan-reports")}
              id="nav-scan-reports"
            >
              <span className="sidebar-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <path d="M7 7h10M7 12h10M7 17h6" />
                </svg>
              </span>
              <span>Scan Reports</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => handleTabChange("chat")}
              id="nav-ai-companion"
            >
              <span className="sidebar-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </span>
              <span>AI Companion</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "history" ? "active" : ""}`}
              onClick={() => handleTabChange("history")}
              id="nav-report-history"
            >
              <span className="sidebar-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
              </span>
              <span>Report History</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === "trends" ? "active" : ""}`}
              onClick={() => handleTabChange("trends")}
              id="nav-health-trends"
            >
              <span className="sidebar-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </span>
              <span>Health Trends</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          {token ? (
            <>
              <div className="sidebar-profile">
                <div className="sidebar-profile-avatar">{userEmail ? userEmail[0].toUpperCase() : "P"}</div>
                <div className="sidebar-profile-info">
                  <span className="sidebar-profile-name">{userProfile?.full_name || userEmail}</span>
                  <span className="sidebar-profile-role">Registered Patient</span>
                </div>
              </div>
              <button
                className={`sidebar-nav-item ${activeTab === "settings" ? "active" : ""}`}
                onClick={() => handleTabChange("settings")}
              >
                <span className="sidebar-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                </span>
                <span>Settings</span>
              </button>
              <button className="sidebar-nav-item" onClick={handleLogout} style={{ color: "var(--status-critical-text)" }}>
                <span className="sidebar-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                </span>
                <span>Sign Out</span>
              </button>
            </>
          ) : (
            <>
              <button
                className={`sidebar-nav-item ${activeTab === "settings" ? "active" : ""}`}
                onClick={() => handleTabChange("settings")}
              >
                <span className="sidebar-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                </span>
                <span>Settings</span>
              </button>
              <button
                className="btn btn-primary"
                style={{ width: "100%" }}
                onClick={() => {
                  setAuthMode("login");
                  setIsAuthOpen(true);
                }}
              >
                Sign In
              </button>
            </>
          )}
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="main-content">
        {/* Top Header Bar */}
        <div className="top-bar">
          <div className="top-bar-title">
            <button className="menu-toggle-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)} aria-label="Toggle Navigation Sidebar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <span>AXON Clinical Console</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              className="theme-toggle-btn"
              onClick={() => toggleTheme(theme === "light" ? "dark" : "light")}
              title="Toggle Light / Dark Mode"
            >
              {theme === "light" ? (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                  </svg>
                  <span>Dark</span>
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="5" />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                  </svg>
                  <span>Light</span>
                </>
              )}
            </button>
          </div>
        </div>

        {renderActiveView()}
      </main>

      {/* CAMERA SCANNER MODAL */}
      {isCameraActive && (
        <div className="scanner-overlay">
          <div className="scanner-container">
            <div className="scanner-header">
              <h3 style={{ fontSize: "0.95rem", fontWeight: 600 }}>
                {cameraTarget === "lab" ? "Photograph Laboratory Document" : "Photograph Radiology Lightbox"}
              </h3>
              <button
                className="modal-close-btn"
                style={{ position: "static" }}
                onClick={stopCamera}
                aria-label="Close Scanner"
              >
                ×
              </button>
            </div>
            <div className="scanner-view-wrapper">
              <video ref={videoRef} autoPlay playsInline muted className="scanner-viewport" />
              <div className="scanner-guidelines">
                <span>Align document evenly within frame</span>
                <span>Ensure steady, glare-free lighting</span>
              </div>
            </div>
            <div className="scanner-footer">
              <button className="btn btn-ghost btn-sm" onClick={stopCamera}>
                Cancel
              </button>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-secondary btn-sm" onClick={toggleFacingMode}>
                  Switch Camera
                </button>
                <button className="btn btn-primary btn-sm" onClick={capturePhoto}>
                  Capture Document
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AUTH MODAL */}
      {isAuthOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close-btn" onClick={() => setIsAuthOpen(false)}>
              ×
            </button>
            <div className="modal-header">
              <h2>{authMode === "login" ? "Sign In" : "Register Profile"}</h2>
              <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
                {authMode === "login" ? "Access your historical medical reports" : "Create an account for longitudinal tracking"}
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
                  placeholder="clinician@example.com"
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
              {labErrorMessage && (
                <p style={{ color: "var(--status-critical-text)", fontSize: "0.82rem", marginBottom: "0.75rem", fontWeight: 500 }}>
                  {labErrorMessage}
                </p>
              )}
              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.25rem" }}>
                {authMode === "login" ? "Sign In" : "Create Account"}
              </button>

              <div className="auth-toggle">
                {authMode === "login" ? (
                  <>
                    No account?{" "}
                    <button type="button" onClick={() => { setAuthMode("register"); setLabErrorMessage(null); }}>Sign Up</button>
                  </>
                ) : (
                  <>
                    Have an account?{" "}
                    <button type="button" onClick={() => { setAuthMode("login"); setLabErrorMessage(null); }}>Sign In</button>
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
