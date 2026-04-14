"""
DataForge – Automated Data Pipeline & Intelligence Engine
==========================================================
Main entry point with CLI interface.

Usage:
    python main.py pipeline --input data/sample_sales.csv
    python main.py clean --input data/messy.xlsx --output output/clean.xlsx
    python main.py scrape --url https://example.com/table
    python main.py analyze --input data/sales.csv
    python main.py schedule --config pipeline
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

import click
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

import config
from utils import (
    DataCleaner,
    ExcelEngine,
    WebScraper,
    AIAnalyzer,
    ReportGenerator,
    Notifier,
    TaskScheduler,
)

# ── Logging Setup ────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    level=config.LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{message}</cyan>",
)
logger.add(
    config.LOG_DIR / "dataforge_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    level="DEBUG",
)

console = Console()


# ╔══════════════════════════════════════════════════════════════╗
# ║                     CLI APPLICATION                          ║
# ╚══════════════════════════════════════════════════════════════╝

BANNER = r"""
[bold blue]
  ██████╗  █████╗ ████████╗ █████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ██║  ██║███████║   ██║   ███████║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
  ██║  ██║██╔══██║   ██║   ██╔══██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
  ██████╔╝██║  ██║   ██║   ██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
[/bold blue]
[dim]  Automated Data Pipeline & Intelligence Engine  v1.0.0[/dim]
"""


@click.group()
@click.version_option(version="1.0.0", prog_name="DataForge")
def cli():
    """DataForge – Automated Data Pipeline & Intelligence Engine."""
    pass


# ── Full Pipeline ────────────────────────────────────────────

@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Input file path (CSV/Excel)")
@click.option("--output", "-o", "output_name", default=None, help="Output filename (without extension)")
@click.option("--context", "-c", default="", help="Business context for AI analysis")
@click.option("--no-ai", is_flag=True, help="Skip AI analysis")
@click.option("--notify", is_flag=True, help="Send notifications on completion")
@click.option("--format", "output_format", type=click.Choice(["excel", "html", "both"]), default="both")
def pipeline(input_path, output_name, context, no_ai, notify, output_format):
    """Run the full data pipeline: clean → analyze → report."""
    console.print(BANNER)
    console.print(Panel("🚀 Starting Full Data Pipeline", style="bold green"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = output_name or f"dataforge_{timestamp}"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Step 1: Load Data
        task = progress.add_task("📂 Loading data...", total=None)
        try:
            df = ExcelEngine.read(input_path)
            progress.update(task, description=f"📂 Loaded {len(df)} rows from {Path(input_path).name}")
        except Exception as e:
            console.print(f"[red]❌ Failed to load file: {e}[/red]")
            raise SystemExit(1)

        # Show raw data preview
        _print_preview(df, "📋 Raw Data Preview", max_rows=5)

        # Step 2: Clean Data
        progress.update(task, description="🧹 Cleaning data...")
        cleaner = DataCleaner(df)
        clean_df = (
            cleaner
            .rename_columns()
            .strip_whitespace()
            .remove_duplicates()
            .normalize_dates()
            .normalize_currency()
            .standardize_phone()
            .validate_emails()
            .normalize_case(case="title",
                            columns=[c for c in df.columns
                                     if any(kw in c.lower() for kw in ("name", "customer", "region", "product"))])
            .fill_missing()
            .get()
        )
        cleaning_report = cleaner.get_report()
        progress.update(task, description=f"🧹 Cleaned: {cleaning_report['rows_removed']} rows removed, {len(cleaning_report['operations'])} operations")

        # Print cleaning report
        _print_cleaning_report(cleaning_report)
        _print_preview(clean_df, "✨ Cleaned Data Preview", max_rows=5)

        # Step 3: AI Analysis
        ai_analysis = None
        if not no_ai:
            progress.update(task, description="🤖 Running AI analysis...")
            analyzer = AIAnalyzer()
            if analyzer.available:
                ai_analysis = analyzer.analyze(clean_df, context=context)
                progress.update(task, description="🤖 AI analysis complete")
            else:
                ai_analysis = analyzer.analyze(clean_df)  # Fallback
                progress.update(task, description="🤖 Statistical analysis complete (no API key)")

        # Print AI insights
        if ai_analysis:
            _print_insights(ai_analysis)

        # Step 4: Generate Outputs
        if output_format in ("excel", "both"):
            progress.update(task, description="📊 Generating Excel report...")
            excel_path = ExcelEngine.write(
                clean_df,
                filename=output_name,
                styled=True,
                include_charts=True,
            )
            console.print(f"  [green]✅ Excel saved:[/green] {excel_path}")

        if output_format in ("html", "both"):
            progress.update(task, description="📄 Generating HTML report...")
            reporter = ReportGenerator()
            html_path = reporter.generate(
                df=clean_df,
                title=context or f"DataForge Analysis – {Path(input_path).stem}",
                ai_analysis=ai_analysis,
                cleaning_report=cleaning_report,
                filename=output_name,
            )
            console.print(f"  [green]✅ HTML report:[/green] {html_path}")

        # Step 5: Notify
        if notify:
            progress.update(task, description="📬 Sending notifications...")
            stats = {
                "Rows Processed": str(len(clean_df)),
                "Rows Cleaned": str(cleaning_report["rows_removed"]),
                "Operations": str(len(cleaning_report["operations"])),
            }
            Notifier.send_slack_report(
                title="DataForge Pipeline Complete",
                summary=f"Processed `{Path(input_path).name}` successfully.",
                stats=stats,
            )

        progress.update(task, description="🎉 Pipeline completed!")

    console.print(Panel("✅ Pipeline finished successfully!", style="bold green"))


# ── Clean Only ───────────────────────────────────────────────

@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Input file path")
@click.option("--output", "-o", "output_name", default=None, help="Output filename")
@click.option("--format", "out_fmt", type=click.Choice(["csv", "excel"]), default="excel")
def clean(input_path, output_name, out_fmt):
    """Clean and standardize a data file."""
    console.print(BANNER)
    console.print(Panel("🧹 Data Cleaning Mode", style="bold cyan"))

    df = ExcelEngine.read(input_path)
    console.print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")

    cleaner = DataCleaner(df)
    clean_df = (
        cleaner
        .rename_columns()
        .strip_whitespace()
        .remove_duplicates()
        .normalize_dates()
        .normalize_currency()
        .standardize_phone()
        .validate_emails()
        .fill_missing()
        .get()
    )

    report = cleaner.get_report()
    _print_cleaning_report(report)

    output_name = output_name or f"clean_{Path(input_path).stem}"
    if out_fmt == "excel":
        path = ExcelEngine.write(clean_df, filename=output_name, styled=True)
    else:
        path = config.OUTPUT_DIR / f"{output_name}.csv"
        clean_df.to_csv(path, index=False)

    console.print(f"\n  [green]✅ Saved to:[/green] {path}")


# ── Scrape ───────────────────────────────────────────────────

@cli.command()
@click.option("--url", "-u", required=True, help="URL to scrape")
@click.option("--output", "-o", "output_name", default=None, help="Output filename")
@click.option("--dynamic", is_flag=True, help="Use Playwright for JS-rendered pages")
@click.option("--selector", "-s", default=None, help="CSS selector to wait for (dynamic mode)")
def scrape(url, output_name, dynamic, selector):
    """Scrape data from a web page."""
    console.print(BANNER)
    console.print(Panel(f"🌐 Scraping: {url}", style="bold cyan"))

    scraper = WebScraper()

    if dynamic:
        console.print("  Using Playwright (dynamic mode)...")
        result = scraper.scrape_dynamic(url, selector=selector)
        if isinstance(result, pd.DataFrame):
            df = result
        else:
            console.print(f"  [yellow]Returned raw HTML ({len(result)} chars)[/yellow]")
            return
    else:
        df = scraper.scrape_table(url)

    if df.empty:
        console.print("  [yellow]No data extracted[/yellow]")
        return

    console.print(f"  Extracted: {len(df)} rows, {len(df.columns)} columns")
    _print_preview(df, "🌐 Scraped Data", max_rows=10)

    output_name = output_name or f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    path = ExcelEngine.write(df, filename=output_name, styled=True)
    console.print(f"\n  [green]✅ Saved to:[/green] {path}")


# ── Analyze ──────────────────────────────────────────────────

@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Input file path")
@click.option("--context", "-c", default="", help="Business context")
@click.option("--focus", "-f", type=click.Choice(["general", "trends", "anomalies", "recommendations"]), default="general")
def analyze(input_path, context, focus):
    """Run AI-powered analysis on a data file."""
    console.print(BANNER)
    console.print(Panel("🤖 AI Analysis Mode", style="bold cyan"))

    df = ExcelEngine.read(input_path)
    console.print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")

    analyzer = AIAnalyzer()
    analysis = analyzer.analyze(df, context=context, focus=focus)

    _print_insights(analysis)

    # Also detect anomalies
    anomalies = analyzer.detect_anomalies(df)
    if anomalies:
        console.print(f"\n  🔍 [yellow]{len(anomalies)} anomaly groups detected[/yellow]")
        for anom in anomalies:
            console.print(f"     [{anom['column']}] {anom['count']} outliers (range: {anom['threshold']})")


# ── Schedule ─────────────────────────────────────────────────

@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Input file to process")
@click.option("--interval", type=click.Choice(["hourly", "daily", "weekly"]), default="daily")
@click.option("--time", "run_time", default="09:00", help="Time to run (HH:MM)")
def schedule(input_path, interval, run_time):
    """Schedule recurring pipeline runs."""
    console.print(BANNER)
    console.print(Panel("⏰ Scheduler Mode", style="bold cyan"))

    def pipeline_job():
        df = ExcelEngine.read(input_path)
        cleaner = DataCleaner(df)
        clean_df = (
            cleaner
            .rename_columns()
            .strip_whitespace()
            .remove_duplicates()
            .normalize_dates()
            .normalize_currency()
            .fill_missing()
            .get()
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ExcelEngine.write(clean_df, filename=f"scheduled_{timestamp}", styled=True)
        logger.info(f"Scheduled pipeline completed: {len(clean_df)} rows processed")

    scheduler = TaskScheduler()
    if interval == "hourly":
        scheduler.every_hour(pipeline_job, tag="DataForge Pipeline")
    elif interval == "daily":
        scheduler.every_day(pipeline_job, at=run_time, tag="DataForge Pipeline")
    elif interval == "weekly":
        scheduler.every_week(pipeline_job, at=run_time, tag="DataForge Pipeline")

    console.print(f"  📅 Scheduled: {interval} at {run_time}")
    console.print(f"  📂 Input: {input_path}")
    console.print(f"\n  [dim]Press Ctrl+C to stop[/dim]")
    scheduler.run()


# ╔══════════════════════════════════════════════════════════════╗
# ║                   DISPLAY HELPERS                            ║
# ╚══════════════════════════════════════════════════════════════╝

def _print_preview(df: pd.DataFrame, title: str, max_rows: int = 5) -> None:
    """Print a rich table preview of a DataFrame."""
    table = Table(title=title, show_lines=False, header_style="bold cyan")
    display_df = df.head(max_rows)

    for col in display_df.columns:
        table.add_column(str(col), overflow="fold")

    for _, row in display_df.iterrows():
        table.add_row(*[str(v) if pd.notna(v) else "—" for v in row])

    console.print(table)
    if len(df) > max_rows:
        console.print(f"  [dim]... and {len(df) - max_rows} more rows[/dim]")


def _print_cleaning_report(report: dict) -> None:
    """Print cleaning report as a rich panel."""
    lines = [f"  • {op}" for op in report["operations"]]
    lines.append(f"\n  📊 Shape: {report['original_shape']} → {report['cleaned_shape']}")
    lines.append(f"  🗑️  Rows removed: {report['rows_removed']}")
    lines.append(f"  ⚠️  Remaining nulls: {report['remaining_nulls']}")
    console.print(Panel("\n".join(lines), title="🔧 Cleaning Report", border_style="yellow"))


def _print_insights(analysis: dict) -> None:
    """Print AI analysis results."""
    # Summary
    if analysis.get("executive_summary"):
        console.print(Panel(analysis["executive_summary"], title="📊 Executive Summary", border_style="blue"))

    # Insights
    if analysis.get("key_insights"):
        console.print("\n  [bold cyan]💡 Key Insights:[/bold cyan]")
        for insight in analysis["key_insights"]:
            console.print(f"    → {insight}")

    # Recommendations
    if analysis.get("recommendations"):
        console.print("\n  [bold green]✅ Recommendations:[/bold green]")
        for rec in analysis["recommendations"]:
            console.print(f"    → {rec}")


# ── Config Check ─────────────────────────────────────────────

@cli.command()
def check():
    """Check configuration and environment setup."""
    console.print(BANNER)
    console.print(Panel("🔍 Configuration Check", style="bold cyan"))

    warnings = config.validate_config()

    console.print(f"  📁 Data dir:   {config.DATA_DIR}")
    console.print(f"  📁 Output dir: {config.OUTPUT_DIR}")
    console.print(f"  📁 Log dir:    {config.LOG_DIR}")

    if warnings:
        console.print(f"\n  [yellow]⚠️  {len(warnings)} warnings:[/yellow]")
        for w in warnings:
            console.print(f"    → {w}")
    else:
        console.print("\n  [green]✅ All checks passed![/green]")


# ── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    cli()
