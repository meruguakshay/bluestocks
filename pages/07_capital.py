import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.db import get_companies, get_all_market_cap_for_year, get_connection

st.title("🌳 Capital Allocation Map")

# Sidebar Year Selector
selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    key="global_year"
)

# ────────────────────────────────────────────────────────
# Helper classification function
# ────────────────────────────────────────────────────────
def get_capital_allocation_pattern(cfo, cfi, cff, net_profit):
    if cfo is None or pd.isna(cfo) or cfi is None or pd.isna(cfi) or cff is None or pd.isna(cff):
        return "-", "-", "-", "Unknown"
        
    cfo_val = float(cfo)
    cfi_val = float(cfi)
    cff_val = float(cff)
    
    cfo_sign = "+" if cfo_val >= 0.0 else "-"
    cfi_sign = "+" if cfi_val >= 0.0 else "-"
    cff_sign = "+" if cff_val >= 0.0 else "-"
    
    # Check high CFO/PAT
    is_high_cfo_pat = False
    if net_profit is not None and pd.notna(net_profit) and net_profit > 0.0:
        if (cfo_val / float(net_profit)) > 1.0:
            is_high_cfo_pat = True
            
    # Classify pattern
    if cfo_sign == "+" and cfi_sign == "-" and cff_sign == "-":
        if is_high_cfo_pat:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "-":
        label = "Liquidating Assets"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "+":
        label = "Distress Signal"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "+":
        label = "Growth Funded by Debt"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "+":
        label = "Cash Accumulator"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "-":
        label = "Pre-Revenue"
    elif cfo_sign == "+" and cfi_sign == "-" and cff_sign == "+":
        label = "Mixed"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "-":
        label = "Distress Signal"
    else:
        label = "Mixed"
        
    return cfo_sign, cfi_sign, cff_sign, label

# ────────────────────────────────────────────────────────
# Load cashflow and net profit data
# ────────────────────────────────────────────────────────
conn = get_connection()

# Query cash flow statements
query_cf = f"SELECT company_id, operating_activity, investing_activity, financing_activity FROM cashflow WHERE year LIKE '{selected_year}-%'"
df_cf = pd.read_sql(query_cf, conn)

# Query net profit from profitandloss
query_pl = f"SELECT company_id, net_profit FROM profitandloss WHERE year LIKE '{selected_year}-%'"
df_pl = pd.read_sql(query_pl, conn)

conn.close()

df_companies = get_companies()
df_mcap = get_all_market_cap_for_year(selected_year)

if df_cf.empty or df_companies.empty:
    st.warning(f"No cash flow data available for the year {selected_year}.")
else:
    # Merge datasets
    df_merged = pd.merge(df_companies, df_cf, on="company_id", how="inner")
    df_merged = pd.merge(df_merged, df_pl, on="company_id", how="inner")
    df_merged = pd.merge(df_merged, df_mcap[["company_id", "market_cap_crore"]], on="company_id", how="left")
    
    # Classify capital allocation for each company
    cfo_signs, cfi_signs, cff_signs, pattern_labels = [], [], [], []
    for idx, row in df_merged.iterrows():
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]
        pat = row["net_profit"]
        
        cfo_s, cfi_s, cff_s, label = get_capital_allocation_pattern(cfo, cfi, cff, pat)
        cfo_signs.append(cfo_s)
        cfi_signs.append(cfi_s)
        cff_signs.append(cff_s)
        pattern_labels.append(label)
        
    df_merged["CFO_Sign"] = cfo_signs
    df_merged["CFI_Sign"] = cfi_signs
    df_merged["CFF_Sign"] = cff_signs
    df_merged["pattern_label"] = pattern_labels
    df_merged["Sign_Pattern"] = df_merged["CFO_Sign"] + ", " + df_merged["CFI_Sign"] + ", " + df_merged["CFF_Sign"]
    
    # Handle any null market cap values for treemap sizing
    df_merged["market_cap_crore"] = df_merged["market_cap_crore"].fillna(100.0).clip(lower=1.0)
    
    # ────────────────────────────────────────────────────────
    # Plotly Treemap
    # ────────────────────────────────────────────────────────
    st.subheader(f"Treemap: Nifty 100 Companies by Capital Allocation Pattern ({selected_year})")
    st.markdown("*Box sizes represent Market Cap. Hover/click to inspect patterns and companies.*")
    
    fig_tree = px.treemap(
        df_merged,
        path=["pattern_label", "company_id"],
        values="market_cap_crore",
        color="pattern_label",
        color_discrete_sequence=px.colors.qualitative.Safe,
        hover_name="company_name",
        hover_data={
            "broad_sector": True,
            "operating_activity": ":.1f",
            "investing_activity": ":.1f",
            "financing_activity": ":.1f",
            "market_cap_crore": ":.2f"
        },
        labels={
            "pattern_label": "Allocation Pattern",
            "operating_activity": "CFO (Cr)",
            "investing_activity": "CFI (Cr)",
            "financing_activity": "CFF (Cr)",
            "market_cap_crore": "Market Cap (₹ Cr)"
        },
        height=550
    )
    fig_tree.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_tree, use_container_width=True)
    
    st.markdown("---")
    
    # ────────────────────────────────────────────────────────
    # Drill-down filter list
    # ────────────────────────────────────────────────────────
    st.subheader("Filter and Explore Companies by Pattern")
    
    unique_patterns = sorted(df_merged["pattern_label"].unique().tolist())
    selected_pattern = st.selectbox(
        "Select a Pattern to View Companies",
        options=unique_patterns
    )
    
    # Filter list
    df_filtered = df_merged[df_merged["pattern_label"] == selected_pattern].copy()
    
    st.markdown(f"**{len(df_filtered)} companies** classified as **{selected_pattern}**:")
    
    df_list_display = df_filtered[[
        "company_id", "company_name", "broad_sector", "operating_activity", "investing_activity", "financing_activity", "Sign_Pattern"
    ]].copy()
    
    df_list_display.columns = [
        "Ticker", "Company Name", "Sector", "CFO (₹ Cr)", "CFI (₹ Cr)", "CFF (₹ Cr)", "Sign Pattern (CFO, CFI, CFF)"
    ]
    
    # Round numbers for layout
    for col in ["CFO (₹ Cr)", "CFI (₹ Cr)", "CFF (₹ Cr)"]:
        df_list_display[col] = df_list_display[col].round(2)
        
    st.dataframe(df_list_display, hide_index=True, use_container_width=True)
