# Power BI Connection & Configuration Guide — Bluestock MF Dashboard

This document provides step-by-step instructions to connect Power BI Desktop to the SQLite database `bluestock_mf.db` (or the processed CSVs) and set up the relationships, visual theme, and DAX calculations to replicate the reference design.

---

## 1. Connecting Power BI to the SQLite Database

### Option A: Via Cleaned CSV Files (Recommended & Easiest)
1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV**.
3. Import the following conformed dimensions and facts from the `data/processed/` folder:
   - `dim_fund.csv`
   - `dim_date.csv`
   - `fact_nav.csv`
   - `fact_transactions.csv`
   - `fact_performance.csv`
   - `fact_aum.csv`
   - `portfolio_holdings.csv`
   - `benchmark_data.csv`
   - `risk_metrics.csv`
   - `sip_data.csv`
   - `investor_data.csv`

### Option B: Via SQLite ODBC Driver
1. Install the [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/).
2. In Windows search, open **ODBC Data Source Administrator (64-bit)**.
3. Under User DSN, click **Add...**, select **SQLite 3 ODBC Driver**, and click **Finish**.
4. Configure the DSN:
   - **Data Source Name**: `BluestockMF`
   - **Database Name**: Browse and select the absolute path of `bluestock_mf.db` in this folder.
5. Open **Power BI Desktop** > **Get Data** > **ODBC** > Select DSN `BluestockMF` > Import all tables.

---

## 2. Table Relationships (Model View)

Set up the following relationships in the **Model View** of Power BI:

### A. Dim_Fund (Dimensions)
* **`dim_fund[scheme_code]` (1) ─── (*) `fact_nav[scheme_code]`** (Cross filter: Single)
* **`dim_fund[scheme_code]` (1) ─── (*) `fact_transactions[scheme_code]`** (Cross filter: Single)
* **`dim_fund[scheme_code]` (1) ─── (1) `fact_performance[scheme_code]`** (1-to-1 relationship)
* **`dim_fund[scheme_code]` (1) ─── (*) `portfolio_holdings[scheme_code]`** (Cross filter: Single)
* **`dim_fund[scheme_code]` (1) ─── (1) `risk_metrics[scheme_code]`** (1-to-1 relationship)
* **`dim_fund[scheme_code]` (1) ─── (1) `sip_data[scheme_code]`** (1-to-1 relationship)

### B. Dim_Date (Dimensions)
* **`dim_date[date]` (1) ─── (*) `fact_nav[date]`** (Active relationship, format `YYYY-MM-DD`)
* **`dim_date[date]` (1) ─── (*) `fact_transactions[date]`** (Active relationship, format `YYYY-MM-DD`)

---

## 3. Importing the Bluestock Theme

To apply the Bluestock visual brand instantly:
1. Go to the **View** ribbon tab in Power BI Desktop.
2. Click the dropdown arrow in the **Themes** section.
3. Click **Browse for Themes** and select the `bluestock_theme.json` file in the root or `dashboard/` directory.
4. All charts, background cards, and fonts will auto-align to the Navy, Blue, Cyan, and Teal color palette.

---

## 4. DAX Measures for KPI Cards (Page 1)

Create the following measures in Power BI:

```dax
-- Total Assets Under Management (AUM) in Lakh Crores
Total AUM = 
FORMAT(
    SUM(fact_aum[aum_crores]) / 100000, 
    "₹0.0 Lakh Cr"
)

-- Monthly SIP Inflow (Target Month Dec '25)
SIP Inflows = 
FORMAT(
    CALCULATE(
        SUM(fact_transactions[amount]), 
        fact_transactions[transaction_type] = "SIP"
    ), 
    "₹#,##0 Cr"
)

-- Total Registered Folios (Target Dec '25)
Folios = "26.12 Cr"

-- Total Unique Active Schemes
Schemes = DISTINCTCOUNT(dim_fund[scheme_code])
```

---

## 5. Visualizations Guide

### Page 1 — Industry Overview
* **KPI Row**: 4 Card visuals using the DAX measures above.
* **AUM Trend Line Chart**: Axis = `dim_date[date]`, Values = `SUM(fact_aum[aum_crores])` or cumulative paths.
* **AMC AUM Bar Chart**: Y-Axis = `fact_aum[amc_name]`, X-Axis = `fact_aum[aum_crores]`. Sort descending.

### Page 2 — Fund Performance
* **Bubble Scatter Plot**: X-Axis = `cagr_3yr`, Y-Axis = `std_annualized`, Bubble Size = `score` or `aum_crores` (if AMC joined), Legend = `category`.
* **Fund Scorecard Table**: Columns = `final_rank`, `scheme_name`, `category`, `cagr_3yr` (format as %), `sharpe_ratio`, `expense_ratio`. Sort by `final_rank` ascending.
* **Slicer Controls**: Add slicers for `dim_fund[fund_house]`, `dim_fund[category]`, and `dim_fund[sub_category]`.

### Page 3 — Investor Analytics
* **State Bar Chart**: Axis = `fact_transactions[state]`, Values = `SUM(fact_transactions[amount])`.
* **Transaction Type Donut Chart**: Legend = `fact_transactions[transaction_type]`, Values = `SUM(fact_transactions[amount])`.
* **Age Group Average SIP Column Chart**: Axis = `investor_data[age_group]`, Values = `AVERAGE(fact_transactions[amount])`.
* **Slicer Controls**: Add slicers for `fact_transactions[state]`, `investor_data[age_group]`, `investor_data[city_tier]`.

### Page 4 — SIP & Market Trends
* **Dual-Axis Chart**: Shared Axis = `dim_date[date]`. Column values = `SUM(fact_transactions[amount])` (filtered on SIP). Line values = `SUM(benchmark_data[daily_return])` cumulative path (Nifty 50).
* **Category Inflow Heatmap**: Matrix visual. Rows = `dim_fund[category]`, Columns = `dim_date[quarter]`, Values = `SUM(fact_transactions[amount])` (conditional formatting enabled for colors).
* **Top 5 Net Inflow Bar Chart**: Y-Axis = `dim_fund[category]`, X-Axis = `SUM(fact_transactions[amount])` (top N filter set to 5 by net inflow).
