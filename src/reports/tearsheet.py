import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # Headless chart generation
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DB_PATH = "db/nifty100.db"
CHARTS_DIR = "scratch/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs("reports/tearsheets", exist_ok=True)


def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, (dict, pd.Series)):
        if len(obj) == 0:
            return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return obj[key] if key in obj else default
    except Exception:
        return default


def format_currency(val):
    if val is None or pd.isna(val) or val == "":
        return "N/A"
    return f"₹{to_float(val):.1f} Cr"


def format_pct(val):
    if val is None or pd.isna(val) or val == "":
        return "N/A"
    return f"{to_float(val):.1f}%"


def format_ratio(val):
    if val is None or pd.isna(val) or val == "":
        return "N/A"
    return f"{to_float(val):.2f}"


# ────────────────────────────────────────────────────────
# CHART GENERATION FUNCTIONS (MATPLOTLIB)
# ────────────────────────────────────────────────────────


def generate_revenue_profit_chart(ticker, df_pnl, dest_path):
    """Plots 10-year Revenue and Net Profit side-by-side bar chart"""
    if df_pnl.empty:
        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)
        ax.text(
            0.5,
            0.5,
            "Revenue & Profit Data Not Available",
            ha="center",
            va="center",
            fontsize=9,
            color="#4B5563",
        )
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.tight_layout()
        plt.savefig(dest_path, transparent=True)
        plt.close()
        return

    df_sorted = df_pnl.sort_values("year")
    # Take last 10 years of data
    df_last_10 = df_sorted.tail(10)

    years = [y.split("-")[0] for y in df_last_10["year"]]
    sales = [to_float(s) for s in df_last_10["sales"]]
    profit = [to_float(p) for p in df_last_10["net_profit"]]

    x = np.arange(len(years))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)

    ax.bar(x - width / 2, sales, width, label="Revenue", color="#002B49")
    ax.bar(x + width / 2, profit, width, label="Net Profit", color="#10B981")

    ax.set_ylabel("Amount (Cr)", fontsize=8, fontweight="bold", color="#002B49")
    ax.set_title(
        "10-Year Revenue & Net Profit Trend",
        fontsize=9,
        fontweight="bold",
        color="#002B49",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=45, fontsize=7)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Clean spines
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#002B49")
    ax.spines["bottom"].set_color("#002B49")
    ax.tick_params(axis="both", which="major", labelsize=7)

    plt.tight_layout()
    plt.savefig(dest_path, transparent=True)
    plt.close()


