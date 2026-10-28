# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Authentication Page Object
Handles sign-in, registration, demo mode activation, and password validation.
"""

from typing import Any
from automation.pages.mobile_base_page import MobileBasePage

class MobileAuthPage(MobileBasePage):
    """Page object for Mobile Authentication & Onboarding screen."""

    # Selectors (using accessibility id and android resource ids)
    EMAIL_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'email') or contains(@text, 'Email')]")
    PASSWORD_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'password') or contains(@text, 'Password')]")
    LOGIN_BTN = ("xpath", "//android.widget.TextView[@text='Sign In' or @text='Login']")
    GUEST_BTN = ("xpath", "//android.widget.TextView[contains(@text, 'Guest') or contains(@text, 'Explore as Guest')]")
    REGISTER_TAB = ("xpath", "//android.widget.TextView[@text='Register' or @text='Sign Up']")
    REGISTER_BTN = ("xpath", "//android.widget.TextView[@text='Create Account' or @text='Register']")
    ERROR_MSG = ("xpath", "//android.widget.TextView[contains(@text, 'Invalid') or contains(@text, 'Error') or contains(@text, 'required')]")
    APP_LOGO = ("xpath", "//android.widget.TextView[@text='AXON' or contains(@text, 'Medical')]")

    def login(self, email: str, password: str) -> bool:
        """Perform login flow."""
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        return self.click(*self.LOGIN_BTN)

    def activate_guest_mode(self) -> bool:
        """Tap guest mode explore button."""
        return self.click(*self.GUEST_BTN)

    def switch_to_register(self) -> bool:
        """Switch to registration view."""
        return self.click(*self.REGISTER_TAB)

    def register(self, email: str, password: str) -> bool:
        """Register new patient account."""
        self.switch_to_register()
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        return self.click(*self.REGISTER_BTN)

    def is_login_screen_visible(self) -> bool:
        """Verify auth screen is visible."""
        return self.is_visible(*self.APP_LOGO) or self.is_visible(*self.LOGIN_BTN)
