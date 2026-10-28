# -*- coding: utf-8 -*-
"""
AXON E2E Automation - WebDriver Factory
Initializes Headless Chrome with production enterprise capabilities:
- Modern Headless mode (--headless=new)
- Performance & security flags
- Console logging preferences for defect diagnostics
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from automation.config.settings import AutomationConfig

class DriverFactory:
    @staticmethod
    def create_driver(headless: bool = None) -> webdriver.Chrome:
        AutomationConfig.validate()
        if headless is None:
            headless = AutomationConfig.HEADLESS

        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        
        # Enterprise Stability & Sandbox Options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument(f"--window-size={AutomationConfig.WINDOW_WIDTH},{AutomationConfig.WINDOW_HEIGHT}")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--user-agent=AXON-Selenium-Automated-E2E-Agent/1.0")

        # Enable Browser Console Logging for Failure Evidence
        options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})

        # Initialize ChromeDriver
        try:
            # First try webdriver-manager
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            # Fallback to system-provided chromedriver (common in CI/CD ubuntu-latest environments)
            print(f"[DRIVER FACTORY NOTICE] ChromeDriver fallback due to: {e}")
            driver = webdriver.Chrome(options=options)

        driver.set_page_load_timeout(AutomationConfig.PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(AutomationConfig.IMPLICIT_WAIT)
        return driver
