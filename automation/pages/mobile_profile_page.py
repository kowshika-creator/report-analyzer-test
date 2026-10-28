# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Profile Page Object
Handles patient profile management, offline mode toggle, and settings.
"""

from typing import Any
from automation.pages.mobile_base_page import MobileBasePage

class MobileProfilePage(MobileBasePage):
    """Page object for Mobile Patient Profile & App Settings."""

    AGE_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'age') or contains(@text, 'Age')]")
    GENDER_PICKER = ("xpath", "//android.widget.TextView[contains(@text, 'Gender') or contains(@text, 'Male') or contains(@text, 'Female')]")
    CONDITIONS_INPUT = ("xpath", "//android.widget.EditText[contains(@content-desc, 'conditions') or contains(@text, 'Conditions')]")
    SAVE_PROFILE_BTN = ("xpath", "//android.widget.TextView[@text='Save Profile' or @text='Update Profile']")
    OFFLINE_SWITCH = ("xpath", "//android.widget.Switch[contains(@content-desc, 'offline') or contains(@text, 'Offline')]")
    LOGOUT_BTN = ("xpath", "//android.widget.TextView[@text='Log Out' or @text='Sign Out']")
    SUCCESS_TOAST = ("xpath", "//android.widget.TextView[contains(@text, 'Saved') or contains(@text, 'Updated')]")

    def update_profile(self, age: str, conditions: str) -> bool:
        """Update patient baseline clinical parameters."""
        self.enter_text(*self.AGE_INPUT, age)
        self.enter_text(*self.CONDITIONS_INPUT, conditions)
        return self.click(*self.SAVE_PROFILE_BTN)

    def toggle_offline_mode(self) -> bool:
        """Toggle local inference offline mode."""
        return self.click(*self.OFFLINE_SWITCH)

    def logout(self) -> bool:
        """Sign out of patient session."""
        return self.click(*self.LOGOUT_BTN)
