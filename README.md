# Mutual Fund Analytics Project

## Project Structure

```
mutual_fund_project/
├── data/
│   ├── raw/          ← Original untouched CSV/API data
│   └── processed/    ← Cleaned and transformed data
├── notebooks/        ← Jupyter notebooks for exploration
├── sql/              ← SQL queries and schema scripts
├── dashboard/        ← Power BI / Plotly Dash files
├── reports/          ← Final PDFs and summaries
├── requirements.txt  ← Python dependencies
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Day 1 — Data Ingestion
- Load 10 CSV datasets
- Fetch live NAV from mfapi.in
- Validate AMFI codes
```
