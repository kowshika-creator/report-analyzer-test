# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Clinical Companion Chat Page Object
Handles conversational queries, clinical clarification, and suggestion chips.
"""

from typing import Any
from automation.pages.mobile_base_page import MobileBasePage

class MobileChatPage(MobileBasePage):
    """Page object for Mobile Clinical AI Companion Chat screen."""

    MESSAGE_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'chat-input') or contains(@text, 'Ask')]")
    SEND_BTN = ("xpath", "//android.widget.TextView[@text='Send' or contains(@content-desc, 'send')]")
    CHAT_BUBBLE = ("xpath", "//android.widget.TextView[contains(@content-desc, 'message') or contains(@text, 'AXON')]")
    CLEAR_CHAT_BTN = ("xpath", "//android.widget.TextView[contains(@text, 'Clear') or contains(@text, 'Reset')]")

    def send_query(self, query: str) -> bool:
        """Send clinical inquiry to AI companion."""
        self.enter_text(*self.MESSAGE_INPUT, query)
        return self.click(*self.SEND_BTN)

    def is_response_received(self, timeout: int = 10) -> bool:
        """Verify AI clinical companion response bubble appeared."""
        return self.is_visible(*self.CHAT_BUBBLE, timeout=timeout)
