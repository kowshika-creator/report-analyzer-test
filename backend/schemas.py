from pydantic import BaseModel
from typing import List, Optional

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
    value: float
    unit: str
    min_normal: float
    max_normal: float
    status: str  # "Low", "High", "Normal"
    confidence: float = 0.95  # e.g., 0.95 = 95% confidence
    is_low_confidence: bool = False  # True if confidence < 0.80
    is_critical: bool = False  # True if value hits panic threshold
    critical_reason: Optional[str] = None
    description: Optional[str] = None

class AnalysisResponse(BaseModel):
    filename: str
    status: str
    metrics: List[MetricAnalysis]
    disease_risks: List[str] = []
    has_critical_alert: bool = False
    critical_alerts: List[str] = []
    patient_summary: str = ""
    language: str = "English"
    is_mock_fallback: Optional[bool] = False

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
