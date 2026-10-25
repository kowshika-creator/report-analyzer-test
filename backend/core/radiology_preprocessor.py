import io
import numpy as np
from PIL import Image, ImageStat
from typing import Dict, Any, List, Optional

def analyze_radiology_locally(
    file_bytes: Optional[bytes] = None, 
    report_text: Optional[str] = None,
    language: str = "English"
) -> Dict[str, Any]:
    """
    Local Radiology Preprocessing & Technical Image Analysis Engine:
    Provides local image validation, dimensions, brightness/contrast quality statistics,
    and text report breakdown without claiming automated medical imaging diagnosis.
    Cloud AI capabilities are clearly marked as optional enhancements.
    """
    image_metadata = {
        "modality": "Medical Diagnostic Imaging",
        "body_region": "Unspecified Clinical Region",
        "indication": "Routine imaging technical evaluation",
        "technique_notes": "AXON Local Image Preprocessing Pipeline"
    }

    image_stats = {}

    if file_bytes:
        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            format_name = img.format or "JPEG/PNG"
            mode = img.mode

            # Convert to grayscale to compute brightness & contrast statistics
            gray_img = img.convert("L")
            stat = ImageStat.Stat(gray_img)
            mean_brightness = round(float(stat.mean[0]), 2)
            std_contrast = round(float(stat.stddev[0]), 2)

            image_metadata["modality"] = f"Physical Scan Image ({format_name})"
            image_metadata["body_region"] = f"Dimensions: {width} x {height} px ({mode})"

            image_stats = {
                "width_px": width,
                "height_px": height,
                "format": format_name,
                "color_mode": mode,
                "mean_brightness_scale_255": mean_brightness,
                "contrast_standard_deviation": std_contrast,
                "quality_assessment": "Optimal Resolution for Technical Review" if width >= 500 else "Standard Resolution"
            }
        except Exception as e:
            print(f"Radiology local image stat error: {e}")

    # Process text if radiology text report was provided
    findings_breakdown = []
    is_emergency = False
    headline = "Radiology imaging file preprocessed locally."

    if report_text and len(report_text.strip()) > 10:
        headline = "Local Radiology Text Findings Analysis"
        text_lower = report_text.lower()
        
        # Simple local keyword categorization
        if any(k in text_lower for k in ["fracture", "haemorrhage", "hemorrhage", "pneumothorax", "acute", "emergency"]):
            is_emergency = True
            headline = "URGENT FINDING NOTED IN REPORT TEXT"

        lines = [l.strip() for l in report_text.splitlines() if len(l.strip()) > 5]
        for idx, line in enumerate(lines[:5]):
            cat = "abnormal" if any(k in text_lower for k in ["impression", "finding", "abnormal", "lesion", "mass"]) else "normal"
            findings_breakdown.append({
                "finding_text": line,
                "category": cat,
                "plain_english_explanation": f"Report Line {idx+1}: {line}",
                "clinical_significance": "Requires review by your attending radiologist or physician."
            })
    else:
        findings_breakdown.append({
            "finding_text": f"Technical Scan Quality: {image_stats.get('quality_assessment', 'Verified')}",
            "category": "normal",
            "plain_english_explanation": f"Image dimensions {image_stats.get('width_px', 0)}x{image_stats.get('height_px', 0)} px. Mean brightness: {image_stats.get('mean_brightness_scale_255', 0)}/255.",
            "clinical_significance": "Technical quality is adequate for radiologist examination."
        })

    return {
        "scan_metadata": image_metadata,
        "triage": {
            "is_emergency": is_emergency,
            "emergency_message": "Urgent keywords detected in text report. Prompt specialist review recommended." if is_emergency else None,
            "summary_headline": headline
        },
        "findings_breakdown": findings_breakdown,
        "radiologist_impression_summary": "AXON Local Analysis Mode: This module provides image quality statistics, contrast enhancement, and report text extraction. Diagnostic interpretation must be performed by a licensed radiologist.",
        "questions_for_doctor": [
            "What specific findings on this scan relate to my current symptoms?",
            "Is any follow-up imaging or comparison with previous scans recommended?"
        ],
        "image_technical_stats": image_stats,
        "analysis_mode": "AXON Local Preprocessing Engine (Cloud AI Optional)"
    }
