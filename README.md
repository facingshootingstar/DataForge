<div align="center">

# ⚙️ DataForge — Automated Data Cleaning & Analysis Pipeline

**Turn messy spreadsheets into clean, analyzed, beautifully reported data — automatically. Ingest chaotic Excel/CSV files, clean and standardize them, run AI-powered analysis, and generate stunning reports from a single command.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[Features](#-key-features) · [Quick Start](#-quick-start) · [Usage](#-usage) · [Output](#-output)

</div>

---

## 📌 About This Project

A personal automation project exploring end-to-end data pipeline design — from ingestion of messy data through AI-powered analysis to professional report generation. This tool demonstrates expertise in data engineering, OpenAI API integration, Excel automation, HTML report generation, and CLI design — built as a hands-on learning exercise and portfolio showcase.

---

## ✨ Key Features

- 🧹 **Intelligent Data Cleaning** — Auto-detect and fix dates, phones, emails, currency, duplicates, missing values
- 📊 **Beautiful Excel Output** — Professional formatting, charts, freeze panes, auto-filters
- 🤖 **AI-Powered Analysis** — GPT-4o insights, anomaly detection, recommendations
- 📄 **Stunning HTML Reports** — Dark-themed dashboards with metrics, insights, data previews
- 🌐 **Web Scraping** — Dual-engine: requests+BS4 for static pages, Playwright for dynamic pages
- ⏰ **Task Scheduling** — Hourly/daily/weekly automated pipeline runs
- 📬 **Notifications** — Slack webhooks + email alerts on completion
- 🖥️ **Beautiful CLI** — Rich terminal UI with progress bars and colored output

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Core runtime |
| OpenAI API | GPT-4o for data analysis |
| Pandas | Data cleaning & manipulation |
| openpyxl | Styled Excel generation |
| Playwright | Dynamic web scraping |
| BeautifulSoup4 | Static HTML parsing |
| Rich | Terminal UI |
| APScheduler | Task scheduling |
| python-dotenv | Environment configuration |

---

## 📁 Project Structure

```
DataForge/
├── main.py                   # CLI entry point (5 commands)
├── config.py                 # Centralized configuration
├── requirements.txt          # Pinned dependencies
├── generate_sample_data.py   # Generate demo data
├── .env.example              # Environment template
├── .gitignore
├── data/                     # Input data directory
│   └── sample_sales.csv      # Demo messy data
├── output/                   # Generated reports & files
├── logs/                     # Application logs
└── utils/
    ├── __init__.py
    ├── cleaner.py            # Data cleaning engine
    ├── excel_engine.py       # Excel read/write with styling
    ├── scraper.py            # Web scraping (static + dynamic)
    ├── ai_analyzer.py        # AI-powered analysis
    ├── reporter.py           # HTML report generator
    ├── notifier.py           # Slack + email notifications
    └── scheduler.py          # Task scheduling
```

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/facingshootingstar/DataForge.git
cd DataForge

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (optional, for JS scraping)
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
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
```

---

## 📖 Usage

### Full Pipeline
```bash
python main.py pipeline -i data/sample_sales.csv
```

### Clean Only
```bash
python main.py clean -i data/sample_sales.csv
```

### AI Analysis Only
```bash
python main.py analyze -i data/sample_sales.csv -c "Monthly sales data"
```

### Scrape a Web Table
```bash
python main.py scrape -u "https://example.com/table"
```

### Check Configuration
```bash
python main.py check
```

---

## 📤 Output

### CLI Pipeline Output
```
🚀 Starting Full Data Pipeline
📂 Loaded 20 rows from sample_sales.csv
🧹 Cleaned: 1 duplicate removed, 9 operations applied
🤖 AI analysis complete
📊 Excel saved: output/dataforge_20260415.xlsx
📄 HTML report: output/dataforge_20260415.html
✅ Pipeline finished successfully!
```

### Excel Output
Professional workbook with:
- Cleaned data with formatting, freeze panes, auto-filters
- Charts and conditional formatting
- Summary statistics sheet

### HTML Report
Beautiful dark-themed report with:
- Metric cards and key statistics
- AI-powered insights and recommendations
- Data quality warnings
- Interactive data preview table

---

## ⚖️ Ethical Use & Disclaimer

> **⚠️ This tool is for educational and personal use.**

- When using the web scraping feature, respect website Terms of Service and `robots.txt`.
- Use built-in rate limiting for responsible scraping.
- Comply with data protection laws (GDPR, CCPA) when handling personal data.
- The author assumes **no liability** for misuse.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">

**Built with ❤️ by [@facingshootingstar](https://github.com/facingshootingstar)**

*Made for personal learning and portfolio purposes.*

</div>
