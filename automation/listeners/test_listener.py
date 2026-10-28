# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Test Execution Listener
Listens to test events, manages failure logging, captures device screenshots,
and records logcat dumps.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

from automation.config.settings import AutomationConfig

logger = logging.getLogger("axon.mobile.listener")

class MobileTestListener:
    """Enterprise test listener for Appium test events."""

    def __init__(self, driver: Any = None):
        self.driver = driver
        self.screenshots_dir = AutomationConfig.SCREENSHOTS_DIR
        self.logs_dir = AutomationConfig.LOGS_DIR
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def on_test_start(self, test_case: Dict[str, Any]):
        logger.info(f"▶ [START] {test_case['test_id']} - {test_case['name']}")

    def on_test_success(self, test_case: Dict[str, Any], duration: float):
        logger.info(f"✔ [PASS] {test_case['test_id']} ({duration:.2f}s)")

    def on_test_failure(self, test_case: Dict[str, Any], error: str, duration: float) -> Dict[str, str]:
        logger.error(f"✖ [FAIL] {test_case['test_id']}: {error} ({duration:.2f}s)")
        evidence = {"screenshot": "", "device_log": "", "stack_trace": error}

        # 1. Capture Device Screenshot
        screenshot_name = f"FAIL_{test_case['test_id']}_{int(time.time()*1000)}.png"
        screenshot_path = os.path.join(self.screenshots_dir, screenshot_name)
        try:
            if self.driver and hasattr(self.driver, "get_screenshot_as_file"):
                self.driver.get_screenshot_as_file(screenshot_path)
                evidence["screenshot"] = screenshot_path
            else:
                # Minimal mock image fallback
                png_1x1 = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                    b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05'
                    b'\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                with open(screenshot_path, "wb") as f:
                    f.write(png_1x1)
                evidence["screenshot"] = screenshot_path
        except Exception as e:
            logger.warning(f"Could not capture screenshot for {test_case['test_id']}: {e}")

        # 2. Capture Device Logs (logcat)
        log_name = f"LOGCAT_{test_case['test_id']}_{int(time.time()*1000)}.log"
        log_path = os.path.join(self.logs_dir, log_name)
        try:
            log_content = f"Logcat dump for {test_case['test_id']}\nTimestamp: {time.ctime()}\nError: {error}\n"
            if self.driver and hasattr(self.driver, "get_log"):
                try:
                    entries = self.driver.get_log("logcat")
                    log_content += "\n".join([f"{e.get('timestamp')}: {e.get('message')}" for e in entries[-50:]])
                except Exception:
                    pass
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            evidence["device_log"] = log_path
        except Exception as e:
            logger.warning(f"Could not capture logcat for {test_case['test_id']}: {e}")

        return evidence

    def on_test_skip(self, test_case: Dict[str, Any], reason: str):
        logger.warning(f"⏸ [SKIP] {test_case['test_id']}: {reason}")
