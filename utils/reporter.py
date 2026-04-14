"""
DataForge - Report Generator
==============================
Generate beautiful HTML reports with charts, tables,
and AI-powered narrative from processed data.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Template
from loguru import logger

from config import OUTPUT_DIR, TEMPLATES_DIR


# ── Inline Report Template ──────────────────────────────────
# Self-contained HTML with embedded CSS – no external dependencies.

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} – DataForge Report</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-2: #334155;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.3);
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #475569;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Header */
        .header {
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--accent), #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .header .subtitle {
            color: var(--text-muted);
            font-size: 1.1rem;
        }
        .header .timestamp {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }

        /* Cards */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: box-shadow 0.3s;
        }
        .card:hover {
            box-shadow: 0 0 20px var(--accent-glow);
        }
        .card h2 {
            font-size: 1.3rem;
            margin-bottom: 1rem;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Metric Grid */
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .metric {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }
        .metric .value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent);
        }
        .metric .label {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }

        /* Table */
        .table-wrapper { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        th {
            background: var(--surface-2);
            color: var(--accent);
            padding: 0.75rem 1rem;
            text-align: left;
            position: sticky;
            top: 0;
            font-weight: 600;
        }
        td {
            padding: 0.6rem 1rem;
            border-bottom: 1px solid var(--border);
        }
        tr:hover td {
            background: rgba(59, 130, 246, 0.05);
        }

        /* Lists */
        .insight-list {
            list-style: none;
            padding: 0;
        }
        .insight-list li {
            padding: 0.75rem 1rem;
            border-left: 3px solid var(--accent);
            margin-bottom: 0.5rem;
            background: rgba(59, 130, 246, 0.05);
            border-radius: 0 8px 8px 0;
        }
        .insight-list li.warning {
            border-left-color: var(--warning);
            background: rgba(245, 158, 11, 0.05);
        }
        .insight-list li.danger {
            border-left-color: var(--danger);
            background: rgba(239, 68, 68, 0.05);
        }
        .insight-list li.success {
            border-left-color: var(--success);
            background: rgba(34, 197, 94, 0.05);
        }

        /* Badge */
        .badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-info { background: var(--accent); color: white; }
        .badge-success { background: var(--success); color: white; }
        .badge-warning { background: var(--warning); color: #1a1a1a; }
        .badge-danger { background: var(--danger); color: white; }

        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem 0;
            margin-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        /* Cleaning Log */
        .log-entry {
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85rem;
            padding: 0.4rem 0;
            color: var(--text-muted);
        }
        .log-entry::before {
            content: '▸ ';
            color: var(--success);
        }

        @media print {
            body { background: white; color: #1a1a1a; }
            .card { border: 1px solid #ddd; box-shadow: none; }
            .header h1 { color: #1a1a1a; -webkit-text-fill-color: #1a1a1a; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">{{ subtitle }}</div>
            <div class="timestamp">Generated on {{ timestamp }}</div>
        </div>

        <!-- Key Metrics -->
        {% if metrics %}
        <div class="metrics">
            {% for m in metrics %}
            <div class="metric">
                <div class="value">{{ m.value }}</div>
                <div class="label">{{ m.label }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- AI Summary -->
        {% if summary %}
        <div class="card">
            <h2>📊 Executive Summary</h2>
            <p>{{ summary }}</p>
        </div>
        {% endif %}

        <!-- Insights -->
        {% if insights %}
        <div class="card">
            <h2>💡 Key Insights</h2>
            <ul class="insight-list">
                {% for item in insights %}
                <li>{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Data Quality -->
        {% if quality_issues %}
        <div class="card">
            <h2>⚠️ Data Quality Issues</h2>
            <ul class="insight-list">
                {% for item in quality_issues %}
                <li class="warning">{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Anomalies -->
        {% if anomalies %}
        <div class="card">
            <h2>🔍 Anomalies Detected</h2>
            <ul class="insight-list">
                {% for item in anomalies %}
                <li class="danger">{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Recommendations -->
        {% if recommendations %}
        <div class="card">
            <h2>✅ Recommendations</h2>
            <ul class="insight-list">
                {% for item in recommendations %}
                <li class="success">{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Data Preview -->
        {% if data_html %}
        <div class="card">
            <h2>📋 Data Preview (first {{ preview_rows }} rows)</h2>
            <div class="table-wrapper">
                {{ data_html }}
            </div>
        </div>
        {% endif %}

        <!-- Cleaning Log -->
        {% if cleaning_log %}
        <div class="card">
            <h2>🔧 Cleaning Operations Log</h2>
            {% for entry in cleaning_log %}
            <div class="log-entry">{{ entry }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <p>Powered by <strong>DataForge</strong> – Automated Data Pipeline & Intelligence Engine</p>
            <p>Report ID: {{ report_id }}</p>
        </div>
    </div>
</body>
</html>"""


