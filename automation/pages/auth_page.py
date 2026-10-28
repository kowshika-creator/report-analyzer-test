# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Authentication Page Object
Maps sign-in, account creation, validation error alerts, and demonstration access.
"""

from selenium.webdriver.common.by import By
from automation.pages.base_page import BasePage

class AuthPage(BasePage):
    # Auth Modal & Gate Locators
    AUTH_CONTAINER = (By.CSS_SELECTOR, ".auth-gate, .auth-modal, .auth-form")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    TOGGLE_AUTH_MODE_BTN = (By.CSS_SELECTOR, ".auth-toggle button")
    DEMO_MODE_BTN = (By.XPATH, "//button[contains(text(), 'Demonstration Mode') or contains(text(), 'Continue as Guest')]")
    ERROR_ALERT = (By.CSS_SELECTOR, ".auth-error, p[style*='critical-text']")
    
    # Profile Locators
    PROFILE_NAME = (By.CSS_SELECTOR, ".sidebar-profile-name, .user-name")
    PROFILE_EMAIL = (By.CSS_SELECTOR, ".sidebar-profile-email, .user-email")

    def is_auth_gate_displayed(self) -> bool:
        return self.is_displayed(self.EMAIL_INPUT, timeout=4)

    def login(self, email: str, password: str) -> None:
        self.type_text(self.EMAIL_INPUT, email)
        self.type_text(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BTN)
        self.wait_for_page_ready()

    def continue_as_guest(self) -> None:
        if self.is_displayed(self.DEMO_MODE_BTN, timeout=3):
            self.click(self.DEMO_MODE_BTN)
            self.wait_for_page_ready()

    def switch_to_sign_up(self) -> None:
        if self.is_displayed(self.TOGGLE_AUTH_MODE_BTN, timeout=2):
            self.click(self.TOGGLE_AUTH_MODE_BTN)

    def get_auth_error_message(self) -> str:
        if self.is_displayed(self.ERROR_ALERT, timeout=3):
            return self.get_text(self.ERROR_ALERT)
        return ""
