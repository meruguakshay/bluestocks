import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_connection, get_peers

st.title("👥 Peer Comparison")

# Sidebar Year Selector
selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    key="global_year",
)

# 11 Peer Groups
peer_groups_list = [
    "Private Banks",
    "Public Sector Banks",
    "IT Services",
    "Pharmaceuticals",
    "Automobiles",
    "Life Insurance",
    "Oil & Gas",
    "Power & Utilities",
    "Steel",
    "FMCG",
    "Consumer Finance",
]

selected_group = st.selectbox("Select Peer Group", options=peer_groups_list, index=0)

# Fetch peers in the selected group
df_group = get_peers(selected_group)

if df_group.empty:
    st.warning("No companies found in this peer group.")
else:
    # Selected Company Selectbox
    company_options = [
        f"{row['company_id']} - {row['company_name']}" for _, row in df_group.iterrows()
    ]

    # Try to find benchmark company to default
    benchmark_idx = 0
    for idx, row in df_group.iterrows():
        if row["is_benchmark"] == 1:
            benchmark_idx = idx
            break

    selected_company_opt = st.selectbox(
        "Select Company to Analyze", options=company_options, index=int(benchmark_idx)
    )

    ticker = selected_company_opt.split(" - ")[0]

    st.markdown("---")

    # ────────────────────────────────────────────────────────
    # Fetch ratios and calculate ROCE for all peers in group
    # ────────────────────────────────────────────────────────
    peer_data_list = []

    conn = get_connection()

    for _, p_row in df_group.iterrows():
        pid = p_row["company_id"]

        # Get ratios for the selected year
        # Instead of get_ratios which returns a dataframe, we do a direct query to filter faster
        query_rat = f"""
        SELECT return_on_equity_pct, debt_to_equity, net_profit_margin_pct, free_cash_flow_cr,
               pat_cagr_5yr, revenue_cagr_5yr, eps_cagr_5yr
        FROM financial_ratios
        WHERE company_id = '{pid}' AND year LIKE '{selected_year}-%'
        """
        df_p_rat = pd.read_sql(query_rat, conn)

        # Get PL and BS for ROCE calculation
        query_pl = f"SELECT profit_before_tax, interest, depreciation FROM profitandloss WHERE company_id = '{pid}' AND year LIKE '{selected_year}-%'"
        query_bs = f"SELECT equity_capital, reserves, borrowings FROM balancesheet WHERE company_id = '{pid}' AND year LIKE '{selected_year}-%'"

        df_p_pl = pd.read_sql(query_pl, conn)
        df_p_bs = pd.read_sql(query_bs, conn)

        # Defaults
        roe = np.nan
        de = np.nan
        npm = np.nan
        fcf = np.nan
        pat_cagr = np.nan
        rev_cagr = np.nan
        eps_cagr = np.nan
        roce = np.nan

        if not df_p_rat.empty:
            rat_row = df_p_rat.iloc[0]
            roe = rat_row.get("return_on_equity_pct")
            de = rat_row.get("debt_to_equity")
            npm = rat_row.get("net_profit_margin_pct")
            fcf = rat_row.get("free_cash_flow_cr")
            pat_cagr = rat_row.get("pat_cagr_5yr")
            rev_cagr = rat_row.get("revenue_cagr_5yr")
            eps_cagr = rat_row.get("eps_cagr_5yr")

        if not df_p_pl.empty and not df_p_bs.empty:
            pl_row = df_p_pl.iloc[0]
            bs_row = df_p_bs.iloc[0]

            pbt = pl_row.get("profit_before_tax", 0) or 0
            interest = pl_row.get("interest", 0) or 0
            ebit = pbt + interest

            equity = (bs_row.get("equity_capital", 0) or 0) + (
                bs_row.get("reserves", 0) or 0
            )
            borrowings = bs_row.get("borrowings", 0) or 0
            capital_employed = equity + borrowings
            if capital_employed > 0:
                roce = (ebit / capital_employed) * 100

        peer_data_list.append(
            {
                "company_id": pid,
                "company_name": p_row["company_name"],
                "is_benchmark": p_row["is_benchmark"],
                "roe": roe,
                "roce": roce,
                "npm": npm,
                "de": de,
                "fcf": fcf,
                "pat_cagr": pat_cagr,
                "rev_cagr": rev_cagr,
                "eps_cagr": eps_cagr,
            }
        )

    conn.close()

    df_peers_metrics = pd.DataFrame(peer_data_list)

    # ────────────────────────────────────────────────────────
    # Radar Chart
    # ────────────────────────────────────────────────────────
    st.subheader("Radar Chart: Metrics vs Peer Group Average")

    # Check if the company has records for this year
    target_row = df_peers_metrics[df_peers_metrics["company_id"] == ticker]

    if target_row.empty:
        st.warning("No data available for the selected company in this year.")
    else:
        target_row = target_row.iloc[0]

        # Calculate group averages
        group_averages = df_peers_metrics.mean(numeric_only=True)

        # 8 radar metrics
        metrics = [
            ("ROE (%)", "roe"),
            ("ROCE (%)", "roce"),
            ("NPM (%)", "npm"),
            ("D/E Ratio", "de"),
            ("FCF (Cr)", "fcf"),
            ("PAT CAGR (%)", "pat_cagr"),
            ("Rev CAGR (%)", "rev_cagr"),
            ("EPS CAGR (%)", "eps_cagr"),
        ]

        # Perform relative scaling to group max for visualization layout
        # (Otherwise axes are skewed due to different metrics types/ranges)
        scaled_company = []
        scaled_average = []
        raw_company_values = []
        raw_average_values = []
        labels = []

        for name, col in metrics:
            labels.append(name)

            c_val = target_row[col]
            a_val = group_averages[col]

            raw_company_values.append(c_val)
            raw_average_values.append(a_val)

            # Group bounds
            min_val = df_peers_metrics[col].min()
            max_val = df_peers_metrics[col].max()

            # Simple Min-Max scaling to range [10, 100] for radar visibility
            if (
                pd.notna(c_val)
                and pd.notna(a_val)
                and pd.notna(max_val)
                and pd.notna(min_val)
                and max_val > min_val
            ):
                sc_c = 10 + (c_val - min_val) / (max_val - min_val) * 90
                sc_a = 10 + (a_val - min_val) / (max_val - min_val) * 90
            else:
                sc_c = 50.0
                sc_a = 50.0

            scaled_company.append(sc_c)
            scaled_average.append(sc_a)

        # Close the loop for radar polar chart
        labels_closed = labels + [labels[0]]
        scaled_company_closed = scaled_company + [scaled_company[0]]
        scaled_average_closed = scaled_average + [scaled_average[0]]

        # Format tooltips with raw values
        def fmt_raw(val, metric_name):
            if pd.isna(val):
                return "N/A"
            if "Ratio" in metric_name:
                return f"{val:.2f}"
            if "Cr" in metric_name:
                return f"₹{val:.1f} Cr"
            return f"{val:.2f}%"

        hover_company = [
            f"{lbl}: {fmt_raw(raw, lbl)}"
            for lbl, raw in zip(labels, raw_company_values)
        ]
        hover_company_closed = hover_company + [hover_company[0]]

        hover_average = [
            f"{lbl}: {fmt_raw(raw, lbl)} (Group Avg)"
            for lbl, raw in zip(labels, raw_average_values)
        ]
        hover_average_closed = hover_average + [hover_average[0]]

        # Plot Scatterpolar
        fig_radar = go.Figure()

        fig_radar.add_trace(
            go.Scatterpolar(
                r=scaled_company_closed,
                theta=labels_closed,
                fill="toself",
                name=ticker,
                line_color="#1E3A8A",
                hoverinfo="text",
                text=hover_company_closed,
            )
        )

        fig_radar.add_trace(
            go.Scatterpolar(
                r=scaled_average_closed,
                theta=labels_closed,
                fill="toself",
                name="Peer Group Avg",
                line_color="#F59E0B",
                hoverinfo="text",
                text=hover_average_closed,
            )
        )

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=False, range=[0, 105])),
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20),
            height=450,
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    # ────────────────────────────────────────────────────────
    # Peer Comparison Table
    # ────────────────────────────────────────────────────────
    st.subheader("Side-by-Side Peer Comparison Table")

    df_peer_display = df_peers_metrics[
        [
            "company_id",
            "company_name",
            "roe",
            "roce",
            "npm",
            "de",
            "fcf",
            "pat_cagr",
            "rev_cagr",
            "eps_cagr",
        ]
    ].copy()

    df_peer_display.columns = [
        "Ticker",
        "Company Name",
        "ROE (%)",
        "ROCE (%)",
        "NPM (%)",
        "D/E Ratio",
        "FCF (Cr)",
        "PAT CAGR (%)",
        "Rev CAGR (%)",
        "EPS CAGR (%)",
    ]

    # Round floats for layout presentation
    for col in df_peer_display.columns:
        if df_peer_display[col].dtype == "float64":
            df_peer_display[col] = df_peer_display[col].round(2)

    # Highlight the selected company's row in green
    def highlight_selected(row, selected_ticker):
        if row["Ticker"] == selected_ticker:
            return [
                "background-color: #D1FAE5; font-weight: bold; color: #111827;"
            ] * len(row)
        return [""] * len(row)

    styled_df = df_peer_display.style.apply(
        highlight_selected, axis=1, selected_ticker=ticker
    )

    st.dataframe(styled_df, hide_index=True, use_container_width=True)
