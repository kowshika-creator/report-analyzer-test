# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Report Upload Page Object
Maps file dropzone, file input, sample preloader, language selectors, and analyze trigger.
"""

from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class ReportUploadPage(BasePage):
    # Upload & Dropzone Locators
    DROPZONE_CONTAINER = (By.CSS_SELECTOR, ".upload-dropzone, .dropzone-area, .file-uploader")
    FILE_INPUT = (By.CSS_SELECTOR, "input[type='file']")
    UPLOAD_TRIGGER_BTN = (By.XPATH, "//button[contains(text(), 'Select Report') or contains(text(), 'Choose File') or contains(text(), 'Upload')]")
    SAMPLE_REPORT_BTN = (By.XPATH, "//button[contains(text(), 'Sample Report') or contains(text(), 'Demo Data')]")
    ANALYZE_BTN = (By.XPATH, "//button[contains(text(), 'Analyze') or contains(text(), 'Run Analysis')]")
    
    # Progress & Alerts
    PROGRESS_BAR = (By.CSS_SELECTOR, ".progress-bar, .loading-spinner, .analyzing-indicator")
    MISMATCH_BANNER = (By.CSS_SELECTOR, ".mismatch-alert-banner")
    LANGUAGE_SELECT = (By.CSS_SELECTOR, "select.select-input, select[name='language']")

    def upload_file(self, absolute_file_path: str) -> None:
        file_input = self.find(self.FILE_INPUT)
        file_input.send_keys(absolute_file_path)
        self.wait_for_page_ready()

    def load_sample_report(self) -> None:
        if self.is_displayed(self.SAMPLE_REPORT_BTN, timeout=3):
            self.click(self.SAMPLE_REPORT_BTN)
            self.wait_for_page_ready()

    def select_language(self, language: str) -> None:
        if self.is_displayed(self.LANGUAGE_SELECT, timeout=2):
            elem = self.find(self.LANGUAGE_SELECT)
            for option in elem.find_elements(By.TAG_NAME, "option"):
                if option.text.strip().lower() == language.lower():
                    option.click()
                    break

    def is_mismatch_banner_visible(self) -> bool:
        return self.is_displayed(self.MISMATCH_BANNER, timeout=3)
