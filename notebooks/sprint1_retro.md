# Sprint 1 Retrospective — Data Foundation

**Theme:** Unified Financial Data Ingestion & Data Quality validation
**Date:** July 10, 2026

---

## 1. Accomplishments (Definition of Done Met)
* **Conformed Data Store:** Built a SQLite database (`db/nifty100.db`) containing 12 fully loaded, clean tables representing GICS sectors, company parameters, and historical financials.
* **Referential Integrity Checked:** Passed SQLite foreign key checks with **zero** violations (`PRAGMA foreign_key_check` returns `[]`).
* **16 Data Quality Rules Aligned:** Refactored `src/etl/validator.py` to enforce the 16 DQ rules from the technical specification, correctly classifying CRITICAL and WARNING severities.
* **Test Suite Success:** Wrote 60 pytest unit tests covering ticker/year normalization, loading logic, and validator rules. All 60 tests passed.
* **Audit Logs Generated:** Created `output/load_audit.csv` and `output/validation_failures.csv` tracking data health.

---

## 2. Challenges & Engineering Decisions
* **Year Column Text format:** The specification required years to be conformed to `YYYY-MM` strings (e.g. `2023-03`). The schema was updated from `INTEGER` to `TEXT` for all time-series tables, and year range parsing logic was corrected to prevent premature regex matching (e.g. matching range `2022-23` incorrectly).
* **Special Characters in Tickers:** Corrected `normalize_ticker` to preserve `&` and `-` so tickers like `M&M` and `BAJAJ-AUTO` load without key mismatches.
* **Referential Filtering:** Safely excluded the 8 extra companies present in core spreadsheets that were not part of the active 92-company index defined in the master `companies.xlsx` sheet, maintaining database referential integrity.
* **Standard Library Head Checks:** Substituted the external `requests` package with Python's built-in `urllib.request` library for document URL checks, reducing deployment overhead.

---

## 3. Next Sprint Preparation (Sprint 2: Ratio Engine)
* **Goal:** Populate the computed KPIs in `financial_ratios` for 92 companies × all historical years.
* **Focus Area:** Write profitability, leverage, growth (CAGR), and cash flow KPIs with robust edge-case handling (negative equity, zero sales).
