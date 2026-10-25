from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ReferenceRangeBase(BaseModel):
    biomarker_name: str
    alias_names: Optional[str] = None
    min_normal: float
    max_normal: float
    unit: str
    panel_name: str
    description: Optional[str] = None

class ReferenceRangeCreate(ReferenceRangeBase):
    pass

class ReferenceRangeResponse(ReferenceRangeBase):
    id: int

    class Config:
        from_attributes = True

class MetricAnalysis(BaseModel):
    biomarker_name: str
    value: Optional[float] = None
    unit: str
    min_normal: Optional[float] = None
    max_normal: Optional[float] = None
    status: str  # "Low", "High", "Normal", "Unreviewed", "Unparseable"
    confidence: float = 0.95  # e.g., 0.95 = 95% confidence
    is_low_confidence: bool = False  # True if confidence < 0.80
    is_critical: bool = False  # True if value hits panic threshold
    critical_reason: Optional[str] = None
    description: Optional[str] = None
    reference_source: Optional[str] = "AXON Local Database"  # "Lab Report", "AXON Local Database", "Standard Clinical Guidelines"
    panel_category: Optional[str] = "General Clinical Metric"

    # Priority 2: Structured Unit Traceability
    source_value: Optional[float] = None
    source_unit: Optional[str] = None
    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None
    conversion_method: Optional[str] = None
    requires_review: bool = False

class ExplainableRuleResult(BaseModel):
    rule_id: str
    title: str
    input_param: str
    input_value: Optional[float] = None
    unit: str
    reference_range: str
    result_status: str
    explanation: str
    doctor_discussion_points: List[str] = []

class AnalysisResponse(BaseModel):
    filename: str
    status: str
    metrics: List[MetricAnalysis]
    disease_risks: List[str] = []
    has_critical_alert: bool = False
    critical_alerts: List[str] = []
    patient_summary: str = ""
    language: str = "English"
    analysis_mode: Optional[str] = "local"  # "local" or "cloud_enhanced"
    engine_info: Optional[str] = "AXON Explainable Clinical Engine (Local)"
    explainable_rules: List[ExplainableRuleResult] = []
    is_mock_fallback: Optional[bool] = False
    suggested_page: Optional[str] = None

# Longitudinal Trend Analysis Schemas
class BiomarkerDelta(BaseModel):
    biomarker_name: str
    baseline_value: float
    current_value: float
    delta_value: float
    percentage_change: float
    unit: str
    direction: str  # "improved", "worsened", "stable"
    insight_text: str

class TrendComparisonRequest(BaseModel):
    baseline_report_id: int
    current_report_id: int

class TrendComparisonResponse(BaseModel):
    baseline_date: str
    current_date: str
    deltas: List[BiomarkerDelta]
    longitudinal_summary: str

# Clinical Imaging & Radiology Scan Report Data Contract
class FindingItem(BaseModel):
    finding_text: str = Field(description="Exact excerpt from the report.")
    category: Literal["normal", "incidental", "abnormal", "urgent"] = Field(
        description="Classification of the finding."
    )
    plain_english_explanation: str = Field(
        description="Clear, reassuring explanation for a patient."
    )
    clinical_significance: str = Field(
        description="What this typically implies for treatment or follow-up."
    )

class ScanMetadata(BaseModel):
    modality: str = Field(description="e.g., MRI, CT, Ultrasound, X-Ray")
    body_region: str = Field(description="e.g., Lumbar Spine, Chest, Abdomen")
    indication: Optional[str] = Field(None, description="Reason for scan")
    technique_notes: Optional[str] = Field(None, description="Contrast/sequences used")

class TriageInfo(BaseModel):
    is_emergency: bool = Field(description="True ONLY if acute life threat is detected")
    emergency_message: Optional[str] = Field(None, description="Immediate care instructions if urgent")
    summary_headline: str = Field(description="1-2 sentence overall summary for the patient")

class ScanReportAnalysis(BaseModel):
    id: Optional[str] = None
    filename: Optional[str] = "Radiology_Scan_Report"
    upload_date: Optional[str] = None
    report_type: Optional[str] = "scan"
    scan_metadata: ScanMetadata
    triage: TriageInfo
    findings_breakdown: List[FindingItem]
    radiologist_impression_summary: str
    questions_for_doctor: List[str]
    suggested_page: Optional[str] = None

# Chat schemas for follow-up medical queries
class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    chat_history: List[ChatMessage] = []
    current_message: str
    extracted_metrics: List[MetricAnalysis] = []
    selected_tone: Optional[str] = "Empathetic"
    language: Optional[str] = "English"
    report_type: Optional[str] = "lab"  # "lab" or "scan"
    scan_context: Optional[ScanReportAnalysis] = None

class ChatResponse(BaseModel):
    response: str
    disclaimer: str

class ProfileUpdateSchema(BaseModel):
    full_name: str
    age: int
    biological_sex: str
    weight_kg: float
    height_cm: float
    chronic_conditions: List[str] = []
    primary_health_goal: str

