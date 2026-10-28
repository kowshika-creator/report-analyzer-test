# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Dashboard Page Object
Handles home screen cards, navigation tabs, biomarker overview, and search.
"""

from typing import Any
from automation.pages.mobile_base_page import MobileBasePage

class MobileDashboardPage(MobileBasePage):
    """Page object for Mobile Clinical Dashboard & Navigation."""

    # Selectors
    HEADER_TITLE = ("xpath", "//android.widget.TextView[contains(@text, 'Clinical Dashboard') or contains(@text, 'Overview')]")
    SEARCH_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'search') or contains(@text, 'Search')]")
    UPLOAD_CARD = ("xpath", "//android.widget.TextView[contains(@text, 'Upload Report') or contains(@text, 'Analyze Report')]")
    SCAN_CARD = ("xpath", "//android.widget.TextView[contains(@text, 'Radiology') or contains(@text, 'Scan')]")
    CHAT_TAB = ("xpath", "//android.widget.TextView[contains(@text, 'Chat') or contains(@text, 'Companion')]")
    PROFILE_TAB = ("xpath", "//android.widget.TextView[contains(@text, 'Profile') or contains(@text, 'Settings')]")
    HISTORY_TAB = ("xpath", "//android.widget.TextView[contains(@text, 'History') or contains(@text, 'Reports')]")
    METRICS_WIDGET = ("xpath", "//android.widget.TextView[contains(@text, 'Biomarkers') or contains(@text, 'Metrics')]")

    def is_dashboard_loaded(self) -> bool:
        """Verify dashboard header or cards are visible."""
        return self.is_visible(*self.HEADER_TITLE) or self.is_visible(*self.UPLOAD_CARD)

    def navigate_to_upload(self) -> bool:
        """Navigate to report upload screen."""
        return self.click(*self.UPLOAD_CARD)

    def navigate_to_chat(self) -> bool:
        """Navigate to AI companion chat screen."""
        return self.click(*self.CHAT_TAB)

    def navigate_to_profile(self) -> bool:
        """Navigate to patient profile screen."""
        return self.click(*self.PROFILE_TAB)

    def navigate_to_history(self) -> bool:
        """Navigate to report history screen."""
        return self.click(*self.HISTORY_TAB)

    def search_biomarker(self, keyword: str) -> bool:
        """Search biomarker catalog."""
        return self.enter_text(*self.SEARCH_INPUT, keyword)
