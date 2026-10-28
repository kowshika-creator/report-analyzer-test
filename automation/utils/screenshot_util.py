# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Screenshot Capture Utility
Captures PNG viewport screenshots for defect evidence and saves them to Test Results/Screenshots/.
"""

import os
import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from automation.config.settings import AutomationConfig

class ScreenshotUtil:
    @staticmethod
    def capture(driver: WebDriver, test_id: str, suffix: str = "failure") -> str:
        AutomationConfig.validate()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_id = test_id.replace(" ", "_").replace("/", "-")
        filename = f"{sanitized_id}_{suffix}_{timestamp}.png"
        filepath = os.path.join(AutomationConfig.SCREENSHOTS_DIR, filename)
        
        try:
            driver.save_screenshot(filepath)
            return filepath
        except Exception as e:
            print(f"[SCREENSHOT ERROR] Failed to capture screenshot for {test_id}: {e}")
            return ""