def generate_roe_roce_chart(ticker, df_pnl, df_bs, df_ratios, dest_path):
    """Plots ROE and ROCE dual-axis line chart"""
    if df_pnl.empty or df_bs.empty or df_ratios.empty:
        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)
        ax.text(
            0.5,
            0.5,
            "ROE & ROCE Trend Data Not Available",
            ha="center",
            va="center",
            fontsize=9,
            color="#4B5563",
        )
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.tight_layout()
        plt.savefig(dest_path, transparent=True)
        plt.close()
        return

    pnl_dict = df_pnl.set_index("year").to_dict(orient="index")
    bs_dict = df_bs.set_index("year").to_dict(orient="index")
    ratio_dict = df_ratios.set_index("year").to_dict(orient="index")

    union_years = sorted(
        list(
            set(df_pnl["year"])
            .intersection(df_bs["year"])
            .intersection(df_ratios["year"])
        )
    )
    union_years = union_years[-10:]  # last 10 years

    if not union_years:
        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)
        ax.text(
            0.5,
            0.5,
            "ROE & ROCE Trend Data Not Available",
            ha="center",
            va="center",
            fontsize=9,
            color="#4B5563",
        )
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.tight_layout()
        plt.savefig(dest_path, transparent=True)
        plt.close()
        return

    years = [y.split("-")[0] for y in union_years]
    roe = []
    roce = []

    for yr in union_years:
        # ROE from ratios table
        y_roe = to_float(ratio_dict.get(yr, {}).get("return_on_equity_pct"), np.nan)
        roe.append(y_roe)

        # Compute ROCE
        # ROCE = EBIT / (Equity + Reserves + Borrowings)
        yr_bs = bs_dict.get(yr, {})
        yr_pnl = pnl_dict.get(yr, {})

        equity_cap = to_float(yr_bs.get("equity_capital"))
        reserves = to_float(yr_bs.get("reserves"))
        borrowings = to_float(yr_bs.get("borrowings"))
        capital_employed = equity_cap + reserves + borrowings

        operating_profit = to_float(yr_pnl.get("operating_profit"))
        depreciation = to_float(yr_pnl.get("depreciation"))
        ebit = operating_profit - depreciation

        if capital_employed > 0.0:
            y_roce = (ebit / capital_employed) * 100.0
        else:
            y_roce = np.nan
        roce.append(y_roce)

    fig, ax1 = plt.subplots(figsize=(6, 2.5), dpi=300)

    ax1.plot(years, roe, color="#004C87", marker="o", linewidth=2, label="ROE (%)")
    ax1.set_xlabel("Year", fontsize=8, color="#002B49")
    ax1.set_ylabel("ROE (%)", fontsize=8, color="#004C87", fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#004C87", labelsize=7)
    ax1.tick_params(axis="x", rotation=45, labelsize=7)

    ax2 = ax1.twinx()
    ax2.plot(years, roce, color="#EF4444", marker="s", linewidth=2, label="ROCE (%)")
    ax2.set_ylabel("ROCE (%)", fontsize=8, color="#EF4444", fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#EF4444", labelsize=7)

    plt.title("ROE vs ROCE Trend", fontsize=9, fontweight="bold", color="#002B49")
    ax1.grid(axis="both", linestyle="--", alpha=0.5)

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=7)

    plt.tight_layout()
    plt.savefig(dest_path, transparent=True)
    plt.close()


def generate_balancesheet_composition_chart(ticker, df_bs, dest_path):
    """Plots Balance Sheet composition stacked bar chart"""
    if df_bs.empty:
        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)
        ax.text(
            0.5,
            0.5,
            "Balance Sheet Data Not Available",
            ha="center",
            va="center",
            fontsize=9,
            color="#4B5563",
        )
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.tight_layout()
        plt.savefig(dest_path, transparent=True)
        plt.close()
        return

    df_sorted = df_bs.sort_values("year")
    df_last_10 = df_sorted.tail(10)

    years = [y.split("-")[0] for y in df_last_10["year"]]
    equity = [
        to_float(r.get("equity_capital")) + to_float(r.get("reserves"))
        for _, r in df_last_10.iterrows()
    ]
    borrowings = [to_float(r.get("borrowings")) for _, r in df_last_10.iterrows()]
    other_liab = [
        to_float(r.get("other_liabilities")) for _, r in df_last_10.iterrows()
    ]

    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)

    # Stacked bars
    ax.bar(years, equity, label="Equity + Reserves", color="#002B49")
    ax.bar(years, borrowings, bottom=equity, label="Borrowings", color="#EF4444")
    bottom_3 = np.array(equity) + np.array(borrowings)
    ax.bar(
        years, other_liab, bottom=bottom_3, label="Other Liabilities", color="#D1D5DB"
    )

    ax.set_ylabel("Amount (Cr)", fontsize=8, color="#002B49", fontweight="bold")
    ax.set_title(
        "Balance Sheet Composition", fontsize=9, fontweight="bold", color="#002B49"
    )
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    plt.savefig(dest_path, transparent=True)
    plt.close()


