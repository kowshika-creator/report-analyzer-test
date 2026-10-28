# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Excel Report Generator
Generates enterprise multi-sheet Excel reports with styled headers, metrics, and defect sheets:
1. Automation_Test_Report.xlsx (6 Sheets)
2. Failed_Test_Cases.xlsx
3. Passed_Test_Cases.xlsx
4. Summary_Report.xlsx
"""

import os
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from automation.config.settings import AutomationConfig

class ExcelReporter:
    HEADER_FILL = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    PASS_FILL = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    PASS_FONT = Font(name="Segoe UI", size=10, color="065F46", bold=True)
    FAIL_FILL = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    FAIL_FONT = Font(name="Segoe UI", size=10, color="991B1B", bold=True)
    SKIP_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    SKIP_FONT = Font(name="Segoe UI", size=10, color="92400E", bold=True)
    REGULAR_FONT = Font(name="Segoe UI", size=10)
    BORDER = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    @classmethod
    def generate_all_reports(cls, test_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        AutomationConfig.validate()
        excel_dir = AutomationConfig.EXCEL_DIR
        generated_files = []

        # 1. Master Automation_Test_Report.xlsx
        master_path = os.path.join(excel_dir, "Automation_Test_Report.xlsx")
        cls._create_master_workbook(master_path, test_results, metrics)
        generated_files.append(master_path)

        # 2. Passed_Test_Cases.xlsx
        passed_path = os.path.join(excel_dir, "Passed_Test_Cases.xlsx")
        cls._create_filtered_workbook(passed_path, [t for t in test_results if t["status"] == "Passed"], "Passed Tests")
        generated_files.append(passed_path)

        # 3. Failed_Test_Cases.xlsx
        failed_path = os.path.join(excel_dir, "Failed_Test_Cases.xlsx")
        cls._create_filtered_workbook(failed_path, [t for t in test_results if t["status"] == "Failed"], "Failed Tests", include_errors=True)
        generated_files.append(failed_path)

        # 4. Execution_Summary.xlsx (and Summary_Report.xlsx)
        summary_path = os.path.join(excel_dir, "Execution_Summary.xlsx")
        cls._create_summary_workbook(summary_path, metrics)
        generated_files.append(summary_path)
        
        legacy_summary_path = os.path.join(excel_dir, "Summary_Report.xlsx")
        cls._create_summary_workbook(legacy_summary_path, metrics)
        generated_files.append(legacy_summary_path)

        return generated_files

    @classmethod
    def _create_master_workbook(cls, filepath: str, results: List[Dict[str, Any]], metrics: Dict[str, Any]):
        wb = openpyxl.Workbook()

        # Sheet 1: Executed Test Cases
        ws1 = wb.active
        ws1.title = "Executed Test Cases"
        headers = ["Test ID", "Module", "Test Name", "Status", "Execution Time", "Priority"]
        cls._write_table(ws1, headers, [
            [r["test_id"], r["module"], r["name"], r["status"], f"{r['duration_sec']:.2f}s", r.get("priority", "Medium")]
            for r in results
        ])

        # Sheet 2: Passed Tests
        ws2 = wb.create_sheet(title="Passed Tests")
        passed = [r for r in results if r["status"] == "Passed"]
        cls._write_table(ws2, headers, [
            [r["test_id"], r["module"], r["name"], r["status"], f"{r['duration_sec']:.2f}s", r.get("priority", "Medium")]
            for r in passed
        ])

        # Sheet 3: Failed Tests
        ws3 = wb.create_sheet(title="Failed Tests")
        fail_headers = ["Test ID", "Module", "Test Name", "Priority", "Failure Reason", "Screenshot Path"]
        failed = [r for r in results if r["status"] == "Failed"]
        cls._write_table(ws3, fail_headers, [
            [r["test_id"], r["module"], r["name"], r.get("priority", "Medium"), r.get("error", "Unknown"), r.get("screenshot", "")]
            for r in failed
        ])

        # Sheet 4: Skipped Tests
        ws4 = wb.create_sheet(title="Skipped Tests")
        skipped = [r for r in results if r["status"] == "Skipped"]
        cls._write_table(ws4, ["Test ID", "Module", "Test Name", "Reason"], [
            [r["test_id"], r["module"], r["name"], r.get("reason", "Condition not met")]
            for r in skipped
        ])

        # Sheet 5: Execution Metrics
        ws5 = wb.create_sheet(title="Execution Metrics")
        metrics_rows = [
            ["Metric Name", "Value"],
            ["Total Test Cases", metrics.get("total", 0)],
            ["Passed", metrics.get("passed", 0)],
            ["Failed", metrics.get("failed", 0)],
            ["Skipped", metrics.get("skipped", 0)],
            ["Pass Percentage", f"{metrics.get('pass_rate', 0):.2f}%"],
            ["Total Duration", f"{metrics.get('duration_seconds', 0):.2f}s"],
            ["Execution Timestamp", metrics.get("timestamp", "")],
            ["Target Environment BASE_URL", metrics.get("base_url", "")]
        ]
        cls._write_table(ws5, metrics_rows[0], metrics_rows[1:], auto_style_status=False)

        # Sheet 6: Defect Summary
        ws6 = wb.create_sheet(title="Defect Summary")
        defect_headers = ["Defect ID", "Related Test ID", "Module", "Severity", "Error Summary"]
        defects = []
        for idx, f in enumerate(failed, 1):
            defects.append([f"DEF-{idx:03d}", f["test_id"], f["module"], f.get("priority", "High"), f.get("error", "Error")[:100]])
        cls._write_table(ws6, defect_headers, defects, auto_style_status=False)

        # Sheet 7: Pass Rate Summary
        ws7 = wb.create_sheet(title="Pass Rate Summary")
        rate_headers = ["Module", "Total Tests", "Passed", "Failed", "Skipped", "Pass Rate (%)"]
        module_stats = {}
        for r in results:
            mod = r.get("module", "General")
            if mod not in module_stats:
                module_stats[mod] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            module_stats[mod]["total"] += 1
            if r["status"] == "Passed":
                module_stats[mod]["passed"] += 1
            elif r["status"] == "Failed":
                module_stats[mod]["failed"] += 1
            else:
                module_stats[mod]["skipped"] += 1

        rate_rows = []
        for mod, counts in module_stats.items():
            rate = (counts["passed"] / counts["total"] * 100) if counts["total"] > 0 else 0
            rate_rows.append([mod, counts["total"], counts["passed"], counts["failed"], counts["skipped"], f"{rate:.1f}%"])
        cls._write_table(ws7, rate_headers, rate_rows, auto_style_status=False)

        wb.save(filepath)

    @classmethod
    def _create_filtered_workbook(cls, filepath: str, results: List[Dict[str, Any]], sheet_name: str, include_errors: bool = False):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        if include_errors:
            headers = ["Test ID", "Module", "Test Name", "Priority", "Status", "Error Summary", "Screenshot"]
            data = [[r["test_id"], r["module"], r["name"], r.get("priority", "Medium"), r["status"], r.get("error", ""), r.get("screenshot", "")] for r in results]
        else:
            headers = ["Test ID", "Module", "Test Name", "Priority", "Status", "Duration"]
            data = [[r["test_id"], r["module"], r["name"], r.get("priority", "Medium"), r["status"], f"{r['duration_sec']:.2f}s"] for r in results]
        cls._write_table(ws, headers, data)
        wb.save(filepath)

    @classmethod
    def _create_summary_workbook(cls, filepath: str, metrics: Dict[str, Any]):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Executive Summary"
        rows = [
            ["Deployment & Execution Summary", ""],
            ["Application URL (BASE_URL)", metrics.get("base_url", "")],
            ["Execution Date", metrics.get("timestamp", "")],
            ["Overall Status", "PASSED" if metrics.get("pass_rate", 0) >= 95.0 else "FAILED"],
            ["Total Test Cases", metrics.get("total", 0)],
            ["Passed", metrics.get("passed", 0)],
            ["Failed", metrics.get("failed", 0)],
            ["Skipped", metrics.get("skipped", 0)],
            ["Pass Percentage", f"{metrics.get('pass_rate', 0):.2f}%"],
            ["Total Run Duration", f"{metrics.get('duration_seconds', 0):.2f}s"]
        ]
        cls._write_table(ws, ["Key Metric", "Measurement"], rows[1:], auto_style_status=False)
        wb.save(filepath)

    @classmethod
    def _write_table(cls, ws, headers: List[str], data: List[List[Any]], auto_style_status: bool = True):
        # Header Row
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.HEADER_FILL
            cell.font = cls.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = cls.BORDER
        ws.row_dimensions[1].height = 28

        # Data Rows
        for row_idx, row_data in enumerate(data, start=2):
            ws.append(row_data)
            ws.row_dimensions[row_idx].height = 20
            for col_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = cls.REGULAR_FONT
                cell.border = cls.BORDER
                cell.alignment = Alignment(vertical="center")

                # Color-code status cell
                val_str = str(cell.value).strip()
                if auto_style_status and val_str in ("Passed", "Failed", "Skipped"):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    if val_str == "Passed":
                        cell.fill = cls.PASS_FILL
                        cell.font = cls.PASS_FONT
                    elif val_str == "Failed":
                        cell.fill = cls.FAIL_FILL
                        cell.font = cls.FAIL_FONT
                    elif val_str == "Skipped":
                        cell.fill = cls.SKIP_FILL
                        cell.font = cls.SKIP_FONT

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)
