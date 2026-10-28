# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Clinical Results Page Object
Maps biomarker tables, panic alert banners, disease risk indicators, and PDF export.
"""

from typing import List, Dict
from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class ResultsPage(BasePage):
    # Results View Locators
    RESULTS_CONTAINER = (By.CSS_SELECTOR, ".results-container, .analysis-dashboard, .biomarker-table-wrapper")
    CRITICAL_ALERT_BANNER = (By.CSS_SELECTOR, ".panic-alert, .critical-alert-banner, [class*='critical']")
    BIOMARKER_ROWS = (By.CSS_SELECTOR, "table tbody tr, .metric-row, .biomarker-card")
    DISEASE_RISK_CARDS = (By.CSS_SELECTOR, ".risk-card, .disease-pattern-pill, [class*='risk']")
    PATIENT_SUMMARY_BOX = (By.CSS_SELECTOR, ".patient-summary-box, .simplified-narrative")
    EXPORT_PDF_BTN = (By.XPATH, "//button[contains(text(), 'Export PDF') or contains(text(), 'Download Summary')]")
    EXPLAINABLE_RULES_SECTION = (By.CSS_SELECTOR, ".rules-container, .clinical-logic-breakdown")

    def has_critical_alert(self) -> bool:
        return self.is_displayed(self.CRITICAL_ALERT_BANNER, timeout=3)

    def get_patient_summary_text(self) -> str:
        if self.is_displayed(self.PATIENT_SUMMARY_BOX, timeout=3):
            return self.get_text(self.PATIENT_SUMMARY_BOX)
        return ""

    def get_biomarker_count(self) -> int:
        return len(self.find_all(self.BIOMARKER_ROWS, timeout=3))

    def get_risk_pattern_count(self) -> int:
        return len(self.find_all(self.DISEASE_RISK_CARDS, timeout=3))

    def click_export_pdf(self) -> None:
        if self.is_displayed(self.EXPORT_PDF_BTN, timeout=3):
            self.click(self.EXPORT_PDF_BTN)
