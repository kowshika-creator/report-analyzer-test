# -*- coding: utf-8 -*-
"""
AXON E2E Automation - JSON Results Serializer
Generates machine-readable execution-results.json for CI/CD integrations.
"""

import os
import json
from typing import List, Dict, Any
from automation.config.settings import AutomationConfig

class JSONReporter:
    @staticmethod
    def generate_json_report(test_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        AutomationConfig.validate()
        filepath = os.path.join(AutomationConfig.JSON_DIR, "execution-results.json")
        payload = {
            "execution_metadata": metrics,
            "test_cases": test_results
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return filepath

    @classmethod
    def generate_report(cls, test_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        return cls.generate_json_report(test_results, metrics)
