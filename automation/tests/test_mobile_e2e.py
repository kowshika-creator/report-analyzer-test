# -*- coding: utf-8 -*-
"""
AXON Mobile Automation - Pytest E2E Test Suite
Integrates MobileDriverFactory, Mobile Page Objects, and test assertions.
"""

import pytest
from automation.drivers.mobile_driver import MobileDriverFactory
from automation.pages.mobile_auth_page import MobileAuthPage
from automation.pages.mobile_dashboard_page import MobileDashboardPage
from automation.pages.mobile_upload_page import MobileUploadPage
from automation.pages.mobile_profile_page import MobileProfilePage
from automation.pages.mobile_chat_page import MobileChatPage

@pytest.fixture(scope="module")
def driver():
    drv = MobileDriverFactory.create_driver()
    yield drv
    drv.quit()

@pytest.fixture
def auth_page(driver):
    return MobileAuthPage(driver)

@pytest.fixture
def dashboard_page(driver):
    return MobileDashboardPage(driver)

@pytest.fixture
def upload_page(driver):
    return MobileUploadPage(driver)

@pytest.fixture
def profile_page(driver):
    return MobileProfilePage(driver)

@pytest.fixture
def chat_page(driver):
    return MobileChatPage(driver)

def test_mobile_guest_onboarding(auth_page, dashboard_page):
    """Verify guest exploration mode unlocks dashboard."""
    assert auth_page.activate_guest_mode() is True

def test_mobile_biomarker_search(dashboard_page):
    """Verify search input functions without error."""
    assert dashboard_page.search_biomarker("Hemoglobin") is True

def test_mobile_report_paste_analysis(upload_page):
    """Verify manual text report entry and trigger."""
    sample = "Hemoglobin: 14.5 g/dL (Normal: 12.0 - 15.5)\nFasting Glucose: 92 mg/dL"
    assert upload_page.upload_sample_text_report(sample) is True

def test_mobile_profile_update(profile_page):
    """Verify patient profile parameter updates."""
    assert profile_page.update_profile("38", "Hypertension") is True

def test_mobile_companion_chat(chat_page):
    """Verify conversational AI companion query submission."""
    assert chat_page.send_query("What does elevated fasting glucose indicate?") is True
