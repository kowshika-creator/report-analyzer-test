"""
AXON Core Intelligent Medical Analysis Engine (Local-First)
Includes standalone local modules for document OCR, medical report parsing, reference range comparison,
explainable clinical rule evaluation, risk pattern detection, emergency panic threshold checks,
patient simplification, longitudinal trend analysis, radiology image preprocessing, and local chatbot knowledge query.
"""

from .local_ocr import extract_text_locally
from .medical_parser import parse_medical_report_text
from .reference_engine import evaluate_reference_ranges
from .emergency_engine import check_emergency_thresholds
from .risk_engine import evaluate_disease_risk_patterns
from .rule_engine import run_explainable_rule_engine
from .patient_simplifier import generate_patient_summary_local
from .trend_engine import compare_longitudinal_trends
from .radiology_preprocessor import analyze_radiology_locally
from .local_chatbot import generate_local_chatbot_response

__all__ = [
    "extract_text_locally",
    "parse_medical_report_text",
    "evaluate_reference_ranges",
    "check_emergency_thresholds",
    "evaluate_disease_risk_patterns",
    "run_explainable_rule_engine",
    "generate_patient_summary_local",
    "compare_longitudinal_trends",
    "analyze_radiology_locally",
    "generate_local_chatbot_response",
]
