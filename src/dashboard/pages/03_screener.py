import pandas as pd
import streamlit as st
from utils.db import get_all_market_cap_for_year, get_all_ratios_for_year, get_companies

st.title("🔍 Financial Screener")

# Sidebar Year Selector
selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    key="global_year",
)

# ────────────────────────────────────────────────────────
# Preset Definitions & Callback Functions
# ────────────────────────────────────────────────────────
SLIDER_DEFAULTS = {
    "roe": 0.0,
    "de": 10.0,
    "fcf": -2000.0,
    "rev_cagr": -50.0,
    "pat_cagr": -100.0,
    "opm": -50.0,
    "pe": 500.0,
    "pb": 100.0,
    "div_yield": 0.0,
    "icr": 0.0,
}

# Initialize session state variables for sliders
for key, val in SLIDER_DEFAULTS.items():
    state_key = f"scr_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = val


# Callback functions for buttons
def set_preset(
    roe=0.0,
    de=10.0,
    fcf=-2000.0,
    rev_cagr=-50.0,
    pat_cagr=-100.0,
    opm=-50.0,
    pe=500.0,
    pb=100.0,
    div_yield=0.0,
    icr=0.0,
):
    st.session_state["scr_roe"] = float(roe)
    st.session_state["scr_de"] = float(de)
    st.session_state["scr_fcf"] = float(fcf)
    st.session_state["scr_rev_cagr"] = float(rev_cagr)
    st.session_state["scr_pat_cagr"] = float(pat_cagr)
    st.session_state["scr_opm"] = float(opm)
    st.session_state["scr_pe"] = float(pe)
    st.session_state["scr_pb"] = float(pb)
    st.session_state["scr_div_yield"] = float(div_yield)
    st.session_state["scr_icr"] = float(icr)


def apply_quality():
    set_preset(roe=15.0, de=1.0, fcf=0.0)


def apply_value():
    set_preset(pe=20.0, pb=3.0)


def apply_growth():
    set_preset(pat_cagr=20.0, rev_cagr=10.0)


def apply_dividend():
    set_preset(div_yield=2.0)


def apply_debt_free():
    set_preset(de=0.0)


def apply_turnaround():
    set_preset(pat_cagr=20.0, opm=10.0, de=1.5)


def reset_filters():
    set_preset()


# Preset buttons layout in the main screen
st.subheader("Screening Presets")
p_col1, p_col2, p_col3, p_col4, p_col5, p_col6, p_col7 = st.columns(7)
p_col1.button("💎 Quality", on_click=apply_quality, use_container_width=True)
p_col2.button("🏷️ Value", on_click=apply_value, use_container_width=True)
p_col3.button("🚀 Growth", on_click=apply_growth, use_container_width=True)
p_col4.button("💰 Dividend", on_click=apply_dividend, use_container_width=True)
p_col5.button("🛡️ Debt-Free", on_click=apply_debt_free, use_container_width=True)
p_col6.button("🔄 Turnaround", on_click=apply_turnaround, use_container_width=True)
p_col7.button("❌ Reset", on_click=reset_filters, use_container_width=True)

st.markdown("---")

# ────────────────────────────────────────────────────────
# Sidebar Sliders (with bounds adjusted to actual data ranges)
# ────────────────────────────────────────────────────────
st.sidebar.header("Filter Criteria")

roe_min = st.sidebar.slider("Min ROE (%)", -50.0, 150.0, key="scr_roe", step=1.0)
de_max = st.sidebar.slider("Max Debt-to-Equity", 0.0, 5.0, key="scr_de", step=0.1)
fcf_min = st.sidebar.slider(
    "Min FCF (₹ Cr)", -1000.0, 20000.0, key="scr_fcf", step=50.0
)
rev_cagr_min = st.sidebar.slider(
    "Min 5yr Revenue CAGR (%)", -30.0, 100.0, key="scr_rev_cagr", step=1.0
)
pat_cagr_min = st.sidebar.slider(
    "Min 5yr PAT CAGR (%)", -50.0, 150.0, key="scr_pat_cagr", step=1.0
)
opm_min = st.sidebar.slider("Min OPM (%)", -20.0, 100.0, key="scr_opm", step=1.0)
pe_max = st.sidebar.slider("Max P/E Ratio", 0.0, 300.0, key="scr_pe", step=5.0)
pb_max = st.sidebar.slider("Max P/B Ratio", 0.0, 50.0, key="scr_pb", step=0.5)
div_yield_min = st.sidebar.slider(
    "Min Dividend Yield (%)", 0.0, 15.0, key="scr_div_yield", step=0.2
)
icr_min = st.sidebar.slider(
    "Min Interest Coverage (ICR)", 0.0, 50.0, key="scr_icr", step=1.0
)

