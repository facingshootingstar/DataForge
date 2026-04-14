# 🔥 DataForge – Automated Data Pipeline & Intelligence Engine

> **Turn messy spreadsheets into clean, analyzed, beautifully reported data — automatically.**

DataForge is a production-ready Python automation tool that eliminates manual data work. It ingests chaotic Excel/CSV files, cleans and standardizes them, runs AI-powered analysis, generates stunning reports, and can even scrape data from the web — all from a single command.

---

## 🎯 What It Solves

| Pain Point | DataForge Solution |
|---|---|
| *"I hate Excel"* | Auto-clean & format with professional styling |
| *"Data is inconsistent"* | Smart normalization (dates, phones, emails, currency) |
| *"Manual copy-paste"* | One-command pipeline from raw → clean → report |
| *"Need web data"* | Built-in scraper (static + JS-rendered pages) |
| *"No insights from data"* | AI-powered analysis with GPT-4o |
| *"Repetitive tasks"* | Built-in scheduler for recurring jobs |

---

## ✨ Key Features

- **🧹 Intelligent Data Cleaning** – Auto-detect and fix dates, phones, emails, currency, duplicates, missing values
- **📊 Beautiful Excel Output** – Professional formatting, charts, freeze panes, auto-filters
- **🤖 AI-Powered Analysis** – GPT-4o insights, anomaly detection, recommendations
- **📄 Stunning HTML Reports** – Dark-themed dashboards with metrics, insights, data previews
- **🌐 Web Scraping** – Dual-engine: requests+BS4 for static, Playwright for dynamic pages
- **⏰ Task Scheduling** – Hourly/daily/weekly automated pipeline runs
- **📬 Notifications** – Slack webhooks + email alerts on completion
- **🖥️ Beautiful CLI** – Rich terminal UI with progress bars and colored output

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/facingshootingstar/Automation.git
cd Automation

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (optional, for JS scraping)
playwright install chromium
```

### 2. Configure

```bash
# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env with your API keys
# OPENAI_API_KEY is required for AI analysis
# Slack/Email settings are optional
```

### 3. Generate Sample Data

```bash
python generate_sample_data.py
```

### 4. Run!

```bash
# Full pipeline (clean → analyze → report)
python main.py pipeline -i data/sample_sales.csv

# With AI analysis context
python main.py pipeline -i data/sample_sales.csv -c "Q1 2026 sales data for widget product line"

# Clean only
python main.py clean -i data/sample_sales.csv

# Scrape a web table
python main.py scrape -u "https://example.com/table"

# AI analysis only
python main.py analyze -i data/sample_sales.csv -c "Monthly sales data"

# Check config
python main.py check
```

---

## 📂 Project Structure

```
dataforge/
├── main.py                 # CLI entry point (5 commands)
├── config.py               # Centralized configuration
├── requirements.txt        # Pinned dependencies
├── generate_sample_data.py # Generate demo data
├── .env.example            # Environment template
├── .gitignore
├── data/                   # Input data directory
│   └── sample_sales.csv    # Demo messy data
├── output/                 # Generated reports & files
├── logs/                   # Application logs
└── utils/
    ├── __init__.py
    ├── cleaner.py           # Data cleaning engine
    ├── excel_engine.py      # Excel read/write with styling
    ├── scraper.py           # Web scraping (static + dynamic)
    ├── ai_analyzer.py       # AI-powered analysis
    ├── reporter.py          # HTML report generator
    ├── notifier.py          # Slack + email notifications
    └── scheduler.py         # Task scheduling
```

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| pandas | 2.2.3 | Data manipulation |
| openpyxl | 3.1.5 | Excel read/write |
| xlsxwriter | 3.2.2 | Advanced Excel formatting |
| requests | 2.32.3 | HTTP requests |
| beautifulsoup4 | 4.12.3 | HTML parsing |
| playwright | 1.49.1 | JS-rendered scraping |
| openai | 1.58.1 | GPT-4o AI analysis |
| click | 8.1.8 | CLI framework |
| rich | 13.9.4 | Terminal UI |
| jinja2 | 3.1.4 | HTML templating |
| schedule | 1.2.2 | Task scheduling |
| slack-sdk | 3.33.5 | Slack notifications |
| pydantic | 2.10.3 | Data validation |
| loguru | 0.7.3 | Logging |
| python-dotenv | 1.0.1 | Environment config |
| lxml | 5.3.0 | Fast HTML parser |

---

## 📸 Screenshots

### CLI Pipeline Output
```
  ██████╗  █████╗ ████████╗ █████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ██║  ██║███████║   ██║   ███████║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
  ...
  🚀 Starting Full Data Pipeline
  📂 Loaded 20 rows from sample_sales.csv
  🧹 Cleaned: 1 duplicate removed, 9 operations applied
  🤖 AI analysis complete
  📊 Excel saved: output/dataforge_20260415.xlsx
  📄 HTML report: output/dataforge_20260415.html
  ✅ Pipeline finished successfully!
```

### HTML Report
> Beautiful dark-themed report with metric cards, AI insights, data quality warnings, and interactive data preview table.

---

## 💰 Service Pricing Guide

This tool is designed to be sold as a **fixed-price automation service**:

| Tier | Price | What's Included |
|---|---|---|
| **Starter** | $500 | Data cleaning + Excel output (1 data source) |
| **Professional** | $1,000 | Full pipeline + AI analysis + HTML reports |
| **Enterprise** | $1,500–$2,000 | Everything + web scraping + scheduling + notifications + custom rules |

### Sales Pitch
> *"Stop wasting 5+ hours/week on manual data cleanup. I'll build you an automated pipeline that cleans your messy spreadsheets, catches errors automatically, and generates beautiful reports with AI-powered insights — all with a single command. One-time setup, runs forever."*

---

## 📄 License

MIT License — Use commercially, modify freely.

---

## 🤝 Author

Built with ❤️ by [facingshootingstar](https://github.com/facingshootingstar)

---

<p align="center">
  <strong>DataForge</strong> – Because your data deserves better than manual Excel work.
</p>
