# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Home & Navigation Page Object
Maps brand elements, navigation items, layout controls, and engine toggles.
"""

from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class HomePage(BasePage):
    # Brand Locators
    BRAND_HEADER = (By.CSS_SELECTOR, ".brand-text h1")
    BRAND_TAGLINE = (By.CSS_SELECTOR, ".brand-text p")
    BRAND_EMBLEM = (By.CSS_SELECTOR, ".brand-emblem")
    
    # Navigation Buttons
    NAV_LAB_REPORTS = (By.ID, "nav-lab-reports")
    NAV_SCAN_REPORTS = (By.ID, "nav-scan-reports")
    NAV_AI_COMPANION = (By.ID, "nav-ai-companion")
    NAV_REPORT_HISTORY = (By.ID, "nav-report-history")
    NAV_HEALTH_TRENDS = (By.ID, "nav-health-trends")
    
    # Engine & Status Toggles
    ENGINE_STATUS_BAR = (By.CSS_SELECTOR, ".engine-status-bar")
    LOCAL_MODE_BTN = (By.XPATH, "//button[contains(text(), 'Local Mode')]")
    CLOUD_AI_BTN = (By.XPATH, "//button[contains(text(), 'Cloud AI')]")
    
    # Layout Elements
    APP_WRAPPER = (By.CSS_SELECTOR, ".app-wrapper")
    SIDEBAR = (By.CSS_SELECTOR, ".sidebar")
    CONTENT_AREA = (By.CSS_SELECTOR, ".main-content, .content-gutter")
    
    # Sample Actions
    SAMPLE_LAB_BTN = (By.XPATH, "//button[contains(text(), 'Load Sample') or contains(@class, 'btn-ghost')]")
    LOGOUT_BTN = (By.XPATH, "//button[contains(text(), 'Sign Out') or contains(text(), 'Logout')]")

    def get_brand_title(self) -> str:
        return self.get_text(self.BRAND_HEADER)

    def navigate_to_tab(self, tab_name: str) -> None:
        tab_map = {
            "lab": self.NAV_LAB_REPORTS,
            "scan": self.NAV_SCAN_REPORTS,
            "chat": self.NAV_AI_COMPANION,
            "history": self.NAV_REPORT_HISTORY,
            "trends": self.NAV_HEALTH_TRENDS
        }
        locator = tab_map.get(tab_name.lower())
        if locator and self.is_displayed(locator, timeout=0):
            try:
                self.click(locator, timeout=1)
                self.wait_for_page_ready(1)
            except Exception:
                pass

    def set_engine_mode(self, mode: str) -> None:
        if mode.lower() == "cloud":
            if self.is_displayed(self.CLOUD_AI_BTN, timeout=0):
                self.click(self.CLOUD_AI_BTN, timeout=1)
        else:
            if self.is_displayed(self.LOCAL_MODE_BTN, timeout=0):
                self.click(self.LOCAL_MODE_BTN, timeout=1)
