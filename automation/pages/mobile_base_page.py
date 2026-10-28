# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Mobile Base Page Object
Encapsulates Appium WebDriver interactions, explicit waits, gestures,
swipe/scroll actions, toast validations, and failure screenshot captures.
"""

import os
import time
import logging
from typing import Any, List, Optional, Tuple

from automation.config.settings import AutomationConfig

logger = logging.getLogger("axon.mobile.page")

class MobileBasePage:
    """Base class for all Mobile Page Objects."""

    def __init__(self, driver: Any):
        self.driver = driver
        self.timeout = AutomationConfig.EXPLICIT_WAIT

    def find_element(self, by: str, value: str, timeout: Optional[int] = None) -> Any:
        """Find element with explicit timeout wait."""
        t_wait = timeout or self.timeout
        start_time = time.time()
        while time.time() - start_time < t_wait:
            try:
                el = self.driver.find_element(by, value)
                if el and hasattr(el, 'is_displayed') and el.is_displayed():
                    return el
                elif el:
                    return el
            except Exception:
                time.sleep(AutomationConfig.POLLING_FREQUENCY)
        return self.driver.find_element(by, value)

    def click(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        """Click mobile element safely."""
        try:
            el = self.find_element(by, value, timeout)
            el.click()
            return True
        except Exception as e:
            logger.warning(f"Click failed on {value}: {e}")
            return False

    def enter_text(self, by: str, value: str, text: str, clear: bool = True) -> bool:
        """Send keys to text input field."""
        try:
            el = self.find_element(by, value)
            if clear:
                el.clear()
            el.send_keys(text)
            return True
        except Exception as e:
            logger.warning(f"Enter text failed on {value}: {e}")
            return False

    def get_text(self, by: str, value: str) -> str:
        """Retrieve text from element."""
        try:
            el = self.find_element(by, value)
            return el.text or el.get_attribute("text") or el.get_attribute("content-desc") or ""
        except Exception:
            return ""

    def is_visible(self, by: str, value: str, timeout: int = 2) -> bool:
        """Check if element is visible on screen."""
        try:
            el = self.find_element(by, value, timeout=timeout)
            return el.is_displayed()
        except Exception:
            return False

    def swipe_up(self, duration: int = 500):
        """Perform vertical scroll/swipe up gesture."""
        try:
            if hasattr(self.driver, "get_window_size") and hasattr(self.driver, "swipe"):
                size = self.driver.get_window_size()
                start_x = size['width'] // 2
                start_y = int(size['height'] * 0.8)
                end_y = int(size['height'] * 0.2)
                self.driver.swipe(start_x, start_y, start_x, end_y, duration)
        except Exception as e:
            logger.debug(f"Swipe up gesture skipped: {e}")

    def swipe_down(self, duration: int = 500):
        """Perform vertical scroll/swipe down gesture."""
        try:
            if hasattr(self.driver, "get_window_size") and hasattr(self.driver, "swipe"):
                size = self.driver.get_window_size()
                start_x = size['width'] // 2
                start_y = int(size['height'] * 0.2)
                end_y = int(size['height'] * 0.8)
                self.driver.swipe(start_x, start_y, start_x, end_y, duration)
        except Exception as e:
            logger.debug(f"Swipe down gesture skipped: {e}")

    def capture_screenshot(self, name: str) -> str:
        """Capture device screenshot and save to Screenshots directory."""
        filename = f"{name}_{int(time.time() * 1000)}.png"
        filepath = os.path.join(AutomationConfig.SCREENSHOTS_DIR, filename)
        try:
            self.driver.get_screenshot_as_file(filepath)
            return filepath
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return ""
