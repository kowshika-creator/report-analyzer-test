# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Base Page Object Model
Provides enterprise web interaction primitives with explicit waits, retry logic,
and automatic error diagnostic capture.
"""

import time
from typing import List, Tuple, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from automation.config.settings import AutomationConfig

class BasePage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.timeout = AutomationConfig.EXPLICIT_WAIT
        self.wait = WebDriverWait(self.driver, self.timeout, poll_frequency=AutomationConfig.POLLING_FREQUENCY)

    def navigate_to(self, path: str = "") -> None:
        """Navigates to an absolute or relative path based on BASE_URL."""
        clean_path = path.lstrip("/")
        if clean_path:
            target_url = f"{AutomationConfig.BASE_URL}/{clean_path}"
        else:
            target_url = AutomationConfig.BASE_URL
        self.driver.get(target_url)
        self.wait_for_page_ready()

    def wait_for_page_ready(self, timeout: Optional[int] = None) -> bool:
        """Waits for document.readyState == 'complete'."""
        wait_time = timeout or self.timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            return False

    def find(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> WebElement:
        """Finds a single element after explicit visibility wait."""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def find_visible(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> WebElement:
        """Waits until the element is present and visible."""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> List[WebElement]:
        """Finds all matching elements."""
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            return wait.until(EC.presence_of_all_elements_located(locator))
        except TimeoutException:
            return []

    def click(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> None:
        """Clicks an element with retry on StaleElement or ClickIntercepted exceptions."""
        wait_time = timeout or self.timeout
        end_time = time.time() + wait_time
        last_exception = None

        while time.time() < end_time:
            try:
                element = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(locator))
                element.click()
                return
            except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                last_exception = e
                # Fallback to JavaScript click if intercepted
                try:
                    elem = self.driver.find_element(*locator)
                    self.driver.execute_script("arguments[0].click();", elem)
                    return
                except Exception:
                    pass
                time.sleep(0.3)
            except TimeoutException as e:
                last_exception = e
                break

        raise TimeoutException(f"Failed to click element {locator} within {wait_time}s: {last_exception}")

    def type_text(self, locator: Tuple[str, str], text: str, clear: bool = True) -> None:
        """Types text into an input field with optional pre-clearing."""
        element = self.find_visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)

    def get_text(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> str:
        """Retrieves visible text from an element."""
        element = self.find_visible(locator, timeout)
        return element.text.strip()

    def is_displayed(self, locator: Tuple[str, str], timeout: int = 1) -> bool:
        """Checks if an element is currently displayed without raising unhandled timeouts."""
        try:
            self.driver.implicitly_wait(0)
            elements = self.driver.find_elements(*locator)
            if elements and elements[0].is_displayed():
                return True
            return False
        except Exception:
            return False
        finally:
            self.driver.implicitly_wait(AutomationConfig.IMPLICIT_WAIT)

    def scroll_to(self, locator: Tuple[str, str]) -> None:
        """Scrolls the element into the viewport center."""
        element = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.2)

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_page_title(self) -> str:
        return self.driver.title

    def get_browser_console_logs(self) -> List[str]:
        """Captures Chrome browser console errors and warnings."""
        try:
            logs = self.driver.get_log("browser")
            return [f"[{log.get('level')}] {log.get('message')}" for log in logs]
        except Exception:
            return []
