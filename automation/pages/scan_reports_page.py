# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Radiology Scan Reports Page Object
Maps radiology text upload, imaging viewer, findings triage, and questions for doctor.
"""

from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class ScanReportsPage(BasePage):
    SCAN_HEADING = (By.XPATH, "//h2[contains(text(), 'Radiology') or contains(text(), 'Scan')]")
    REPORT_TEXTAREA = (By.CSS_SELECTOR, "textarea[placeholder*='findings'], textarea[placeholder*='radiology']")
    ANALYZE_SCAN_BTN = (By.XPATH, "//button[contains(text(), 'Analyze Scan') or contains(text(), 'Evaluate Scan')]")
    SAMPLE_MRI_BTN = (By.XPATH, "//button[contains(text(), 'Sample MRI')]")
    SAMPLE_XRAY_BTN = (By.XPATH, "//button[contains(text(), 'Sample Chest X-Ray')]")
    IMPRESSION_BOX = (By.CSS_SELECTOR, ".radiologist-impression-box, .scan-impression")
    FINDINGS_LIST = (By.CSS_SELECTOR, ".finding-item, .findings-card")

    def is_scan_view_active(self) -> bool:
        return self.is_displayed(self.SCAN_HEADING, timeout=3)

    def load_sample_mri(self) -> None:
        if self.is_displayed(self.SAMPLE_MRI_BTN, timeout=3):
            self.click(self.SAMPLE_MRI_BTN)
            self.wait_for_page_ready()

    def analyze_scan(self) -> None:
        if self.is_displayed(self.ANALYZE_SCAN_BTN, timeout=3):
            self.click(self.ANALYZE_SCAN_BTN)
            self.wait_for_page_ready()