def generate_cashflow_waterfall_chart(ticker, df_cf, dest_path):
    """Plots Cash Flow waterfall chart for latest year"""
    if df_cf.empty:
        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)
        ax.text(
            0.5,
            0.5,
            "Cash Flow Data Not Available",
            ha="center",
            va="center",
            fontsize=9,
            color="#4B5563",
        )
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.tight_layout()
        plt.savefig(dest_path, transparent=True)
        plt.close()
        return

    df_sorted = df_cf.sort_values("year")
    latest_row = df_sorted.iloc[-1]

    cfo = to_float(latest_row.get("operating_activity"))
    cfi = to_float(latest_row.get("investing_activity"))
    cff = to_float(latest_row.get("financing_activity"))
    net_cf = to_float(latest_row.get("net_cash_flow"))

    labels = ["CFO", "CFI", "CFF", "Net Cash"]
    values = [cfo, cfi, cff, net_cf]

    # Calculate waterfall steps
    cumulative = 0
    bottoms = []
    heights = []

    # CFO starts at 0
    bottoms.append(0)
    heights.append(cfo)
    cumulative += cfo

    # CFI starts at CFO
    bottoms.append(cumulative)
    heights.append(cfi)
    cumulative += cfi

    # CFF starts at CFO + CFI
    bottoms.append(cumulative)
    heights.append(cff)
    cumulative += cff

    # Net cash starts at 0
    bottoms.append(0)
    heights.append(net_cf)

    # Plot
    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=300)

    colors_list = ["#10B981" if h >= 0 else "#EF4444" for h in heights]
    colors_list[3] = "#002B49"  # Net Cash color

    ax.bar(labels, heights, bottom=bottoms, color=colors_list)

    # Add horizontal lines indicating connection
    for i in range(3):
        ax.plot(
            [i, i + 1],
            [bottoms[i] + heights[i], bottoms[i] + heights[i]],
            color="gray",
            linestyle=":",
            alpha=0.8,
        )

    ax.set_ylabel("Amount (Cr)", fontsize=8, color="#002B49", fontweight="bold")
    ax.set_title(
        f'Latest Year Cash Flow Waterfall ({latest_row.get("year")})',
        fontsize=9,
        fontweight="bold",
        color="#002B49",
    )
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="both", which="major", labelsize=7)

    plt.tight_layout()
    plt.savefig(dest_path, transparent=True)
    plt.close()


# ────────────────────────────────────────────────────────
# MAIN PDF TEARSHEET GENERATOR
# ────────────────────────────────────────────────────────


