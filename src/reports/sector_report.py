import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DB_PATH = "db/nifty100.db"
os.makedirs("reports/sector", exist_ok=True)


def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def generate_sector_report(sector_id, sector_name, dest_path):
    """Generates a PDF report for a sector showing median metrics and company comparisons"""
    conn = sqlite3.connect(DB_PATH)

    # Query companies in sector
    df_comp = pd.read_sql(
        f"SELECT company_id, company_name FROM companies WHERE sector_id = {sector_id}",
        conn,
    )
    if df_comp.empty:
        conn.close()
        return False

    tickers = df_comp["company_id"].tolist()

    # Query latest conformed financials for all companies in sector
    data = []
    for ticker in tickers:
        # Find latest conformed year (intersection of pnl, bs, cashflow)
        query_years = f"""
        select year from profitandloss where company_id = '{ticker}'
        intersect
        select year from balancesheet where company_id = '{ticker}'
        intersect
        select year from cashflow where company_id = '{ticker}'
        """
        df_yrs = pd.read_sql(query_years, conn)
        if df_yrs.empty:
            continue
        latest_yr = sorted(df_yrs["year"].tolist())[-1]

        # Load latest values
        pnl_row = pd.read_sql(
            f"SELECT sales, net_profit, operating_profit, depreciation FROM profitandloss WHERE company_id = '{ticker}' AND year = '{latest_yr}'",
            conn,
        )
        bs_row = pd.read_sql(
            f"SELECT equity_capital, reserves, borrowings FROM balancesheet WHERE company_id = '{ticker}' AND year = '{latest_yr}'",
            conn,
        )
        ratio_row = pd.read_sql(
            f"SELECT return_on_equity_pct, debt_to_equity FROM financial_ratios WHERE company_id = '{ticker}' AND year = '{latest_yr}'",
            conn,
        )
        mcap_row = pd.read_sql(
            f"SELECT market_cap_crore FROM market_cap WHERE company_id = '{ticker}' AND year = '{latest_yr}'",
            conn,
        )

        sales = to_float(pnl_row.iloc[0]["sales"]) if not pnl_row.empty else 0.0
        net_profit = (
            to_float(pnl_row.iloc[0]["net_profit"]) if not pnl_row.empty else 0.0
        )
        roe = (
            to_float(ratio_row.iloc[0]["return_on_equity_pct"])
            if not ratio_row.empty
            else 0.0
        )
        de = (
            to_float(ratio_row.iloc[0]["debt_to_equity"])
            if not ratio_row.empty
            else 0.0
        )
        mcap = (
            to_float(mcap_row.iloc[0]["market_cap_crore"])
            if not mcap_row.empty
            else 0.0
        )

        # Compute ROCE
        roce = 0.0
        if not pnl_row.empty and not bs_row.empty:
            op = to_float(pnl_row.iloc[0]["operating_profit"])
            dep = to_float(pnl_row.iloc[0]["depreciation"])
            ebit = op - dep

            eq = to_float(bs_row.iloc[0]["equity_capital"])
            res = to_float(bs_row.iloc[0]["reserves"])
            borrow = to_float(bs_row.iloc[0]["borrowings"])
            cap_employed = eq + res + borrow

            if cap_employed > 0.0:
                roce = (ebit / cap_employed) * 100.0

        c_name = df_comp[df_comp["company_id"] == ticker].iloc[0]["company_name"]
        data.append(
            {
                "ticker": ticker,
                "name": c_name,
                "sales": sales,
                "net_profit": net_profit,
                "roe": roe,
                "roce": roce,
                "de": de,
                "mcap": mcap,
            }
        )

    conn.close()

    if not data:
        return False

    df_sec_data = pd.DataFrame(data)

    # Calculate Sector Medians
    median_sales = df_sec_data["sales"].median()
    median_pat = df_sec_data["net_profit"].median()
    median_roe = df_sec_data["roe"].median()
    median_roce = df_sec_data["roce"].median()
    median_de = df_sec_data["de"].median()
    median_mcap = df_sec_data["mcap"].median()

    # Build Document
    doc = SimpleDocTemplate(
        dest_path,
        pagesize=A4,
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    styles = getSampleStyleSheet()

    # Styles
    style_header = ParagraphStyle(
        "SecHeader",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.white,
    )
    style_subheader = ParagraphStyle(
        "SecSubheader",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )
    style_sec_title = ParagraphStyle(
        "SecSectionTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=HexColor("#002B49"),
        spaceAfter=8,
    )

    style_cell = ParagraphStyle(
        "Cell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=HexColor("#374151"),
    )
    style_cell_bold = ParagraphStyle(
        "CellBold",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=HexColor("#111827"),
    )
    style_cell_center = ParagraphStyle(
        "CellCenter",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=HexColor("#374151"),
        alignment=TA_CENTER,
    )
    style_cell_right = ParagraphStyle(
        "CellRight",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=HexColor("#374151"),
        alignment=TA_RIGHT,
    )

    story = []

    # Header Banner
    header_data = [
        [
            Paragraph(f"Sector Analysis: {sector_name}", style_header),
            Paragraph(f"Companies: {len(df_sec_data)}", style_subheader),
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

    # Medians KPI Summary Table
    story.append(Paragraph("Sector Medians Summary", style_sec_title))
    medians_data = [
        [
            Paragraph("<b>Median Revenue (Sales)</b>", style_cell_center),
            Paragraph("<b>Median Net Profit (PAT)</b>", style_cell_center),
            Paragraph("<b>Median Return on Equity (ROE)</b>", style_cell_center),
        ],
        [
            Paragraph(f"₹{median_sales:.1f} Cr", style_cell_bold),
            Paragraph(f"₹{median_pat:.1f} Cr", style_cell_bold),
            Paragraph(f"{median_roe:.1f}%", style_cell_bold),
        ],
        [
            Paragraph("<b>Median ROCE</b>", style_cell_center),
            Paragraph("<b>Median Debt-to-Equity (D/E)</b>", style_cell_center),
            Paragraph("<b>Median Market Cap</b>", style_cell_center),
        ],
        [
            Paragraph(f"{median_roce:.1f}%", style_cell_bold),
            Paragraph(f"{median_de:.2f}x", style_cell_bold),
            Paragraph(f"₹{median_mcap:.1f} Cr", style_cell_bold),
        ],
    ]
    medians_table = Table(
        medians_data, colWidths=[2.43 * inch, 2.43 * inch, 2.43 * inch]
    )
    medians_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F3F4F6")),
                ("BACKGROUND", (0, 2), (-1, 2), HexColor("#F3F4F6")),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(medians_table)
    story.append(Spacer(1, 15))

    # Companies Comparison Table
    story.append(Paragraph("Sector Company Comparison", style_sec_title))

    comp_header = [
        Paragraph("<b>Ticker</b>", style_cell_bold),
        Paragraph("<b>Company Name</b>", style_cell_bold),
        Paragraph("<b>Revenue (Cr)</b>", style_cell_right),
        Paragraph("<b>PAT (Cr)</b>", style_cell_right),
        Paragraph("<b>ROE (%)</b>", style_cell_right),
        Paragraph("<b>ROCE (%)</b>", style_cell_right),
        Paragraph("<b>D/E (x)</b>", style_cell_right),
        Paragraph("<b>Mkt Cap (Cr)</b>", style_cell_right),
    ]

    comparison_rows = [comp_header]
    for _, row in df_sec_data.iterrows():
        comparison_rows.append(
            [
                Paragraph(row["ticker"], style_cell_bold),
                Paragraph(row["name"], style_cell),
                Paragraph(f"{row['sales']:,.1f}", style_cell_right),
                Paragraph(f"{row['net_profit']:,.1f}", style_cell_right),
                Paragraph(f"{row['roe']:.1f}%", style_cell_right),
                Paragraph(f"{row['roce']:.1f}%", style_cell_right),
                Paragraph(f"{row['de']:.2f}", style_cell_right),
                Paragraph(f"{row['mcap']:,.1f}", style_cell_right),
            ]
        )

    comp_table = Table(
        comparison_rows,
        colWidths=[
            0.8 * inch,
            2.0 * inch,
            0.85 * inch,
            0.75 * inch,
            0.7 * inch,
            0.7 * inch,
            0.6 * inch,
            0.9 * inch,
        ],
    )
    comp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#002B49")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    # Text color adjust for header row in table
    for i in range(len(comp_header)):
        comp_table.setStyle(TableStyle([("TEXTCOLOR", (i, 0), (i, 0), colors.white)]))

    story.append(comp_table)

    # Build
    doc.build(story)
    return True


def main():
    print("=" * 60)
    print("TESTING SECTOR REPORT GENERATION")
    print("=" * 60)

    # Let's run a test on sector 8 (Information Technology)
    dest = "reports/sector/Information_Technology_report.pdf"
    success = generate_sector_report(8, "Information Technology", dest)
    if success:
        print(
            f"[OK] Generated test sector report: {dest} ({os.path.getsize(dest)} bytes)"
        )
    else:
        print("[ERROR] Failed to generate Information Technology sector report.")


if __name__ == "__main__":
    main()
