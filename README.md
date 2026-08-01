# Nifty 100 Financial Intelligence Platform

This platform provides institutional-grade tools to filter, compare, and analyze the financial health of the top 92 companies listed on the NSE (Nifty 100). It features a multi-page interactive Streamlit dashboard and a valuation analytics engine.

---

## Running the Dashboard

To run the Streamlit dashboard locally, follow these steps:

1. **Activate the Virtual Environment**:
   ```powershell
   .venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt python-dotenv
   ```
3. **Run Streamlit**:
   ```powershell
   streamlit run src/dashboard/app.py
   ```
   The dashboard will automatically open in your browser at `http://localhost:8501`.

---

## Dashboard Screens (8 Screens)

The dashboard contains the following multi-page screens located in the `src/dashboard/pages/` directory:

1. **01 Home / Overview (`01_home.py`)**:
   - Displays 6 high-level market metrics: Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR (5yr), and Debt-Free Companies.
   - Shows an interactive Plotly donut chart of the sector breakdown.
   - Displays a table of the top-5 quality companies ranked by their composite quality score.
   - A sidebar year selector (2019-2024) dynamically updates all KPIs.

2. **02 Company Profile (`02_profile.py`)**:
   - Includes an autocomplete text search for all 92 companies.
   - Displays a comprehensive company card with metadata (sector, sub-sector, NSE ticker, description).
   - Provides 6 latest KPIs (ROE, ROCE, NPM, D/E, 5yr Revenue CAGR, FCF).
   - Displays a 10-year bar chart for Revenue vs. Net Profit, and a dual-axis line chart comparing ROE and ROCE over 10 years.
   - Summarizes strengths (Pros) and weaknesses (Cons) from the database as check/cross badges.

3. **03 Financial Screener (`03_screener.py`)**:
   - Sidebar sliders for 10 core financial metrics (ROE, D/E, FCF, Revenue/PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR).
   - Preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround) that instantly auto-fill the sliders.
   - Live-updating results count and table sorted by composite quality score.
   - CSV export button to download the filtered results sheet.

4. **04 Peer Comparison (`04_peers.py`)**:
   - Allows selecting one of 11 peer groups and a target company.
   - Renders a multi-metric radar chart (using Plotly `Scatterpolar`) comparing the selected company with the peer group average across 8 normalized metrics.
   - Displays a side-by-side comparison table for all companies in the peer group, highlighting the selected company row in green.

5. **05 Trend Analysis (`05_trends.py`)**:
   - Search box to select any company.
   - Multi-metric selector allowing up to 3 metrics (Revenue, Profit, ROE, etc.) to be overlaid on a 10-year line chart.
   - Features text annotations representing YoY % growth on every data point.

6. **06 Sector Analysis (`06_sectors.py`)**:
   - Sector dropdown displaying a bubble chart (X=Revenue, Y=ROE, size=Market Cap, color=sub-sector) for Nifty 100 companies.
   - Visualizes sub-sector median KPI bar charts below the bubble chart.

7. **07 Capital Allocation Map (`07_capital.py`)**:
   - Displays a Plotly treemap of all 92 companies grouped by their 8 CFO/CFI/CFF sign-based capital allocation patterns.
   - Drill-down selector to list all companies categorized under the selected pattern.

8. **08 Annual Reports (`08_reports.py`)**:
   - Company search selector.
   - Lists available report years with direct clickable BSE PDF links.
   - Displays a red `Report unavailable` badge if status checks return a 404.

---

## Valuation Module

The valuation engine is implemented in `src/analytics/valuation.py` and is run using:
```powershell
.venv\Scripts\python.exe src/analytics/valuation.py
```

### Outputs Generated:
- **`output/valuation_summary.xlsx`**: Excel file containing all 92 companies with:
  - Valuation multiples (`P/E`, `P/B`, `EV/EBITDA`)
  - Computed `FCF_yield_pct` (`FCF / Market_Cap * 100`)
  - `5yr_median_PE` (2020-2024)
  - `PE_vs_sector_median_pct`
  - Overvaluation `flag` (`Caution` if P/E > 1.5x sector median, `Discount` if P/E < 0.7x sector median, else `Fair`).
- **`output/valuation_flags.csv`**: A CSV subset containing only companies flagged as `Caution` or `Discount` with supporting data.

---

## Sprint 4 Retrospective

### UX & Architecture Decisions
- **Path Portability**: Avoided relative path issues when running Streamlit from different working directories by dynamically resolving absolute paths relative to the file location.
- **Session State Synchronization**: Integrated the sidebar year selector into Streamlit's `st.session_state` so the user's selected year remains consistent across all pages during navigation.
- **Radar Chart Scaling**: Raw financial metrics (e.g. FCF in thousands vs. D/E ratio under 1) have massive scale differences. Normalized these to [10, 100] within peer groups for visual plotting on Scatterpolar, while maintaining raw values in the tooltips.
- **Styled Peer Tables**: Applied soft green backgrounds to highlight the active company within its peer group table.

### Data Edge Cases Handled
- **Non-March Financial Year Endings**: Tickers like `SIEMENS` report year-ends in September (`-09`), while others report in March (`-03`). The query functions dynamically sort by completeness of data and year-end matches to ensure exactly one record per company is loaded for each calendar year.
- **Missing Data Handling**: Handled NaN/Null financial values by displaying `N/A` in KPI metrics and filtering them out of sector median computations, avoiding zero-division crashes.

### Performance Findings
- **Data Load Times**: Measured the Company Profile load times for 5 tickers (ABB, INFY, TCS, HDFCBANK, SIEMENS). By leveraging sqlite3 query caching (`@st.cache_data`) and indexing, local page load times were compressed from several seconds to **under 6 milliseconds**, far below the 3-second SLA.
- **Report Status Caching**: Verifying 10+ URL links in real-time on the Reports page can block page load. Caching this function with a 24-hour TTL guarantees immediate page rendering on subsequent visits.