def generate_tearsheet(ticker, dest_path):
    """Generates the 2-page company tearsheet PDF using ReportLab"""
    # 1. Fetch data from SQLite
    conn = sqlite3.connect(DB_PATH)

    company = pd.read_sql(
        f"SELECT * FROM companies WHERE company_id = '{ticker}'", conn
    )
    if company.empty:
        conn.close()
        raise ValueError(f"Company {ticker} not found in database.")
    c_info = company.iloc[0]

    pnl = pd.read_sql(
        f"SELECT * FROM profitandloss WHERE company_id = '{ticker}' ORDER BY year", conn
    )
    bs = pd.read_sql(
        f"SELECT * FROM balancesheet WHERE company_id = '{ticker}' ORDER BY year", conn
    )
    cf = pd.read_sql(
        f"SELECT * FROM cashflow WHERE company_id = '{ticker}' ORDER BY year", conn
    )
    ratios = pd.read_sql(
        f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}' ORDER BY year",
        conn,
    )
    mcap = pd.read_sql(
        f"SELECT * FROM market_cap WHERE company_id = '{ticker}' ORDER BY year", conn
    )

    # Load sectors
    sector_id = c_info.get("sector_id")
    sector_row = pd.read_sql(
        f"SELECT broad_sector FROM sectors WHERE sector_id = {sector_id}", conn
    )
    sector_name = (
        sector_row.iloc[0]["broad_sector"] if not sector_row.empty else "Unknown"
    )

    conn.close()

    # Bypassed skip logic: process all companies
    valid_tables_years = []
    if not pnl.empty:
        valid_tables_years.append(set(pnl["year"]))
    if not bs.empty:
        valid_tables_years.append(set(bs["year"]))
    if not cf.empty:
        valid_tables_years.append(set(cf["year"]))

    if valid_tables_years:
        conformed_years = set.intersection(*valid_tables_years)
    else:
        conformed_years = set()

    if conformed_years:
        latest_year = sorted(list(conformed_years))[-1]
    else:
        all_years = (
            set(pnl["year"]).union(bs["year"]).union(cf["year"]).union(ratios["year"])
        )
        if not all_years:
            all_years = {"2024-03"}
        latest_year = sorted(list(all_years))[-1]

    latest_ratio = (
        ratios[ratios["year"] == latest_year].iloc[0]
        if not ratios[ratios["year"] == latest_year].empty
        else {}
    )
    latest_mcap = (
        mcap[mcap["year"] == latest_year].iloc[0]
        if not mcap[mcap["year"] == latest_year].empty
        else {}
    )
    latest_pnl = (
        pnl[pnl["year"] == latest_year].iloc[0]
        if not pnl[pnl["year"] == latest_year].empty
        else {}
    )
    latest_cf = (
        cf[cf["year"] == latest_year].iloc[0]
        if not cf[cf["year"] == latest_year].empty
        else {}
    )
    latest_bs = (
        bs[bs["year"] == latest_year].iloc[0]
        if not bs[bs["year"] == latest_year].empty
        else {}
    )

    # 2. Load Pros and Cons from output/pros_cons_generated.csv
    df_pros_cons = pd.DataFrame()
    if os.path.exists("output/pros_cons_generated.csv"):
        df_pros_cons = pd.read_csv("output/pros_cons_generated.csv")

    comp_pros_cons = (
        df_pros_cons[df_pros_cons["company_id"] == ticker]
        if not df_pros_cons.empty
        else pd.DataFrame()
    )
    pros_list = comp_pros_cons[comp_pros_cons["type"] == "pro"]["text"].tolist()
    cons_list = comp_pros_cons[comp_pros_cons["type"] == "con"]["text"].tolist()

    # If empty, default bullet
    if not pros_list:
        pros_list = ["Positive operating fundamentals."]
    if not cons_list:
        cons_list = ["Standard macro and sector risks."]

    # Get Capital Allocation Label
    # We retrieve it from ratios table or query cashflow_intelligence if available
    cap_alloc_label = "Unknown"
    if os.path.exists("output/cashflow_intelligence.xlsx"):
        df_cf_intel = pd.read_excel("output/cashflow_intelligence.xlsx")
        c_intel = df_cf_intel[df_cf_intel["company_id"] == ticker]
        if not c_intel.empty:
            cap_alloc_label = str(c_intel.iloc[0]["capital_allocation_label"])

    # 3. Generate the 4 charts and save as temporary image paths
    chart_rev_path = os.path.join(CHARTS_DIR, f"{ticker}_revenue_profit.png")
    chart_roe_path = os.path.join(CHARTS_DIR, f"{ticker}_roe_roce.png")
    chart_bs_path = os.path.join(CHARTS_DIR, f"{ticker}_balancesheet.png")
    chart_cf_path = os.path.join(CHARTS_DIR, f"{ticker}_cashflow.png")

    generate_revenue_profit_chart(ticker, pnl, chart_rev_path)
    generate_roe_roce_chart(ticker, pnl, bs, ratios, chart_roe_path)
    generate_balancesheet_composition_chart(ticker, bs, chart_bs_path)
    generate_cashflow_waterfall_chart(ticker, cf, chart_cf_path)

    # 4. Compile PDF Report using ReportLab SimpleDocTemplate
    doc = SimpleDocTemplate(
        dest_path,
        pagesize=A4,
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom Styles
    style_header = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    style_subheader = ParagraphStyle(
        "SubheaderStyle",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )
    style_tile_num = ParagraphStyle(
        "TileNum",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=HexColor("#002B49"),
        alignment=TA_CENTER,
    )
    style_tile_lbl = ParagraphStyle(
        "TileLbl",
        fontName="Helvetica",
        fontSize=7.5,
        textColor=HexColor("#4B5563"),
        alignment=TA_CENTER,
    )

    style_bullet_pro = ParagraphStyle(
        "BulletPro",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#065F46"),
    )
    style_bullet_con = ParagraphStyle(
        "BulletCon",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#991B1B"),
    )
    style_section_title = ParagraphStyle(
        "SectionTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=HexColor("#002B49"),
        spaceAfter=5,
    )
    style_badge = ParagraphStyle(
        "BadgeStyle",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    story = []

    # ────────────────────────────────────────────────────────
    # PAGE 1
    # ────────────────────────────────────────────────────────
    # Header bar Table
    comp_name = str(c_info.get("company_name"))
    header_data = [
        [
            Paragraph(f"{comp_name} ({ticker})", style_header),
            Paragraph(f"Sector: {sector_name} | FY: {latest_year}", style_subheader),
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.1 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#002B49")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 6 KPI Tiles in 2 rows of 3
    # Retrieve metrics safely
    rev_val = format_currency(safe_get(latest_pnl, "sales"))
    pat_val = format_currency(safe_get(latest_pnl, "net_profit"))
    roe_val = format_pct(safe_get(latest_ratio, "return_on_equity_pct"))
    de_val = format_ratio(safe_get(latest_ratio, "debt_to_equity"))
    cfo_val = format_currency(safe_get(latest_cf, "operating_activity"))
    mcap_val = format_currency(safe_get(latest_mcap, "market_cap_crore"))

    tile_data = [
        [
            [
                Paragraph(rev_val, style_tile_num),
                Paragraph("Revenue (Sales)", style_tile_lbl),
            ],
            [
                Paragraph(pat_val, style_tile_num),
                Paragraph("Net Profit (PAT)", style_tile_lbl),
            ],
            [
                Paragraph(roe_val, style_tile_num),
                Paragraph("Return on Equity (ROE)", style_tile_lbl),
            ],
        ],
        [
            [
                Paragraph(de_val, style_tile_num),
                Paragraph("Debt-to-Equity (D/E)", style_tile_lbl),
            ],
            [
                Paragraph(cfo_val, style_tile_num),
                Paragraph("Cash Flow from Ops (CFO)", style_tile_lbl),
            ],
            [
                Paragraph(mcap_val, style_tile_num),
                Paragraph("Market Capitalisation", style_tile_lbl),
            ],
        ],
    ]

    tile_table = Table(tile_data, colWidths=[2.43 * inch, 2.43 * inch, 2.43 * inch])
    tile_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F4F6F8")),
                ("BOX", (0, 0), (0, 0), 0.5, HexColor("#D1D5DB")),
                ("BOX", (1, 0), (1, 0), 0.5, HexColor("#D1D5DB")),
                ("BOX", (2, 0), (2, 0), 0.5, HexColor("#D1D5DB")),
                ("BOX", (0, 1), (0, 1), 0.5, HexColor("#D1D5DB")),
                ("BOX", (1, 1), (1, 1), 0.5, HexColor("#D1D5DB")),
                ("BOX", (2, 1), (2, 1), 0.5, HexColor("#D1D5DB")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(tile_table)
    story.append(Spacer(1, 15))

    # Page 1 Charts
    img_rev = Image(chart_rev_path, width=3.6 * inch, height=1.7 * inch)
    img_roe = Image(chart_roe_path, width=3.6 * inch, height=1.7 * inch)

    charts_table_p1 = Table([[img_rev, img_roe]], colWidths=[3.65 * inch, 3.65 * inch])
    charts_table_p1.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(charts_table_p1)

    story.append(Spacer(1, 10))

    # Brief Company Profile Table
    profile_title = Paragraph("Business Overview", style_section_title)
    about_text = str(c_info.get("about_company", "No business overview available."))
    # Truncate slightly to prevent overflow
    if len(about_text) > 400:
        about_text = about_text[:397] + "..."
    profile_p = Paragraph(
        about_text,
        ParagraphStyle(
            "AboutStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=HexColor("#374151"),
        ),
    )

    profile_table = Table([[profile_title], [profile_p]], colWidths=[7.3 * inch])
    profile_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(profile_table)

    story.append(PageBreak())

    # ────────────────────────────────────────────────────────
    # PAGE 2
    # ────────────────────────────────────────────────────────
    # Header bar Page 2
    header_table_p2 = Table(header_data, colWidths=[4.2 * inch, 3.1 * inch])
    header_table_p2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#002B49")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(header_table_p2)
    story.append(Spacer(1, 15))

    # Page 2 Charts
    img_bs = Image(chart_bs_path, width=3.6 * inch, height=1.7 * inch)
    img_cf = Image(chart_cf_path, width=3.6 * inch, height=1.7 * inch)

    charts_table_p2 = Table([[img_bs, img_cf]], colWidths=[3.65 * inch, 3.65 * inch])
    charts_table_p2.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(charts_table_p2)

    story.append(Spacer(1, 15))

    # Pros and Cons side-by-side Table (using green/red background borders)
    pro_bullet_flowables = [
        Paragraph(
            "<b>PROS (Key Strengths)</b>",
            ParagraphStyle(
                "ProTitle",
                parent=style_section_title,
                textColor=HexColor("#065F46"),
                spaceAfter=5,
            ),
        )
    ]
    for idx, pro_txt in enumerate(pros_list[:4]):  # limit to 4 to prevent overflow
        pro_bullet_flowables.append(Paragraph(f"• {pro_txt}", style_bullet_pro))
        pro_bullet_flowables.append(Spacer(1, 3))

    con_bullet_flowables = [
        Paragraph(
            "<b>CONS (Risks / Weaknesses)</b>",
            ParagraphStyle(
                "ConTitle",
                parent=style_section_title,
                textColor=HexColor("#991B1B"),
                spaceAfter=5,
            ),
        )
    ]
    for idx, con_txt in enumerate(cons_list[:4]):  # limit to 4 to prevent overflow
        con_bullet_flowables.append(Paragraph(f"• {con_txt}", style_bullet_con))
        con_bullet_flowables.append(Spacer(1, 3))

    pros_cons_table = Table(
        [[pro_bullet_flowables, con_bullet_flowables]],
        colWidths=[3.55 * inch, 3.55 * inch],
    )
    pros_cons_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), HexColor("#ECFDF5")),  # Soft green
                ("BACKGROUND", (1, 0), (1, 0), HexColor("#FEF2F2")),  # Soft red
                ("BOX", (0, 0), (0, 0), 0.5, HexColor("#A7F3D0")),
                ("BOX", (1, 0), (1, 0), 0.5, HexColor("#FCA5A5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    # We place pros and cons in a wrapper table to keep side-by-side structure
    wrapper_table = Table([[pros_cons_table]], colWidths=[7.3 * inch])
    wrapper_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(wrapper_table)

    story.append(Spacer(1, 15))

    # Capital Allocation Badge Table at bottom
    # We assign badge background color based on pattern
    badge_bg = HexColor("#002B49")  # Navy default
    if cap_alloc_label == "Shareholder Returns":
        badge_bg = HexColor("#10B981")  # Green
    elif cap_alloc_label == "Reinvestor":
        badge_bg = HexColor("#3B82F6")  # Blue
    elif "Distress" in cap_alloc_label:
        badge_bg = HexColor("#EF4444")  # Red
    elif "Growth" in cap_alloc_label:
        badge_bg = HexColor("#F59E0B")  # Amber

    badge_p = Paragraph(
        f"CAPITAL ALLOCATION PATTERN: {cap_alloc_label.upper()}", style_badge
    )
    badge_table = Table([[badge_p]], colWidths=[7.3 * inch])
    badge_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), badge_bg),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(badge_table)

    # Build Document
    doc.build(story)
    return True


# ────────────────────────────────────────────────────────
# CLI TEST EXECUTION
# ────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("TESTING TEARSHEET TEMPLATE GENERATION (DAY 33)")
    print("=" * 60)

    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]

    for ticker in test_tickers:
        dest_path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
        print(f"Generating test tearsheet for {ticker}...")
        try:
            success = generate_tearsheet(ticker, dest_path)
            if success:
                print(
                    f"  [OK] Saved tearsheet to {dest_path} ({os.path.getsize(dest_path)} bytes)"
                )
            else:
                print(
                    f"  [SKIPPED] Ticker {ticker} has less than 3 years of financial data."
                )
        except Exception as e:
            print(f"  [ERROR] Failed for {ticker}: {e}")
            raise e

    print("\nTearsheet layout testing completed successfully!")


if __name__ == "__main__":
    main()
