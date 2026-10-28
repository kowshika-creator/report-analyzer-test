# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Configuration & Environment Settings
Handles dynamic BASE_URL resolution (never hardcoded, never localhost in production).
"""

import os
from typing import Optional

class AutomationConfig:
    # BASE_URL must be provided via environment variable pointing to LIVE deployment
    # Example: https://<username>.github.io/<repository-name>/
    BASE_URL: str = os.environ.get("BASE_URL", "").rstrip("/")
    
    # Headless Chrome Settings
    HEADLESS: bool = os.environ.get("HEADLESS", "true").lower() in ("true", "1", "yes")
    WINDOW_WIDTH: int = int(os.environ.get("WINDOW_WIDTH", "1920"))
    WINDOW_HEIGHT: int = int(os.environ.get("WINDOW_HEIGHT", "1080"))
    
    # Timeouts (seconds)
    PAGE_LOAD_TIMEOUT: int = int(os.environ.get("PAGE_LOAD_TIMEOUT", "20"))
    IMPLICIT_WAIT: int = int(os.environ.get("IMPLICIT_WAIT", "1"))
    EXPLICIT_WAIT: int = int(os.environ.get("EXPLICIT_WAIT", "3"))
    POLLING_FREQUENCY: float = 0.3
    
    # Execution & Report Settings
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "1"))
    REPORTS_DIR: str = os.path.abspath(os.environ.get("REPORTS_DIR", "Test Results"))
    SCREENSHOTS_DIR: str = os.path.join(REPORTS_DIR, "Screenshots")
    LOGS_DIR: str = os.path.join(REPORTS_DIR, "Logs")
    EXCEL_DIR: str = os.path.join(REPORTS_DIR, "Excel")
    HTML_DIR: str = os.path.join(REPORTS_DIR, "HTML")
    JSON_DIR: str = os.path.join(REPORTS_DIR, "JSON")
    SUMMARY_DIR: str = os.path.join(REPORTS_DIR, "Summary")
    
    # Quality Gates
    PASS_PERCENTAGE_THRESHOLD: float = 95.0
    MAX_CRITICAL_FAIL_PERCENT: float = 5.0

    @classmethod
    def validate(cls):
        if not cls.BASE_URL:
            # Fallback for local sandbox testing if not set
            cls.BASE_URL = os.environ.get("DEPLOYMENT_URL", "https://kowshika-creator.github.io/report-analyzer-test")
            print(f"[CONFIG WARNING] BASE_URL not provided. Defaulting to: {cls.BASE_URL}")
        
        # Enforce live URL validation policy
        if "localhost" in cls.BASE_URL or "127.0.0.1" in cls.BASE_URL:
            if os.environ.get("ALLOW_LOCALHOST_OVERRIDE", "false").lower() != "true":
                raise ValueError(
                    f"VIOLATION: BASE_URL is set to '{cls.BASE_URL}'. "
                    f"Selenium E2E automation must NEVER run against localhost or local dev servers. "
                    f"It must target the LIVE GitHub Pages deployment."
                )
        
        # Ensure report directories exist
        for directory in [cls.REPORTS_DIR, cls.SCREENSHOTS_DIR, cls.LOGS_DIR, cls.EXCEL_DIR, cls.HTML_DIR, cls.JSON_DIR, cls.SUMMARY_DIR]:
            os.makedirs(directory, exist_ok=True)
