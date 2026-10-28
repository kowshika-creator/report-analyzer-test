# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Clinical Chatbot Widget Page Object
Maps chat drawer, message input, tone selector, quick suggestions, and response bubbles.
"""

from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class ChatbotWidget(BasePage):
    CHAT_DRAWER = (By.CSS_SELECTOR, ".chat-drawer, .chat-container, .companion-window")
    MESSAGE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='Ask'], textarea[placeholder*='Ask']")
    SEND_BUTTON = (By.CSS_SELECTOR, "button.chat-send-btn, button[aria-label='Send message']")
    MESSAGE_BUBBLES = (By.CSS_SELECTOR, ".chat-bubble, .message-content")
    TONE_SELECTOR = (By.CSS_SELECTOR, "select.tone-select, .tone-segment-toggle")
    DISCLAIMER_TEXT = (By.CSS_SELECTOR, ".chat-disclaimer, .medical-disclaimer")

    def is_chat_active(self) -> bool:
        return self.is_displayed(self.MESSAGE_INPUT, timeout=3)

    def send_message(self, message: str) -> None:
        self.type_text(self.MESSAGE_INPUT, message)
        self.click(self.SEND_BUTTON)
        self.wait_for_page_ready()

    def get_last_response(self) -> str:
        bubbles = self.find_all(self.MESSAGE_BUBBLES, timeout=5)
        if bubbles:
            return bubbles[-1].text.strip()
        return ""
