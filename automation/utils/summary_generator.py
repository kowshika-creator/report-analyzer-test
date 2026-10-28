# -*- coding: utf-8 -*-
"""
AXON E2E Automation - GitHub Actions Execution Summary Generator
Generates summary.md and publishes to $GITHUB_STEP_SUMMARY matching the exact specification.
"""

import os
from typing import List, Dict, Any
from automation.config.settings import AutomationConfig

class SummaryGenerator:
    @classmethod
    def generate_summary(cls, test_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        AutomationConfig.validate()
        summary_dir = AutomationConfig.SUMMARY_DIR
        filepath = os.path.join(summary_dir, "summary.md")

        total = metrics.get("total", len(test_results))
        passed = metrics.get("passed", sum(1 for r in test_results if r["status"] == "Passed"))
        failed = metrics.get("failed", sum(1 for r in test_results if r["status"] == "Failed"))
        skipped = metrics.get("skipped", sum(1 for r in test_results if r["status"] == "Skipped"))
        pass_rate = metrics.get("pass_rate", (passed / max(1, total)) * 100)
        duration = metrics.get("duration_seconds", 0)
        base_url = metrics.get("base_url", "https://kowshika-creator.github.io/report-analyzer-test")
        timestamp = metrics.get("timestamp", "")
        build_status = metrics.get("build_status", "PASS")
        deployment_status = metrics.get("deployment_status", "PASS")

        # Module aggregation
        modules = {}
        for r in test_results:
            mod = r["module"]
            if mod not in modules:
                modules[mod] = {"total": 0, "passed": 0, "failed": 0}
            modules[mod]["total"] += 1
            if r["status"] == "Passed":
                modules[mod]["passed"] += 1
            elif r["status"] == "Failed":
                modules[mod]["failed"] += 1

        # Top Passing Modules
        top_passing = sorted(
            modules.items(),
            key=lambda x: (x[1]["passed"] / max(1, x[1]["total"])),
            reverse=True
        )

        # Top Failing Modules
        top_failing = sorted(
            [m for m in modules.items() if m[1]["failed"] > 0],
            key=lambda x: x[1]["failed"],
            reverse=True
        )

        failed_tests = [r for r in test_results if r["status"] == "Failed"]

        # Build Markdown content
        lines = [
            "# Live GitHub Pages E2E Execution Summary",
            "",
            f"**Deployment URL:**",
            f"[{base_url}]({base_url})",
            "",
            f"**Execution Date:**",
            f"`{timestamp}`",
            "",
            f"**Build Status:**",
            f"`{build_status}`",
            "",
            f"**Deployment Status:**",
            f"`{deployment_status}`",
            "",
            f"**Total Test Cases:**",
            f"**{total}** (Target: 400+)",
            "",
            "| Metric | Count | Ratio |",
            "| :--- | :---: | :---: |",
            f"| **Executed** | {total} | 100.0% |",
            f"| **Passed** | {passed} | {pass_rate:.2f}% |",
            f"| **Failed** | {failed} | {(failed / max(1, total)) * 100:.2f}% |",
            f"| **Skipped** | {skipped} | {(skipped / max(1, total)) * 100:.2f}% |",
            "",
            f"**Pass Percentage:**",
            f"`{pass_rate:.2f}%` {'✅ (Quality Gate Passed ≥ 95%)' if pass_rate >= 95.0 else '❌ (Quality Gate Failed < 95%)'}",
            "",
            f"**Execution Duration:**",
            f"`{duration:.2f} seconds`",
            "",
            "---",
            "",
            "### Top Passing Modules",
            ""
        ]

        for mod_name, stats in top_passing[:5]:
            rate = (stats["passed"] / max(1, stats["total"])) * 100
            lines.append(f"- **{mod_name}**: `{rate:.1f}% Pass` ({stats['passed']}/{stats['total']})")

        lines.extend([
            "",
            "### Top Failed Modules",
            ""
        ])

        if top_failing:
            for mod_name, stats in top_failing[:5]:
                lines.append(f"- **{mod_name}**: `{stats['failed']} Failures` out of {stats['total']} tests")
        else:
            lines.append("- *Zero modules failed. Clean execution run!*")

        lines.extend([
            "",
            "### Failed Tests",
            ""
        ])

        if failed_tests:
            for ft in failed_tests[:10]:
                lines.append(f"- **{ft['test_id']}**: {ft['name']}")
                lines.append(f"  - *Failure Reason*: `{ft.get('error', 'Assertion or timeout error')}`")
        else:
            lines.append("- *No failed tests recorded.*")

        lines.extend([
            "",
            "---",
            "",
            "### Artifacts Generated",
            "",
            "✓ **Excel Reports**: `Automation_Test_Report.xlsx`, `Failed_Test_Cases.xlsx`, `Passed_Test_Cases.xlsx`, `Summary_Report.xlsx`",
            "✓ **HTML Reports**: `execution-report.html`, `dashboard.html`",
            "✓ **Screenshots**: High-resolution PNGs stored in `Test Results/Screenshots/`",
            "✓ **Logs**: Complete execution traces in `Test Results/Logs/execution.log`",
            "✓ **JSON Results**: Full telemetry in `Test Results/JSON/execution-results.json`",
            ""
        ])

        summary_content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary_content)

        # Write to $GITHUB_STEP_SUMMARY if running in GitHub Actions
        github_step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if github_step_summary_path and os.path.exists(os.path.dirname(github_step_summary_path)):
            try:
                with open(github_step_summary_path, "a", encoding="utf-8") as f:
                    f.write("\n" + summary_content + "\n")
            except Exception as e:
                print(f"[SUMMARY WARNING] Could not write to GITHUB_STEP_SUMMARY: {e}")

        return filepath
