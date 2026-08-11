import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DB_PATH = "db/nifty100.db"
os.makedirs("reports/portfolio", exist_ok=True)


def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def get_trend_arrow(latest, previous):
    """Returns (arrow_char, color_hex, text_change) based on YoY difference"""
    if latest is None or previous is None or pd.isna(latest) or pd.isna(previous):
        return "→", "#6B7280", "N/A"

    l = float(latest)
    p = float(previous)

    if p == 0.0:
        if l > 0.0:
            return "↑", "#10B981", "+100%+"
        elif l < 0.0:
            return "↓", "#EF4444", "-100%+"
        else:
            return "→", "#6B7280", "0.0%"

    rel_change = (l - p) / abs(p)
    pct_change = rel_change * 100.0

    if rel_change > 0.02:
        return "↑", "#10B981", f"+{pct_change:.1f}%"
    elif rel_change < -0.02:
        return "↓", "#EF4444", f"{pct_change:.1f}%"
    else:
        return "→", "#6B7280", f"{pct_change:+.1f}%"


def main():
    print("=" * 60)
    print("GENERATING PORTFOLIO SUMMARY PDF (DAY 35)")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Get all companies sorted by ticker (company_id)
    df_companies = pd.read_sql(
        "SELECT company_id, company_name, sector_id FROM companies ORDER BY company_id",
        conn,
    )
    df_sectors = pd.read_sql("SELECT sector_id, broad_sector FROM sectors", conn)

    # Load financial tables
    df_pnl = pd.read_sql(
        "SELECT company_id, year, sales, net_profit, operating_profit, depreciation FROM profitandloss",
        conn,
    )
    df_bs = pd.read_sql(
        "SELECT company_id, year, equity_capital, reserves, borrowings FROM balancesheet",
        conn,
    )
    df_ratio = pd.read_sql(
        "SELECT company_id, year, return_on_equity_pct, debt_to_equity FROM financial_ratios",
        conn,
    )
    df_mcap = pd.read_sql(
        "SELECT company_id, year, market_cap_crore FROM market_cap", conn
    )

    conn.close()

    sector_map = dict(zip(df_sectors["sector_id"], df_sectors["broad_sector"]))
    df_companies["broad_sector"] = df_companies["sector_id"].map(sector_map)

    tickers = df_companies["company_id"].tolist()

    # Setup document
    dest_path = "reports/portfolio/portfolio_summary.pdf"
    doc = SimpleDocTemplate(
        dest_path,
        pagesize=A4,
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_header = ParagraphStyle(
        "PortHeader",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.white,
    )
    style_subheader = ParagraphStyle(
        "PortSubheader",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )
    style_sec_title = ParagraphStyle(
        "PortSecTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=HexColor("#002B49"),
        spaceAfter=8,
    )

    style_cell_lbl = ParagraphStyle(
        "CellLbl",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=HexColor("#374151"),
    )
    style_cell_val = ParagraphStyle(
        "CellVal",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#1F2937"),
    )
    style_cell_val_bold = ParagraphStyle(
        "CellValBold",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=HexColor("#111827"),
    )

    story = []

    for idx, ticker in enumerate(tickers):
        comp_info = df_companies[df_companies["company_id"] == ticker].iloc[0]
        comp_name = comp_info["company_name"]
        sector_name = comp_info["broad_sector"]

        # Sort values by year
        c_pnl = df_pnl[df_pnl["company_id"] == ticker].sort_values("year")
        c_bs = df_bs[df_bs["company_id"] == ticker].sort_values("year")
        c_ratio = df_ratio[df_ratio["company_id"] == ticker].sort_values("year")
        c_mcap = df_mcap[df_mcap["company_id"] == ticker].sort_values("year")

        # Identify conformed years
        union_years = sorted(
            list(
                set(c_pnl["year"])
                .intersection(c_bs["year"])
                .intersection(c_ratio["year"])
            )
        )

        latest_year = "N/A"
        prev_year = "N/A"

        lat_data = {}
        prev_data = {}

        if len(union_years) >= 1:
            latest_year = union_years[-1]
            # Fetch latest
            lat_pnl = (
                c_pnl[c_pnl["year"] == latest_year].iloc[0]
                if not c_pnl[c_pnl["year"] == latest_year].empty
                else {}
            )
            lat_bs = (
                c_bs[c_bs["year"] == latest_year].iloc[0]
                if not c_bs[c_bs["year"] == latest_year].empty
                else {}
            )
            lat_ratio = (
                c_ratio[c_ratio["year"] == latest_year].iloc[0]
                if not c_ratio[c_ratio["year"] == latest_year].empty
                else {}
            )
            lat_mcap = (
                c_mcap[c_mcap["year"] == latest_year].iloc[0]
                if not c_mcap[c_mcap["year"] == latest_year].empty
                else {}
            )

            # Compute ROCE
            roce_lat = 0.0
            if len(lat_pnl) > 0 and len(lat_bs) > 0:
                op = to_float(lat_pnl.get("operating_profit"))
                dep = to_float(lat_pnl.get("depreciation"))
                ebit = op - dep
                eq = to_float(lat_bs.get("equity_capital"))
                res = to_float(lat_bs.get("reserves"))
                borrow = to_float(lat_bs.get("borrowings"))
                cap_employed = eq + res + borrow
                if cap_employed > 0.0:
                    roce_lat = (ebit / cap_employed) * 100.0

            lat_data = {
                "sales": to_float(lat_pnl.get("sales")),
                "net_profit": to_float(lat_pnl.get("net_profit")),
                "roe": to_float(lat_ratio.get("return_on_equity_pct")),
                "roce": roce_lat,
                "de": to_float(lat_ratio.get("debt_to_equity")),
                "mcap": to_float(lat_mcap.get("market_cap_crore")),
            }

        if len(union_years) >= 2:
            prev_year = union_years[-2]
            # Fetch previous
            p_pnl = (
                c_pnl[c_pnl["year"] == prev_year].iloc[0]
                if not c_pnl[c_pnl["year"] == prev_year].empty
                else {}
            )
            p_bs = (
                c_bs[c_bs["year"] == prev_year].iloc[0]
                if not c_bs[c_bs["year"] == prev_year].empty
                else {}
            )
            p_ratio = (
                c_ratio[c_ratio["year"] == prev_year].iloc[0]
                if not c_ratio[c_ratio["year"] == prev_year].empty
                else {}
            )
            p_mcap = (
                c_mcap[c_mcap["year"] == prev_year].iloc[0]
                if not c_mcap[c_mcap["year"] == prev_year].empty
                else {}
            )

            # Compute ROCE
            roce_prev = 0.0
            if len(p_pnl) > 0 and len(p_bs) > 0:
                op = to_float(p_pnl.get("operating_profit"))
                dep = to_float(p_pnl.get("depreciation"))
                ebit = op - dep
                eq = to_float(p_bs.get("equity_capital"))
                res = to_float(p_bs.get("reserves"))
                borrow = to_float(p_bs.get("borrowings"))
                cap_employed = eq + res + borrow
                if cap_employed > 0.0:
                    roce_prev = (ebit / cap_employed) * 100.0

            prev_data = {
                "sales": to_float(p_pnl.get("sales")),
                "net_profit": to_float(p_pnl.get("net_profit")),
                "roe": to_float(p_ratio.get("return_on_equity_pct")),
                "roce": roce_prev,
                "de": to_float(p_ratio.get("debt_to_equity")),
                "mcap": to_float(p_mcap.get("market_cap_crore")),
            }

        # Header banner for page
        header_data = [
            [
                Paragraph(f"{comp_name} ({ticker})", style_header),
                Paragraph(f"Sector: {sector_name}", style_subheader),
            ]
        ]
        header_table = Table(header_data, colWidths=[4.8 * inch, 2.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#002B49")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 15))

        # Key metrics table comparison with trend arrows
        story.append(
            Paragraph(
                f"YoY Performance Dashboard (Comparing {prev_year} vs {latest_year})",
                style_sec_title,
            )
        )

        metric_keys = ["sales", "net_profit", "roe", "roce", "de", "mcap"]
        metric_names = [
            "Revenue (Sales) (Cr)",
            "Net Profit (PAT) (Cr)",
            "Return on Equity (ROE)",
            "Return on Capital Employed (ROCE)",
            "Debt-to-Equity (D/E) Ratio",
            "Market Capitalisation (Cr)",
        ]

        comp_header = [
            Paragraph("<b>Key Performance Indicator</b>", style_cell_lbl),
            Paragraph(f"<b>Previous ({prev_year})</b>", style_cell_lbl),
            Paragraph(f"<b>Latest ({latest_year})</b>", style_cell_lbl),
            Paragraph("<b>YoY Change</b>", style_cell_lbl),
            Paragraph("<b>Trend</b>", style_cell_lbl),
        ]

        rows = [comp_header]

        for k, name in zip(metric_keys, metric_names):
            lat_v = lat_data.get(k)
            prev_v = prev_data.get(k)

            arrow, color, text_change = get_trend_arrow(lat_v, prev_v)

            # Format display
            if lat_v is not None:
                if k in ["roe", "roce"]:
                    disp_lat = f"{lat_v:.1f}%"
                elif k == "de":
                    disp_lat = f"{lat_v:.2f}x"
                else:
                    disp_lat = f"₹{lat_v:,.1f}"
            else:
                disp_lat = "N/A"

            if prev_v is not None:
                if k in ["roe", "roce"]:
                    disp_prev = f"{prev_v:.1f}%"
                elif k == "de":
                    disp_prev = f"{prev_v:.2f}x"
                else:
                    disp_prev = f"₹{prev_v:,.1f}"
            else:
                disp_prev = "N/A"

            arrow_style = ParagraphStyle(
                "ArrowStyle",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=HexColor(color),
                alignment=TA_CENTER,
            )
            change_style = ParagraphStyle(
                "ChangeStyle",
                fontName="Helvetica-Bold",
                fontSize=8.5,
                textColor=HexColor(color),
            )

            rows.append(
                [
                    Paragraph(name, style_cell_lbl),
                    Paragraph(disp_prev, style_cell_val),
                    Paragraph(disp_lat, style_cell_val_bold),
                    Paragraph(text_change, change_style),
                    Paragraph(arrow, arrow_style),
                ]
            )

        metrics_table = Table(
            rows, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch]
        )
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F3F4F6")),
                    ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(metrics_table)
        story.append(Spacer(1, 20))

        # Add PageBreak for all but the last company
        if idx < len(tickers) - 1:
            story.append(PageBreak())

    # Build document
    doc.build(story)
    print(
        f"Successfully generated portfolio summary PDF: {dest_path} ({os.path.getsize(dest_path)} bytes)"
    )


if __name__ == "__main__":
    main()