# ────────────────────────────────────────────────────────
# Load and Filter Data
# ────────────────────────────────────────────────────────
df_ratios = get_all_ratios_for_year(selected_year)
df_mcap = get_all_market_cap_for_year(selected_year)
df_companies = get_companies()

if df_ratios.empty or df_companies.empty:
    st.warning(f"No screener data available for the year {selected_year}.")
else:
    # Merge datasets
    df_screener = pd.merge(df_ratios, df_mcap, on="company_id", how="inner")
    df_screener = pd.merge(
        df_screener,
        df_companies[["company_id", "company_name", "broad_sector"]],
        on="company_id",
        how="inner",
    )

    # Filter operations (handling NaNs by filling or logical checking)
    # Note: If a value is NaN, it won't pass filters unless we decide to keep/drop.
    # Typically, filters exclude NaNs. We will fill NaNs with safe default values for checks.
    df_filtered = df_screener.copy()

    df_filtered = df_filtered[
        df_filtered["return_on_equity_pct"].fillna(-999.0) >= roe_min
    ]
    df_filtered = df_filtered[df_filtered["debt_to_equity"].fillna(999.0) <= de_max]
    df_filtered = df_filtered[
        df_filtered["free_cash_flow_cr"].fillna(-99999.0) >= fcf_min
    ]
    df_filtered = df_filtered[
        df_filtered["revenue_cagr_5yr"].fillna(-999.0) >= rev_cagr_min
    ]
    df_filtered = df_filtered[
        df_filtered["pat_cagr_5yr"].fillna(-999.0) >= pat_cagr_min
    ]
    df_filtered = df_filtered[
        df_filtered["operating_profit_margin_pct"].fillna(-999.0) >= opm_min
    ]
    df_filtered = df_filtered[df_filtered["pe_ratio"].fillna(999.0) <= pe_max]
    df_filtered = df_filtered[df_filtered["pb_ratio"].fillna(999.0) <= pb_max]
    df_filtered = df_filtered[
        df_filtered["dividend_yield_pct"].fillna(-999.0) >= div_yield_min
    ]
    df_filtered = df_filtered[
        df_filtered["interest_coverage"].fillna(-999.0) >= icr_min
    ]

    # Sort by composite score
    df_filtered = df_filtered.sort_values(by="composite_quality_score", ascending=False)

    # ────────────────────────────────────────────────────────
    # Results Presentation
    # ────────────────────────────────────────────────────────
    match_count = len(df_filtered)
    st.markdown(f"### 📊 {match_count} companies match your filters")

    # Select columns to display
    display_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "interest_coverage",
    ]

    df_display = df_filtered[display_cols].copy()
    df_display.columns = [
        "Ticker",
        "Company Name",
        "Sector",
        "Quality Score",
        "ROE (%)",
        "D/E",
        "FCF (Cr)",
        "Rev CAGR 5yr (%)",
        "PAT CAGR 5yr (%)",
        "OPM (%)",
        "P/E",
        "P/B",
        "Div Yield (%)",
        "ICR",
    ]

    # Format values for display (replace NaN with N/A)
    # Streamlit dataframe handles floats natively, but let's round them
    for col in df_display.columns:
        if df_display[col].dtype == "float64":
            df_display[col] = df_display[col].round(2)

    st.dataframe(df_display, hide_index=True, use_container_width=True)

    # CSV Download Button
    csv_data = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Screener Results as CSV",
        data=csv_data,
        file_name=f"screener_results_{selected_year}.csv",
        mime="text/csv",
        use_container_width=True,
    )
