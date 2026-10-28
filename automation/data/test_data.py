# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Test Data Management
Provides parameterized datasets for authentication, file uploads, biomarker inputs,
and cross-browser viewports.
"""

import os

class TestData:
    # Authentication Data
    VALID_USERS = [
        {"email": "clinician.lead@axon.com", "password": "SecurePassword!2026", "name": "Dr. Sarah Mitchell"},
        {"email": "nurse.specialist@axon.com", "password": "ClinicalPass@99", "name": "Nurse Alex Chen"},
        {"email": "lab.tech@axon.com", "password": "TechPassword#12", "name": "Tech Jordan Taylor"}
    ]
    
    INVALID_EMAILS = [
        "plainaddress",
        "#@%^%#$@#$@#.com",
        "@example.com",
        "Joe Smith <email@example.com>",
        "email.example.com",
        "email@example@example.com",
        "email@example",
        "email@111.222.333.44444"
    ]
    
    INVALID_PASSWORDS = [
        "",
        "123",
        "short",
        "alllowercase",
        "NOSPACE123"
    ]

    # Clinical Report Texts for Ingestion Tests
    MOCK_NORMAL_CBC_REPORT = """
    ==================================================
    AXON CLINICAL LABORATORY REPORT - CBC PANEL
    ==================================================
    Biomarker            Value     Unit      Reference Interval
    Hemoglobin:          14.2      g/dL      12.0 - 17.5
    WBC Count:           6.8       10^3/uL   4.5 - 11.0
    Platelet Count:      260.0     10^3/uL   150 - 450
    RBC Count:           4.8       10^6/uL   4.2 - 5.9
    Neutrophils:         58.0      %         40.0 - 75.0
    Lymphocytes:         32.0      %         20.0 - 45.0
    """

    MOCK_PANIC_ALERT_REPORT = """
    ==================================================
    CRITICAL PANIC LABORATORY REPORT
    ==================================================
    Hemoglobin:          5.8       g/dL      12.0 - 17.5
    Platelet Count:      18.0      10^3/uL   150 - 450
    Fasting Glucose:     340.0     mg/dL     70 - 100
    Potassium:           2.1       mEq/L     3.5 - 5.1
    Serum Creatinine:    5.8       mg/dL     0.6 - 1.2
    """

    MOCK_RADIOLOGY_TEXT = """
    CLINICAL INDICATION: Lower back pain radiating to left lower extremity.
    MRI LUMBAR SPINE:
    Technique: Multiplanar T1 and T2 weighted images.
    FINDINGS:
    L4-L5: Moderate broad-based posterior disc protrusion indenting the thecal sac.
    L5-S1: Mild desiccated disc bulge without significant canal stenosis.
    IMPRESSION: L4-L5 disc protrusion with mild bilateral neural foraminal narrowing.
    """

    # Responsive Viewports for Cross-Device Testing
    VIEWPORTS = {
        "desktop_4k": (3840, 2160),
        "desktop_fhd": (1920, 1080),
        "laptop_hd": (1366, 768),
        "tablet_ipad_pro": (1024, 1366),
        "tablet_ipad": (768, 1024),
        "mobile_iphone14": (390, 844),
        "mobile_pixel7": (412, 915),
        "mobile_small": (360, 640)
    }

    # Supported Languages
    LANGUAGES = ["English", "Tamil", "Hindi", "Telugu", "Spanish", "French", "German"]
