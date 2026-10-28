# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Upload Page Object
Handles PDF/text report upload, document picker interaction, and analysis trigger.
"""

from typing import Any
from automation.pages.mobile_base_page import MobileBasePage

class MobileUploadPage(MobileBasePage):
    """Page object for Mobile Report Upload & Scan Analysis screen."""

    FILE_PICKER_BTN = ("xpath", "//android.widget.TextView[contains(@text, 'Select File') or contains(@text, 'Browse')]")
    CAMERA_PICKER_BTN = ("xpath", "//android.widget.TextView[contains(@text, 'Take Photo') or contains(@text, 'Camera')]")
    PASTE_TEXT_TAB = ("xpath", "//android.widget.TextView[contains(@text, 'Paste Text') or contains(@text, 'Manual Input')]")
    TEXT_INPUT_AREA = ("xpath", "//android.widget.EditText[contains(@content-desc, 'report-text') or contains(@text, 'Paste')]")
    ANALYZE_BTN = ("xpath", "//android.widget.TextView[@text='Analyze Report' or contains(@text, 'Process')]")
    PROCESSING_INDICATOR = ("xpath", "//android.widget.ProgressBar or //android.widget.TextView[contains(@text, 'Analyzing')]")
    RESULTS_CONTAINER = ("xpath", "//android.widget.TextView[contains(@text, 'Analysis Results') or contains(@text, 'Biomarkers')]")
    FLAGGED_BADGE = ("xpath", "//android.widget.TextView[contains(@text, 'HIGH') or contains(@text, 'LOW') or contains(@text, 'CRITICAL')]")

    def upload_sample_text_report(self, report_text: str) -> bool:
        """Paste clinical report text and trigger analysis."""
        self.click(*self.PASTE_TEXT_TAB)
        self.enter_text(*self.TEXT_INPUT_AREA, report_text)
        return self.click(*self.ANALYZE_BTN)

    def trigger_file_picker(self) -> bool:
        """Tap system document picker."""
        return self.click(*self.FILE_PICKER_BTN)

    def is_analysis_complete(self, timeout: int = 15) -> bool:
        """Wait for analysis results container to appear."""
        return self.is_visible(*self.RESULTS_CONTAINER, timeout=timeout)
