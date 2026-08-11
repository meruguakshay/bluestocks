import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_bs, get_companies, get_pl, get_ratios

st.title("📈 Trend Analysis")

# Load all companies
df_companies = get_companies()

if df_companies.empty:
    st.error("No companies found in the database.")
else:
    # Autocomplete company search
    company_options = [
        f"{row['company_id']} - {row['company_name']}"
        for _, row in df_companies.iterrows()
    ]

    selected_option = st.selectbox(
        "Search Company",
        options=[""] + company_options,
        index=0,
        placeholder="Select a company to analyze trends...",
    )

    if selected_option == "":
        st.info("Please select a company to plot trends.")
    else:
        ticker = selected_option.split(" - ")[0]

        st.markdown("---")

        # Load historical statements
        df_pl = get_pl(ticker)
        df_bs = get_bs(ticker)
        df_rat = get_ratios(ticker)

        # Define available metrics
        METRIC_MAP = {
            "Revenue (Sales)": (df_pl, "sales", "₹ Cr"),
            "Operating Profit": (df_pl, "operating_profit", "₹ Cr"),
            "Net Profit": (df_pl, "net_profit", "₹ Cr"),
            "Total Assets": (df_bs, "total_assets", "₹ Cr"),
            "Borrowings (Debt)": (df_bs, "borrowings", "₹ Cr"),
            "Return on Equity (ROE)": (df_rat, "return_on_equity_pct", "%"),
            "Debt to Equity (D/E)": (df_rat, "debt_to_equity", ""),
            "Free Cash Flow (FCF)": (df_rat, "free_cash_flow_cr", "₹ Cr"),
            "Interest Coverage (ICR)": (df_rat, "interest_coverage", ""),
        }

        # Multi-metric selector
        selected_metrics = st.multiselect(
            "Select Metrics (up to 3)",
            options=list(METRIC_MAP.keys()),
            default=["Revenue (Sales)", "Net Profit"],
            max_selections=3,
        )

        if not selected_metrics:
            st.warning("Please select at least one metric to display.")
        else:
            # ────────────────────────────────────────────────────────
            # Plotly 10-Year Line Chart with YoY Annotations
            # ────────────────────────────────────────────────────────
            fig = go.Figure()

            # Find the complete year index list to align different metrics
            # Take year list from P&L (usually has all years)
            all_years = sorted(list(df_pl["year"].unique()))
            # Limit to last 10 years
            years_10 = all_years[-10:]

            for m_name in selected_metrics:
                df_source, col_name, unit = METRIC_MAP[m_name]

                # Fetch data points matching our 10-year list
                m_data = []
                for yr in years_10:
                    row = df_source[df_source["year"] == yr]
                    val = row.iloc[0][col_name] if not row.empty else np.nan
                    m_data.append(val)

                # Calculate YoY % changes
                yoy_annotations = []
                for i in range(len(m_data)):
                    if i == 0:
                        yoy_annotations.append("")  # First point has no YoY
                    else:
                        prev = m_data[i - 1]
                        curr = m_data[i]
                        if pd.notna(prev) and pd.notna(curr) and prev != 0:
                            yoy_val = ((curr - prev) / abs(prev)) * 100.0
                            sign = "+" if yoy_val > 0 else ""
                            yoy_annotations.append(f"{sign}{yoy_val:.1f}%")
                        else:
                            yoy_annotations.append("")

                # Unit suffix
                unit_suffix = f" ({unit})" if unit else ""

                # Add trace
                fig.add_trace(
                    go.Scatter(
                        x=years_10,
                        y=m_data,
                        name=m_name + unit_suffix,
                        mode="lines+markers+text",
                        text=yoy_annotations,
                        textposition="top center",
                        textfont=dict(size=8, color="#475569"),
                        line=dict(width=3),
                        marker=dict(size=7),
                        hovertemplate=f"<b>{m_name}</b><br>Year: %{{x}}<br>Value: %{{y:.2f}}{unit}<br>YoY: %{{text}}<extra></extra>",
                    )
                )

            fig.update_layout(
                xaxis_title="Financial Year",
                yaxis_title="Metric Value",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1
                ),
                margin=dict(l=40, r=40, t=50, b=20),
                height=500,
            )

            st.plotly_chart(fig, use_container_width=True)

            # ────────────────────────────────────────────────────────
            # Tabular view of raw data
            # ────────────────────────────────────────────────────────
            st.subheader("Historical Data Table")

            table_rows = []
            for yr in years_10:
                row_dict = {"Year": yr}
                for m_name in selected_metrics:
                    df_source, col_name, _ = METRIC_MAP[m_name]
                    row_s = df_source[df_source["year"] == yr]
                    val = row_s.iloc[0][col_name] if not row_s.empty else None
                    # Round floats
                    if isinstance(val, (float, np.float64)):
                        val = round(val, 2)
                    row_dict[m_name] = val
                table_rows.append(row_dict)

            df_table = pd.DataFrame(table_rows)
            st.dataframe(df_table, hide_index=True, use_container_width=True)