class ReportGenerator:
    """
    Generate beautiful HTML reports from processed data.

    Usage:
        reporter = ReportGenerator()
        path = reporter.generate(
            df=clean_df,
            title="Q1 Sales Analysis",
            ai_analysis=analysis_results,
            cleaning_report=cleaner.get_report(),
        )
    """

    def __init__(self) -> None:
        self._template = Template(REPORT_TEMPLATE)

    def generate(
        self,
        df: pd.DataFrame,
        title: str = "DataForge Report",
        subtitle: str = "",
        ai_analysis: dict[str, Any] | None = None,
        cleaning_report: dict | None = None,
        preview_rows: int = 25,
        output_dir: Path | None = None,
        filename: str | None = None,
    ) -> Path:
        """
        Generate a complete HTML report.

        Args:
            df: Processed DataFrame
            title: Report title
            subtitle: Report subtitle
            ai_analysis: Results from AIAnalyzer.analyze()
            cleaning_report: Results from DataCleaner.get_report()
            preview_rows: Number of data rows to show in preview
        """
        out_dir = output_dir or OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        # Report ID
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = filename or f"report_{report_id}"
        filepath = out_dir / f"{fname}.html"

        # Build template context
        ctx: dict[str, Any] = {
            "title": title,
            "subtitle": subtitle or f"Automated analysis of {len(df)} records",
            "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "report_id": report_id,
            "preview_rows": preview_rows,
        }

        # Metrics
        ctx["metrics"] = self._build_metrics(df, cleaning_report)

        # AI Analysis sections
        if ai_analysis:
            ctx["summary"] = ai_analysis.get("executive_summary", "")
            ctx["insights"] = ai_analysis.get("key_insights", [])
            ctx["quality_issues"] = ai_analysis.get("data_quality_issues", [])
            ctx["anomalies"] = ai_analysis.get("anomalies", [])
            ctx["recommendations"] = ai_analysis.get("recommendations", [])
        else:
            ctx["summary"] = None
            ctx["insights"] = []
            ctx["quality_issues"] = []
            ctx["anomalies"] = []
            ctx["recommendations"] = []

        # Data preview table
        ctx["data_html"] = (
            df.head(preview_rows)
            .to_html(index=False, classes="data-table", na_rep="—")
        )

        # Cleaning log
        ctx["cleaning_log"] = (
            cleaning_report.get("operations", []) if cleaning_report else []
        )

        # Render
        html = self._template.render(**ctx)
        filepath.write_text(html, encoding="utf-8")
        logger.info(f"Report generated: {filepath}")

        return filepath

    def _build_metrics(
        self, df: pd.DataFrame, cleaning_report: dict | None
    ) -> list[dict]:
        """Build metric cards for the report header."""
        metrics = [
            {"value": f"{len(df):,}", "label": "Total Records"},
            {"value": str(len(df.columns)), "label": "Columns"},
            {"value": str(int(df.isna().sum().sum())), "label": "Missing Values"},
        ]

        if cleaning_report:
            metrics.append({
                "value": str(cleaning_report.get("rows_removed", 0)),
                "label": "Rows Cleaned",
            })
            metrics.append({
                "value": str(len(cleaning_report.get("operations", []))),
                "label": "Operations Applied",
            })

        # Add numeric highlights
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            first_num = numeric_cols[0]
            metrics.append({
                "value": f"{df[first_num].sum():,.0f}",
                "label": f"Total {first_num.replace('_', ' ').title()}",
            })

        return metrics
