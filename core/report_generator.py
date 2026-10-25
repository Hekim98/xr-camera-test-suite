"""
Report Generator Module:
Generates colored terminal console tables, machine-readable JSON logs,
and self-contained interactive HTML diagnostic reports.
"""

import json
import os
import time
from typing import Dict, Any


class ReportGenerator:
    # ANSI Color codes for clean terminal output
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

    def print_terminal_summary(self, suite_results: Dict[str, Any]) -> None:
        """Renders an executive summary table directly in the console."""
        device = suite_results.get("device", {})
        print("\n" + "=" * 80)
        print(f"{self.BOLD}{self.CYAN}XR CAMERA & SENSOR DIAGNOSTIC HARNESS{self.RESET}")
        print("=" * 80)
        print(f"Target Device:   {self.BOLD}{device.get('name', 'Unknown')}{self.RESET}")
        print(f"Hardware Type:   {device.get('type', 'Unknown')} | Profile: {device.get('profile_key')}")
        print(f"Cooling Profile: {device.get('cooling_type')} | Serial: {suite_results.get('serial', 'N/A')}")
        print(f"Timestamp:       {suite_results.get('timestamp')}")
        print("-" * 80)

        # Print each section
        categories = suite_results.get("results", {})
        total_passed = 0
        total_failed = 0
        total_warnings = 0

        for cat_key, cat_data in categories.items():
            cat_title = cat_data.get("category", cat_key)
            cat_status = cat_data.get("overall_status", "UNKNOWN")
            status_badge = self._badge(cat_status)
            print(f"\n{self.BOLD}{cat_title}{self.RESET} [{status_badge}]")

            for test_key, test in cat_data.get("tests", {}).items():
                t_name = test.get("name", test_key)
                t_status = test.get("status", "UNKNOWN")
                t_val = test.get("measured_value", "N/A")
                t_unit = test.get("unit", "")
                t_thresh = test.get("threshold", "N/A")

                if t_status == "PASS":
                    total_passed += 1
                elif t_status == "WARN":
                    total_warnings += 1
                else:
                    total_failed += 1

                val_str = f"{t_val} {t_unit}".strip()
                badge = self._badge(t_status)
                print(f"  • {t_name:<38} : {self.BOLD}{val_str:<18}{self.RESET} [Limit: {t_thresh}] -> {badge}")

        # Final Summary
        print("-" * 80)
        overall_status = "FAIL" if total_failed > 0 else ("WARN" if total_warnings > 0 else "PASS")
        print(f"OVERALL SUITE RESULT: {self._badge(overall_status, full=True)}")
        print(f"Tests Passed: {self.GREEN}{total_passed}{self.RESET} | Warnings: {self.YELLOW}{total_warnings}{self.RESET} | Failures: {self.RED}{total_failed}{self.RESET}")
        print("=" * 80 + "\n")

    def save_json_report(self, suite_results: Dict[str, Any], output_path: str) -> str:
        """Saves full telemetry and metrics to a JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(suite_results, f, indent=2)
        return output_path

    def save_html_report(self, suite_results: Dict[str, Any], output_path: str) -> str:
        """Generates a modern, single-page HTML report."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        device = suite_results.get("device", {})
        categories = suite_results.get("results", {})
        overall_status = suite_results.get("overall_status", "PASS")

        badge_color = "#10b981" if overall_status == "PASS" else ("#f59e0b" if overall_status == "WARN" else "#ef4444")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XR Camera Diagnostic Report - {device.get('name')}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: #334155;
            --pass: #10b981;
            --fail: #ef4444;
            --warn: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text-primary);
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            font-size: 24px;
        }}
        .meta {{
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.6;
        }}
        .overall-badge {{
            padding: 8px 20px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 16px;
            background: {badge_color}22;
            color: {badge_color};
            border: 1px solid {badge_color};
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .card h2 {{
            margin-top: 0;
            font-size: 18px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--text-secondary);
            font-weight: 600;
        }}
        .status-badge {{
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
            display: inline-block;
        }}
        .status-PASS {{ background: #10b98122; color: #10b981; border: 1px solid #10b981; }}
        .status-WARN {{ background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b; }}
        .status-FAIL {{ background: #ef444422; color: #ef4444; border: 1px solid #ef4444; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>XR Camera & Sensor Diagnostic Report</h1>
                <div class="meta">
                    <strong>Device:</strong> {device.get('name')} ({device.get('type')})<br>
                    <strong>Profile:</strong> {device.get('profile_key')} | <strong>Cooling:</strong> {device.get('cooling_type')}<br>
                    <strong>Timestamp:</strong> {suite_results.get('timestamp')}
                </div>
            </div>
            <div class="overall-badge">{overall_status}</div>
        </div>
"""
        # Append tables for each category
        for cat_key, cat_data in categories.items():
            html_content += f"""
        <div class="card">
            <h2>
                <span>{cat_data.get('category', cat_key)}</span>
                <span class="status-badge status-{cat_data.get('overall_status')}">{cat_data.get('overall_status')}</span>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric / Test Item</th>
                        <th>Measured Value</th>
                        <th>Specification Limit</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
"""
            for test_key, test in cat_data.get("tests", {}).items():
                t_name = test.get("name", test_key)
                t_val = f"{test.get('measured_value', 'N/A')} {test.get('unit', '')}".strip()
                t_lim = test.get("threshold", "N/A")
                t_stat = test.get("status", "UNKNOWN")
                t_det = test.get("details", "")

                html_content += f"""
                    <tr>
                        <td><strong>{t_name}</strong></td>
                        <td>{t_val}</td>
                        <td>{t_lim}</td>
                        <td><span class="status-badge status-{t_stat}">{t_stat}</span></td>
                        <td style="color: var(--text-secondary);">{t_det}</td>
                    </tr>
"""
            html_content += """
                </tbody>
            </table>
        </div>
"""

        html_content += """
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    def _badge(self, status: str, full: bool = False) -> str:
        if status == "PASS":
            return f"{self.GREEN}{self.BOLD}[ PASS ]{self.RESET}"
        elif status == "WARN":
            return f"{self.YELLOW}{self.BOLD}[ WARN ]{self.RESET}"
        else:
            return f"{self.RED}{self.BOLD}[ FAIL ]{self.RESET}"
