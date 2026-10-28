# -*- coding: utf-8 -*-
"""
AXON E2E Automation - HTML Report & Dashboard Generator
Creates modern, responsive, standalone HTML execution dashboards with SVG charts,
module metrics, search/filtering, and failure modal view.
"""

import os
import json
from typing import List, Dict, Any
from automation.config.settings import AutomationConfig

class HTMLReporter:
    @classmethod
    def generate_reports(cls, test_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        AutomationConfig.validate()
        html_dir = AutomationConfig.HTML_DIR
        
        # 1. execution-report.html
        exec_report_path = os.path.join(html_dir, "execution-report.html")
        html_content = cls._build_html(test_results, metrics, is_dashboard=False)
        with open(exec_report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 2. dashboard.html
        dashboard_path = os.path.join(html_dir, "dashboard.html")
        dashboard_content = cls._build_html(test_results, metrics, is_dashboard=True)
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard_content)

        return [exec_report_path, dashboard_path]

    @classmethod
    def _build_html(cls, results: List[Dict[str, Any]], metrics: Dict[str, Any], is_dashboard: bool = False) -> str:
        total = metrics.get("total", len(results))
        passed = metrics.get("passed", sum(1 for r in results if r["status"] == "Passed"))
        failed = metrics.get("failed", sum(1 for r in results if r["status"] == "Failed"))
        skipped = metrics.get("skipped", sum(1 for r in results if r["status"] == "Skipped"))
        pass_rate = metrics.get("pass_rate", (passed / max(1, total)) * 100)
        duration = metrics.get("duration_seconds", 0)
        base_url = metrics.get("base_url", "https://kowshika-creator.github.io/report-analyzer-test")
        timestamp = metrics.get("timestamp", "")

        # Compute Module Stats
        modules = {}
        for r in results:
            mod = r["module"]
            if mod not in modules:
                modules[mod] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            modules[mod]["total"] += 1
            if r["status"] == "Passed":
                modules[mod]["passed"] += 1
            elif r["status"] == "Failed":
                modules[mod]["failed"] += 1
            else:
                modules[mod]["skipped"] += 1

        # Calculate SVG Donut chart angles
        pass_deg = (passed / max(1, total)) * 360
        fail_deg = (failed / max(1, total)) * 360
        skip_deg = (skipped / max(1, total)) * 360

        rows_html = ""
        for r in results:
            status = r["status"]
            badge_class = "badge-pass" if status == "Passed" else ("badge-fail" if status == "Failed" else "badge-skip")
            error_msg = f"<div class='error-snippet'>{r.get('error', '')}</div>" if r.get('error') else ""
            rows_html += f"""
            <tr class="test-row status-{status.lower()}">
                <td class="font-mono">{r["test_id"]}</td>
                <td><span class="module-tag">{r["module"]}</span></td>
                <td>
                    <div class="test-name">{r["name"]}</div>
                    {error_msg}
                </td>
                <td><span class="badge {badge_class}">{status}</span></td>
                <td>{r.get('priority', 'Medium')}</td>
                <td class="text-right font-mono">{r['duration_sec']:.2f}s</td>
            </tr>
            """

        module_cards_html = ""
        for mod_name, mod_stat in modules.items():
            mod_pass_rate = (mod_stat["passed"] / max(1, mod_stat["total"])) * 100
            bar_color = "#10B981" if mod_pass_rate >= 95 else ("#F59E0B" if mod_pass_rate >= 80 else "#EF4444")
            module_cards_html += f"""
            <div class="module-card">
                <div class="module-card-header">
                    <h4>{mod_name}</h4>
                    <span class="pass-percent">{mod_pass_rate:.1f}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {mod_pass_rate}%; background: {bar_color};"></div>
                </div>
                <div class="module-stat-line">
                    <span>Passed: <strong>{mod_stat['passed']}</strong></span>
                    <span>Failed: <strong style="color: #EF4444">{mod_stat['failed']}</strong></span>
                    <span>Total: <strong>{mod_stat['total']}</strong></span>
                </div>
            </div>
            """

        page_title = "AXON Live GitHub Pages E2E Dashboard" if is_dashboard else "AXON Selenium E2E Execution Report"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        :root {{
            --bg: #0F172A;
            --surface: #1E293B;
            --surface-card: #243247;
            --border: #334155;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --accent: #0D9488;
            --pass: #10B981;
            --fail: #EF4444;
            --skip: #F59E0B;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background: var(--bg); color: var(--text-primary); padding: 2rem; line-height: 1.5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem; }}
        h1 {{ font-size: 1.6rem; font-weight: 700; color: #38BDF8; display: flex; align-items: center; gap: 0.5rem; }}
        .header-meta {{ font-size: 0.85rem; color: var(--text-secondary); }}
        .header-meta span {{ color: var(--text-primary); font-family: monospace; }}
        
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
        .metric-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; position: relative; overflow: hidden; }}
        .metric-card h3 {{ font-size: 0.82rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
        .metric-card .value {{ font-size: 2rem; font-weight: 800; }}
        .metric-pass .value {{ color: var(--pass); }}
        .metric-fail .value {{ color: var(--fail); }}
        .metric-skip .value {{ color: var(--skip); }}
        .metric-rate .value {{ color: #38BDF8; }}

        .chart-section {{ display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
        @media (max-width: 900px) {{ .chart-section {{ grid-template-columns: 1fr; }} }}
        .chart-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
        .modules-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }}
        .module-card {{ background: var(--surface-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }}
        .module-card-header {{ display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: 600; }}
        .progress-bar-bg {{ background: #334155; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem; }}
        .progress-bar-fill {{ height: 100%; transition: width 0.3s; }}
        .module-stat-line {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-secondary); }}

        .table-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
        .table-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem; }}
        .filter-controls {{ display: flex; gap: 0.5rem; }}
        .filter-btn {{ background: #334155; border: 1px solid var(--border); color: #FFF; padding: 0.35rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.82rem; }}
        .filter-btn.active {{ background: #0284C7; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
        th {{ background: #0F172A; text-align: left; padding: 0.75rem 1rem; color: var(--text-secondary); font-weight: 600; border-bottom: 2px solid var(--border); }}
        td {{ padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
        .font-mono {{ font-family: monospace; font-size: 0.82rem; }}
        .text-right {{ text-align: right; }}
        .module-tag {{ background: rgba(56, 189, 248, 0.1); color: #38BDF8; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
        .badge {{ padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; display: inline-block; }}
        .badge-pass {{ background: rgba(16, 185, 129, 0.15); color: var(--pass); border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-fail {{ background: rgba(239, 68, 68, 0.15); color: var(--fail); border: 1px solid rgba(239, 68, 68, 0.3); }}
        .badge-skip {{ background: rgba(245, 158, 11, 0.15); color: var(--skip); border: 1px solid rgba(245, 158, 11, 0.3); }}
        .error-snippet {{ margin-top: 0.4rem; padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border-left: 3px solid var(--fail); color: #FCA5A5; font-size: 0.8rem; font-family: monospace; border-radius: 2px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🩺 {page_title}</h1>
                <div class="header-meta">
                    Target Live URL: <span>{base_url}</span> | Execution Timestamp: <span>{timestamp}</span>
                </div>
            </div>
            <div style="text-align: right">
                <span class="badge {'badge-pass' if pass_rate >= 95 else 'badge-fail'}" style="font-size: 0.9rem; padding: 0.4rem 1rem;">
                    {'QUALITY GATE PASS' if pass_rate >= 95 else 'QUALITY GATE FAIL'} ({pass_rate:.1f}%)
                </span>
            </div>
        </header>

        <section class="metric-grid">
            <div class="metric-card">
                <h3>Total Test Cases</h3>
                <div class="value">{total:,}</div>
            </div>
            <div class="metric-card metric-pass">
                <h3>Passed</h3>
                <div class="value">{passed:,}</div>
            </div>
            <div class="metric-card metric-fail">
                <h3>Failed</h3>
                <div class="value">{failed:,}</div>
            </div>
            <div class="metric-card metric-skip">
                <h3>Skipped</h3>
                <div class="value">{skipped:,}</div>
            </div>
            <div class="metric-card metric-rate">
                <h3>Pass Percentage</h3>
                <div class="value">{pass_rate:.2f}%</div>
            </div>
            <div class="metric-card">
                <h3>Total Execution Time</h3>
                <div class="value" style="font-size: 1.5rem; line-height: 2rem;">{duration:.2f}s</div>
            </div>
        </section>

        <section class="chart-section">
            <div class="chart-box">
                <h3 style="margin-bottom: 1rem; font-size: 0.95rem;">Test Distribution</h3>
                <div style="display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.88rem;">
                    <div style="display: flex; justify-content: space-between;"><span style="color: var(--pass)">● Passed</span> <strong>{passed} ({pass_rate:.1f}%)</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: var(--fail)">● Failed</span> <strong>{failed} ({(failed/max(1,total))*100:.1f}%)</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: var(--skip)">● Skipped</span> <strong>{skipped} ({(skipped/max(1,total))*100:.1f}%)</strong></div>
                </div>
                <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--text-secondary);">
                    Threshold: <strong>≥ 95% Pass</strong> required for workflow success.
                </div>
            </div>

            <div class="chart-box">
                <h3 style="margin-bottom: 1rem; font-size: 0.95rem;">Module Execution Breakdown (14 Categories)</h3>
                <div class="modules-grid">
                    {module_cards_html}
                </div>
            </div>
        </section>

        <section class="table-section">
            <div class="table-header">
                <h3>Executed Test Cases Table ({total} Cases)</h3>
                <div class="filter-controls">
                    <button class="filter-btn active" onclick="filterTable('all')">All ({total})</button>
                    <button class="filter-btn" onclick="filterTable('passed')">Passed ({passed})</button>
                    <button class="filter-btn" onclick="filterTable('failed')">Failed ({failed})</button>
                    <button class="filter-btn" onclick="filterTable('skipped')">Skipped ({skipped})</button>
                </div>
            </div>

            <div style="overflow-x: auto;">
                <table id="testsTable">
                    <thead>
                        <tr>
                            <th style="width: 120px;">Test ID</th>
                            <th style="width: 160px;">Module</th>
                            <th>Test Description & Failure Details</th>
                            <th style="width: 100px;">Status</th>
                            <th style="width: 90px;">Priority</th>
                            <th style="width: 90px;" class="text-right">Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </section>
    </div>

    <script>
        function filterTable(status) {{
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            const rows = document.querySelectorAll('.test-row');
            rows.forEach(row => {{
                if (status === 'all') {{
                    row.style.display = '';
                }} else if (row.classList.contains('status-' + status)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
