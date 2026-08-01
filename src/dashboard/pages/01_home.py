import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_companies, get_all_ratios_for_year, get_all_market_cap_for_year

# Set wide config (called on entry points, but good practice here too)
# Note: Streamlit pages inherit the page config from app.py, but we can set up the header.

st.title("📊 Nifty 100 Overview")

# Sidebar Year Selector (Syncs across pages via session state)
selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    key="global_year"
)

# Load data for selected year
df_ratios = get_all_ratios_for_year(selected_year)
df_mcap = get_all_market_cap_for_year(selected_year)
df_companies = get_companies()

# Handle empty data edge case
if df_ratios.empty or df_companies.empty:
    st.warning(f"No financial data available for the year {selected_year}.")
else:
    # ────────────────────────────────────────────────────────
    # KPI Calculations
    # ────────────────────────────────────────────────────────
    
    # 1. Average ROE
    avg_roe = df_ratios["return_on_equity_pct"].mean()
    
    # 2. Median P/E (join ratios and market cap)
    df_merged = pd.merge(df_ratios, df_mcap, on="company_id", how="inner")
    median_pe = df_merged["pe_ratio"].median() if not df_merged.empty else df_mcap["pe_ratio"].median()
    
    # 3. Median D/E
    median_de = df_ratios["debt_to_equity"].median()
    
    # 4. Total Companies
    total_companies = len(df_companies)
    
    # 5. Median Revenue CAGR 5yr
    median_rev_cagr = df_ratios["revenue_cagr_5yr"].median()
    
    # 6. Debt-Free Companies Count (D/E == 0)
    debt_free_count = (df_ratios["debt_to_equity"] <= 0.001).sum()
    
    # ────────────────────────────────────────────────────────
    # KPI Grid Layout
    # ────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    # Render with nice formatting and fallback to N/A
    def fmt_pct(val):
        return f"{val:.2f}%" if pd.notna(val) else "N/A"
    
    def fmt_num(val):
        return f"{val:.2f}" if pd.notna(val) else "N/A"

    col1.metric("Average ROE", fmt_pct(avg_roe))
    col2.metric("Median P/E", fmt_num(median_pe))
    col3.metric("Median D/E", fmt_num(median_de))
    col4.metric("Total Companies", f"{total_companies}")
    col5.metric("Median Revenue CAGR (5yr)", fmt_pct(median_rev_cagr))
    col6.metric("Debt-Free Companies", f"{debt_free_count}")
    
    st.markdown("---")
    
    # ────────────────────────────────────────────────────────
    # Charts & Tables
    # ────────────────────────────────────────────────────────
    chart_col, table_col = st.columns([1, 1.2])
    
    with chart_col:
        st.subheader("Sector Breakdown")
        # Donut Chart for Sector Breakdown
        sector_counts = df_companies["broad_sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Company Count"]
        
        fig = px.pie(
            sector_counts,
            values="Company Count",
            names="Sector",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism,
            height=400
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with table_col:
        st.subheader("Top-5 Quality Companies")
        # Top 5 by composite quality score
        # Join with companies to get names
        df_top = pd.merge(df_ratios, df_companies[["company_id", "company_name", "broad_sector"]], on="company_id", how="inner")
        
        # Sort and select top 5
        df_top = df_top.dropna(subset=["composite_quality_score"])
        df_top = df_top.sort_values(by="composite_quality_score", ascending=False).head(5)
        
        if not df_top.empty:
            df_top_display = df_top[[
                "company_id", 
                "company_name", 
                "broad_sector", 
                "composite_quality_score", 
                "return_on_equity_pct", 
                "debt_to_equity"
            ]].copy()
            
            # Format columns for presentation
            df_top_display.columns = ["Ticker", "Company Name", "Sector", "Quality Score", "ROE (%)", "D/E Ratio"]
            df_top_display["Quality Score"] = df_top_display["Quality Score"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            df_top_display["ROE (%)"] = df_top_display["ROE (%)"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
            df_top_display["D/E Ratio"] = df_top_display["D/E Ratio"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
            
            st.dataframe(df_top_display, hide_index=True, use_container_width=True)
        else:
            st.info("No composite quality score data available for this year.")
