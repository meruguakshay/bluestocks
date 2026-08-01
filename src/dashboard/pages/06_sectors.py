import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_companies, get_all_ratios_for_year, get_all_market_cap_for_year, get_connection

st.title("🍕 Sector Analysis")

# Sidebar Year Selector
selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    key="global_year"
)

# Fetch sectors list
df_companies = get_companies()

if df_companies.empty:
    st.error("No companies or sectors found.")
else:
    broad_sectors = sorted(df_companies["broad_sector"].dropna().unique().tolist())
    
    # Dropdown for sector selection
    selected_sector = st.selectbox(
        "Select Broad Sector",
        options=["All Sectors"] + broad_sectors,
        index=0
    )
    
    st.markdown("---")
    
    # ────────────────────────────────────────────────────────
    # Fetch and merge financial data for the selected year
    # ────────────────────────────────────────────────────────
    conn = get_connection()
    
    # Query sales from profit and loss for the selected year
    query_pl = f"SELECT company_id, sales FROM profitandloss WHERE year LIKE '{selected_year}-%'"
    df_pl = pd.read_sql(query_pl, conn)
    
    conn.close()
    
    # Fetch ratios and market cap
    df_ratios = get_all_ratios_for_year(selected_year)
    df_mcap = get_all_market_cap_for_year(selected_year)
    
    # Merge all
    df_all = pd.merge(df_companies, df_ratios, on="company_id", how="inner")
    df_all = pd.merge(df_all, df_mcap, on="company_id", how="inner")
    df_all = pd.merge(df_all, df_pl, on="company_id", how="inner")
    
    if df_all.empty:
        st.warning(f"No data available for the year {selected_year}.")
    else:
        # Filter by sector if not "All Sectors"
        if selected_sector != "All Sectors":
            df_filtered = df_all[df_all["broad_sector"] == selected_sector].copy()
        else:
            df_filtered = df_all.copy()
            
        if df_filtered.empty:
            st.warning(f"No companies found for sector '{selected_sector}' in {selected_year}.")
        else:
            # ────────────────────────────────────────────────────────
            # Bubble Chart
            # ────────────────────────────────────────────────────────
            st.subheader(f"Bubble Chart: Revenue vs ROE ({selected_sector})")
            st.markdown("*Bubble size represents Market Cap (in ₹ Crores), colored by sub-sector.*")
            
            # Clean values for plotting
            df_filtered = df_filtered.dropna(subset=["sales", "return_on_equity_pct", "market_cap_crore"])
            # Remove negative/zero market cap or sales from bubble size calculation
            df_plot = df_filtered[
                (df_filtered["market_cap_crore"] > 0) & 
                (df_filtered["sales"] > 0)
            ].copy()
            
            if df_plot.empty:
                st.info("No data available with positive Revenue and Market Cap.")
            else:
                fig_bubble = px.scatter(
                    df_plot,
                    x="sales",
                    y="return_on_equity_pct",
                    size="market_cap_crore",
                    color="sub_sector",
                    hover_name="company_name",
                    hover_data={
                        "company_id": True,
                        "sales": ":.2f",
                        "return_on_equity_pct": ":.2f",
                        "market_cap_crore": ":.2f",
                        "pe_ratio": ":.2f"
                    },
                    labels={
                        "sales": "Revenue (₹ Crores)",
                        "return_on_equity_pct": "ROE (%)",
                        "sub_sector": "Sub-Sector",
                        "market_cap_crore": "Market Cap (₹ Cr)",
                        "pe_ratio": "P/E Ratio"
                    },
                    height=500
                )
                fig_bubble.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_bubble, use_container_width=True)
                
            st.markdown("---")
            
            # ────────────────────────────────────────────────────────
            # Median KPI Bar Chart by Sub-sector
            # ────────────────────────────────────────────────────────
            st.subheader(f"Sub-Sector Median KPIs ({selected_sector})")
            
            # Calculate medians grouped by sub-sector
            df_medians = df_filtered.groupby("sub_sector")[[
                "return_on_equity_pct", "pe_ratio", "debt_to_equity"
            ]].median().reset_index()
            
            if df_medians.empty:
                st.info("No sub-sector median data available.")
            else:
                # Let user choose which KPI to display in the bar chart
                selected_kpi = st.selectbox(
                    "Select KPI for Median Comparison Chart",
                    options=[
                        "Return on Equity (%)", 
                        "P/E Ratio", 
                        "Debt-to-Equity Ratio"
                    ]
                )
                
                kpi_col_mapping = {
                    "Return on Equity (%)": ("return_on_equity_pct", "Median ROE (%)", "#10B981"),
                    "P/E Ratio": ("pe_ratio", "Median P/E", "#F59E0B"),
                    "Debt-to-Equity Ratio": ("debt_to_equity", "Median D/E", "#EF4444")
                }
                
                db_col, label_name, color_hex = kpi_col_mapping[selected_kpi]
                
                # Sort values for a clean chart
                df_medians_sorted = df_medians.dropna(subset=[db_col]).sort_values(by=db_col, ascending=False)
                
                fig_bar = px.bar(
                    df_medians_sorted,
                    x="sub_sector",
                    y=db_col,
                    text=db_col,
                    labels={
                        "sub_sector": "Sub-Sector",
                        db_col: label_name
                    },
                    color_discrete_sequence=[color_hex],
                    height=450
                )
                fig_bar.update_traces(
                    texttemplate='%{text:.2f}', 
                    textposition='outside'
                )
                fig_bar.update_layout(
                    xaxis_title="Sub-Sector",
                    yaxis_title=label_name,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
