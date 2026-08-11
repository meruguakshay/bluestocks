import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_bs, get_cf, get_companies, get_connection, get_pl, get_ratios

st.title("🏢 Company Profile")

# Load all companies for search list
df_companies = get_companies()

if df_companies.empty:
    st.error("No companies found in the database.")
else:
    # Autocomplete selection
    company_options = [
        f"{row['company_id']} - {row['company_name']}"
        for _, row in df_companies.iterrows()
    ]

    selected_option = st.selectbox(
        "Search Company Name or Ticker",
        options=[""] + company_options,
        index=0,
        placeholder="Type ticker or name...",
    )

    if selected_option == "":
        st.info("Please search and select a company from the dropdown.")
    else:
        # Extract ticker from option
        ticker = selected_option.split(" - ")[0]

        # Verify ticker exists in companies list
        company_row = df_companies[df_companies["company_id"] == ticker]
        if company_row.empty:
            st.error("Ticker not found — please try another")
        else:
            company_row = company_row.iloc[0]
            st.markdown("---")

            # ────────────────────────────────────────────────────────
            # Company Details Card
            # ────────────────────────────────────────────────────────
            card_col, logo_col = st.columns([3, 1])

            with card_col:
                st.subheader(company_row["company_name"])
                st.markdown(f"**NSE Ticker**: `{company_row['company_id']}`")
                st.markdown(
                    f"**Sector**: {company_row['broad_sector']} | **Sub-Sector**: {company_row['sub_sector']}"
                )
                st.markdown(
                    f"**About**: {company_row['about_company'] if pd.notna(company_row['about_company']) else 'N/A'}"
                )
                if pd.notna(company_row["website"]):
                    st.markdown(f"🌐 [Visit Website]({company_row['website']})")

            with logo_col:
                # If logo URL exists and is valid, show it, otherwise draw placeholder
                if (
                    pd.notna(company_row["company_logo"])
                    and company_row["company_logo"] != ""
                ):
                    st.image(
                        company_row["company_logo"],
                        width=150,
                        fallback="https://via.placeholder.com/150?text=No+Logo",
                    )
                else:
                    st.markdown(
                        """
                        <div style="width: 150px; height: 150px; background-color: #E5E7EB; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #4B5563;">
                            No Logo
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

            st.markdown("---")

            # ────────────────────────────────────────────────────────
            # Load statements & Calculate KPIs
            # ────────────────────────────────────────────────────────
            df_ratios = get_ratios(ticker)
            df_pl = get_pl(ticker)
            df_bs = get_bs(ticker)
            df_cf = get_cf(ticker)

            if df_ratios.empty or df_pl.empty or df_bs.empty:
                st.warning(
                    "Complete financial statements are not available for this company."
                )
            else:
                # Find latest year
                latest_ratio = df_ratios.iloc[-1]
                latest_year = latest_ratio["year"]

                # Fetch FCF from ratios or calculate CFO + CFI
                latest_fcf = latest_ratio.get("free_cash_flow_cr")
                if pd.isna(latest_fcf):
                    # Fallback to cashflow table calculation
                    latest_cf_row = df_cf[df_cf["year"] == latest_year]
                    if not latest_cf_row.empty:
                        latest_fcf = latest_cf_row.iloc[0].get(
                            "operating_activity", 0
                        ) + latest_cf_row.iloc[0].get("investing_activity", 0)

                # Dynamic ROCE calculation for the latest year
                # ROCE = EBIT / Capital Employed * 100
                latest_pl_row = df_pl[df_pl["year"] == latest_year]
                latest_bs_row = df_bs[df_bs["year"] == latest_year]
                latest_roce = None

                if not latest_pl_row.empty and not latest_bs_row.empty:
                    pbt = latest_pl_row.iloc[0].get("profit_before_tax", 0)
                    interest = latest_pl_row.iloc[0].get("interest", 0)
                    depr = latest_pl_row.iloc[0].get("depreciation", 0)
                    ebit = pbt + interest

                    equity = latest_bs_row.iloc[0].get(
                        "equity_capital", 0
                    ) + latest_bs_row.iloc[0].get("reserves", 0)
                    borrowings = latest_bs_row.iloc[0].get("borrowings", 0)
                    capital_employed = equity + borrowings
                    if capital_employed > 0:
                        latest_roce = (ebit / capital_employed) * 100

                # 6 KPI Tiles Layout
                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                kpi_col4, kpi_col5, kpi_col6 = st.columns(3)

                def fmt_p(val):
                    return f"{val:.2f}%" if pd.notna(val) else "N/A"

                def fmt_r(val):
                    return f"{val:.2f}" if pd.notna(val) else "N/A"

                def fmt_cr(val):
                    return f"₹{val:.1f} Cr" if pd.notna(val) else "N/A"

                kpi_col1.metric(
                    f"ROE ({latest_year})",
                    fmt_p(latest_ratio.get("return_on_equity_pct")),
                )
                kpi_col2.metric(f"ROCE ({latest_year})", fmt_p(latest_roce))
                kpi_col3.metric(
                    f"Net Profit Margin ({latest_year})",
                    fmt_p(latest_ratio.get("net_profit_margin_pct")),
                )
                kpi_col4.metric(
                    f"D/E Ratio ({latest_year})",
                    fmt_r(latest_ratio.get("debt_to_equity")),
                )
                kpi_col5.metric(
                    "Revenue CAGR (5yr)", fmt_p(latest_ratio.get("revenue_cagr_5yr"))
                )
                kpi_col6.metric(f"Free Cash Flow ({latest_year})", fmt_cr(latest_fcf))

                st.markdown("---")

                # ────────────────────────────────────────────────────────
                # Charts Section
                # ────────────────────────────────────────────────────────
                chart_pl_col, chart_ro_col = st.columns(2)

                # Prepare 10-year historical dataset
                df_pl_10yr = df_pl.tail(10)
                available_years = len(df_pl_10yr)
                if available_years < 10:
                    st.info(
                        f"ℹ️ Partial financial data available: Showing last {available_years} years."
                    )

                with chart_pl_col:
                    st.subheader("10-Year Revenue & Net Profit Trend")

                    fig_pl = go.Figure()
                    fig_pl.add_trace(
                        go.Bar(
                            x=df_pl_10yr["year"],
                            y=df_pl_10yr["sales"],
                            name="Revenue (Sales)",
                            marker_color="#1E3A8A",
                        )
                    )
                    fig_pl.add_trace(
                        go.Bar(
                            x=df_pl_10yr["year"],
                            y=df_pl_10yr["net_profit"],
                            name="Net Profit",
                            marker_color="#10B981",
                        )
                    )
                    fig_pl.update_layout(
                        barmode="group",
                        xaxis_title="Year",
                        yaxis_title="Amount (₹ Crores)",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        margin=dict(l=20, r=20, t=50, b=20),
                    )
                    st.plotly_chart(fig_pl, use_container_width=True)

                with chart_ro_col:
                    st.subheader("10-Year ROE vs ROCE Trend")

                    # Merge P&L, BS, Ratios to calculate historical ROCE
                    df_ratios_10yr = df_ratios.tail(10).copy()

                    roce_vals = []
                    for idx, row in df_ratios_10yr.iterrows():
                        yr = row["year"]
                        pl_row = df_pl[df_pl["year"] == yr]
                        bs_row = df_bs[df_bs["year"] == yr]

                        roce_val = None
                        if not pl_row.empty and not bs_row.empty:
                            pbt = pl_row.iloc[0].get("profit_before_tax", 0)
                            interest = pl_row.iloc[0].get("interest", 0)
                            ebit = pbt + interest

                            equity = bs_row.iloc[0].get(
                                "equity_capital", 0
                            ) + bs_row.iloc[0].get("reserves", 0)
                            borrowings = bs_row.iloc[0].get("borrowings", 0)
                            capital_employed = equity + borrowings
                            if capital_employed > 0:
                                roce_val = (ebit / capital_employed) * 100
                        roce_vals.append(roce_val)

                    df_ratios_10yr["calculated_roce"] = roce_vals

                    fig_ro = go.Figure()
                    fig_ro.add_trace(
                        go.Scatter(
                            x=df_ratios_10yr["year"],
                            y=df_ratios_10yr["return_on_equity_pct"],
                            name="ROE (%)",
                            line=dict(color="#3B82F6", width=3),
                            mode="lines+markers",
                        )
                    )
                    fig_ro.add_trace(
                        go.Scatter(
                            x=df_ratios_10yr["year"],
                            y=df_ratios_10yr["calculated_roce"],
                            name="ROCE (%)",
                            line=dict(color="#EF4444", width=3, dash="dash"),
                            mode="lines+markers",
                        )
                    )
                    fig_ro.update_layout(
                        xaxis_title="Year",
                        yaxis_title="Percentage (%)",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        margin=dict(l=20, r=20, t=50, b=20),
                    )
                    st.plotly_chart(fig_ro, use_container_width=True)

                st.markdown("---")

                # ────────────────────────────────────────────────────────
                # Pros & Cons Section
                # ────────────────────────────────────────────────────────
                st.subheader("Strengths & Weaknesses (Pros & Cons)")

                conn = get_connection()
                df_pc = pd.read_sql(
                    f"SELECT * FROM prosandcons WHERE company_id = '{ticker}'", conn
                )
                conn.close()

                if df_pc.empty:
                    st.info(
                        "No specific pros & cons listed in the database for this company."
                    )
                else:
                    pros_text = df_pc.iloc[0].get("pros")
                    cons_text = df_pc.iloc[0].get("cons")

                    pros_list = (
                        [p.strip() for p in pros_text.split("\n") if p.strip()]
                        if pd.notna(pros_text)
                        else []
                    )
                    cons_list = (
                        [c.strip() for c in cons_text.split("\n") if c.strip()]
                        if pd.notna(cons_text)
                        else []
                    )

                    pro_col, con_col = st.columns(2)

                    with pro_col:
                        st.markdown("**Pros**")
                        if not pros_list:
                            st.write("No strengths listed.")
                        for pro in pros_list:
                            st.markdown(f"✅ {pro}")

                    with con_col:
                        st.markdown("**Cons**")
                        if not cons_list:
                            st.write("No weaknesses listed.")
                        for con in cons_list:
                            st.markdown(f"❌ {con}")
