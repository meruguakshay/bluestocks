import os
import re
import urllib.request
import pandas as pd
from typing import Optional, Dict
from src.etl.normaliser import normalize_year, normalize_ticker

class DataQualityValidator:
    def __init__(self):
        self.failures = []

    def log_failure(self, table_name: str, column_name: str, rule_id: str, severity: str, description: str, record_id: str):
        self.failures.append({
            "table_name": table_name,
            "column_name": column_name,
            "rule_id": rule_id,
            "severity": severity,
            "description": description,
            "record_id": str(record_id)
        })

    def run_validation(self, data_dict: Dict[str, pd.DataFrame], output_path: Optional[str] = "output/validation_failures.csv") -> pd.DataFrame:
        """
        Runs 16 conformed DQ rules across all Nifty 100 dataframes.
        If output_path is provided, writes validation_failures.csv.
        """
        self.failures = []
        
        # Extract dataframes
        companies = data_dict.get("companies", pd.DataFrame())
        pnl = data_dict.get("profitandloss", pd.DataFrame())
        bs = data_dict.get("balancesheet", pd.DataFrame())
        cf = data_dict.get("cashflow", pd.DataFrame())
        prices = data_dict.get("stock_prices", pd.DataFrame())
        sectors = data_dict.get("sectors", pd.DataFrame())
        ratios = data_dict.get("financial_ratios", pd.DataFrame())
        docs = data_dict.get("documents", pd.DataFrame())
        analysis = data_dict.get("analysis", pd.DataFrame())
        prosandcons = data_dict.get("prosandcons", pd.DataFrame())
        peer_groups = data_dict.get("peer_groups", pd.DataFrame())
        market_cap = data_dict.get("market_cap", pd.DataFrame())

        # Normalize companies company_id on columns renaming
        comp_id_col = 'company_id' if 'company_id' in companies.columns else ('id' if 'id' in companies.columns else None)
        sect_comp_col = 'company_id' if 'company_id' in sectors.columns else None

        # Build sector dictionary to map tickers to sectors (broad sector)
        sect_map = {}
        if not sectors.empty:
            s_col = 'company_id' if 'company_id' in sectors.columns else 'id'
            for idx, r in sectors.iterrows():
                t = normalize_ticker(r.get(s_col))
                if t:
                    sect_map[t] = str(r.get("broad_sector", "")).strip()

        # ────────────────────────────────────────────────────────
        # DQ-01: Company PK Uniqueness (CRITICAL)
        # ────────────────────────────────────────────────────────
        for tbl_name, df, col in [
            ("companies", companies, comp_id_col),
            ("sectors", sectors, sect_comp_col),
            ("prosandcons", prosandcons, "company_id"),
            ("analysis", analysis, "company_id"),
            ("peer_groups", peer_groups, "company_id")
        ]:
            if not df.empty and col and col in df.columns:
                dups = df[df.duplicated(subset=[col], keep=False)]
                for idx, r in dups.iterrows():
                    val = r[col]
                    self.log_failure(tbl_name, col, "DQ-01", "CRITICAL", f"Duplicate primary key {col}: {val}", val)

        # ────────────────────────────────────────────────────────
        # DQ-02: Annual PK Uniqueness (CRITICAL)
        # ────────────────────────────────────────────────────────
        for tbl_name, df in [
            ("profitandloss", pnl),
            ("balancesheet", bs),
            ("cashflow", cf),
            ("financial_ratios", ratios),
            ("documents", docs),
            ("market_cap", market_cap)
        ]:
            if not df.empty and 'company_id' in df.columns:
                yr_col = 'year' if 'year' in df.columns else ('Year' if 'Year' in df.columns else None)
                if yr_col:
                    dups = df[df.duplicated(subset=['company_id', yr_col], keep=False)]
                    for idx, r in dups.iterrows():
                        self.log_failure(tbl_name, f"company_id, {yr_col}", "DQ-02", "CRITICAL", 
                                         f"Duplicate composite key (company_id: {r['company_id']}, year: {r[yr_col]})", 
                                         f"{r['company_id']}_{r[yr_col]}")

        # ────────────────────────────────────────────────────────
        # DQ-03: Foreign Key Integrity (CRITICAL)
        # ────────────────────────────────────────────────────────
        valid_company_ids = set()
        if not companies.empty and comp_id_col:
            valid_company_ids = set(companies[comp_id_col].dropna().apply(normalize_ticker).unique())

        for tbl_name, df in [
            ("profitandloss", pnl),
            ("balancesheet", bs),
            ("cashflow", cf),
            ("financial_ratios", ratios),
            ("documents", docs),
            ("analysis", analysis),
            ("prosandcons", prosandcons),
            ("peer_groups", peer_groups),
            ("market_cap", market_cap),
            ("sectors", sectors),
            ("stock_prices", prices)
        ]:
            if not df.empty and 'company_id' in df.columns and len(valid_company_ids) > 0:
                orphans = df[~df['company_id'].apply(normalize_ticker).isin(valid_company_ids)]
                for idx, r in orphans.iterrows():
                    self.log_failure(tbl_name, "company_id", "DQ-03", "CRITICAL", 
                                     f"Orphan company_id {r['company_id']} not found in companies table", 
                                     r['company_id'])

        # ────────────────────────────────────────────────────────
        # DQ-04: Balance Sheet Balance (WARNING)
        # ────────────────────────────────────────────────────────
        if not bs.empty:
            for idx, r in bs.iterrows():
                assets = r.get("total_assets", 0)
                liabilities = r.get("total_liabilities", 0)
                if assets > 0:
                    diff = abs(assets - liabilities)
                    if diff / assets >= 0.01:
                        self.log_failure("balancesheet", "total_assets", "DQ-04", "WARNING", 
                                         f"Assets ({assets}) do not match Liabilities ({liabilities}) within 1%", 
                                         f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-05: OPM Cross-Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
            for idx, r in pnl.iterrows():
                sales = r.get("sales", 0)
                op = r.get("operating_profit", 0)
                opm_val = r.get("opm_percentage", 0)
                if sales > 0:
                    calc_opm = (op / sales) * 100
                    if abs(calc_opm - opm_val) >= 1.0:
                        self.log_failure("profitandloss", "opm_percentage", "DQ-05", "WARNING", 
                                         f"Calculated OPM ({calc_opm:.2f}%) does not match recorded OPM ({opm_val}%) by >= 1%", 
                                         f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-06: Positive Sales (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
            for idx, r in pnl.iterrows():
                c_id = normalize_ticker(r.get("company_id"))
                sales = r.get("sales", 0)
                if c_id and sect_map.get(c_id) == 'Financials':
                    continue
                if sales <= 0:
                    self.log_failure("profitandloss", "sales", "DQ-06", "WARNING", 
                                     f"Non-bank sales must be positive (recorded: {sales})", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-07: Year Format (CRITICAL)
        # ────────────────────────────────────────────────────────
        for tbl_name, df in [
            ("profitandloss", pnl),
            ("balancesheet", bs),
            ("cashflow", cf),
            ("financial_ratios", ratios),
            ("documents", docs),
            ("market_cap", market_cap)
        ]:
            if not df.empty:
                yr_col = 'year' if 'year' in df.columns else ('Year' if 'Year' in df.columns else None)
                if yr_col:
                    for idx, r in df.iterrows():
                        norm_yr = normalize_year(r[yr_col])
                        if norm_yr is None or not re.match(r'^\d{4}-\d{2}$', norm_yr):
                            self.log_failure(tbl_name, yr_col, "DQ-07", "CRITICAL", 
                                             f"Invalid year format: {r[yr_col]} (normalised: {norm_yr})", 
                                             f"{r.get('company_id')}_{r.get(yr_col)}")

        # ────────────────────────────────────────────────────────
        # DQ-08: Ticker Format (CRITICAL)
        # ────────────────────────────────────────────────────────
        ticker_regex = re.compile(r'^[A-Z0-9\-&]+$')
        for tbl_name, df in [
            ("companies", companies),
            ("sectors", sectors),
            ("profitandloss", pnl),
            ("balancesheet", bs),
            ("cashflow", cf),
            ("financial_ratios", ratios),
            ("documents", docs),
            ("analysis", analysis),
            ("prosandcons", prosandcons),
            ("peer_groups", peer_groups),
            ("market_cap", market_cap),
            ("stock_prices", prices)
        ]:
            if not df.empty:
                col = 'company_id' if 'company_id' in df.columns else ('id' if tbl_name == 'companies' else None)
                if col:
                    for idx, r in df.iterrows():
                        ticker = str(r.get(col, "")).strip()
                        norm_ticker = normalize_ticker(ticker)
                        if norm_ticker is None or len(norm_ticker) < 2 or len(norm_ticker) > 12 or not ticker_regex.match(norm_ticker):
                            self.log_failure(tbl_name, col, "DQ-08", "CRITICAL", 
                                             f"Invalid ticker length or characters: {ticker}", 
                                             ticker)

        # ────────────────────────────────────────────────────────
        # DQ-09: Net Cash Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not cf.empty:
            for idx, r in cf.iterrows():
                cfo = r.get("operating_activity", 0)
                cfi = r.get("investing_activity", 0)
                cff = r.get("financing_activity", 0)
                net_cf = r.get("net_cash_flow", 0)
                calc_cf = cfo + cfi + cff
                if abs(net_cf - calc_cf) > 10.0:
                    self.log_failure("cashflow", "net_cash_flow", "DQ-09", "WARNING", 
                                     f"Net Cash Flow mismatch: CFO={cfo}, CFI={cfi}, CFF={cff}, sum={calc_cf}, recorded={net_cf}", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-10: Non-Negative Fixed Assets (WARNING)
        # ────────────────────────────────────────────────────────
        if not bs.empty:
            for idx, r in bs.iterrows():
                fa = r.get("fixed_assets", 0)
                if fa < 0:
                    self.log_failure("balancesheet", "fixed_assets", "DQ-10", "WARNING", 
                                     f"Negative fixed assets: {fa}", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-11: Tax Rate Range (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
            for idx, r in pnl.iterrows():
                tax = r.get("tax_percentage", 0)
                if tax < 0 or tax > 60:
                    self.log_failure("profitandloss", "tax_percentage", "DQ-11", "WARNING", 
                                     f"Tax rate out of expected 0-60% range: {tax}%", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-12: Dividend Payout Cap (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
            for idx, r in pnl.iterrows():
                div = r.get("dividend_payout", 0)
                if div > 200:
                    self.log_failure("profitandloss", "dividend_payout", "DQ-12", "WARNING", 
                                     f"Dividend payout ratio exceeds 200%: {div}%", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-13: URL Validity (documents) (WARNING)
        # ────────────────────────────────────────────────────────
        url_regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        if not docs.empty:
            col = "annual_report" if "annual_report" in docs.columns else ("Annual_Report" if "Annual_Report" in docs.columns else None)
            if col:
                for idx, r in docs.iterrows():
                    url = str(r.get(col, "")).strip()
                    if not url or url.lower() in ("nan", "null", ""):
                        self.log_failure("documents", col, "DQ-13", "WARNING", f"Empty document URL: {url}", r.get('company_id'))
                    elif not url_regex.match(url):
                        self.log_failure("documents", col, "DQ-13", "WARNING", f"Invalid URL format: {url}", r.get('company_id'))

        # ────────────────────────────────────────────────────────
        # DQ-14: EPS Sign Consistency (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
            for idx, r in pnl.iterrows():
                net_profit = r.get("net_profit", 0)
                eps = r.get("eps", 0)
                if (net_profit > 0 and eps < 0) or (net_profit < 0 and eps > 0):
                    self.log_failure("profitandloss", "eps", "DQ-14", "WARNING", 
                                     f"EPS sign ({eps}) does not match Net Profit sign ({net_profit})", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-15: BSE/ASE Balance (ext.) (INFO)
        # ────────────────────────────────────────────────────────
        if not bs.empty:
            for idx, r in bs.iterrows():
                assets = r.get("total_assets", 0)
                liabilities = r.get("total_liabilities", 0)
                if assets != liabilities:
                    self.log_failure("balancesheet", "total_assets", "DQ-15", "INFO", 
                                     f"Strict balance difference: assets ({assets}) != liabilities ({liabilities})", 
                                     f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-16: Coverage Check (WARNING)
        # ────────────────────────────────────────────────────────
        history_counts = {}
        for tbl_name, df in [("profitandloss", pnl), ("balancesheet", bs), ("cashflow", cf)]:
            if not df.empty and 'company_id' in df.columns:
                yr_col = 'year' if 'year' in df.columns else ('Year' if 'Year' in df.columns else None)
                if yr_col:
                    for idx, r in df.iterrows():
                        c_id = normalize_ticker(r['company_id'])
                        if c_id:
                            if c_id not in history_counts:
                                history_counts[c_id] = set()
                            norm_yr = normalize_year(r[yr_col])
                            if norm_yr:
                                history_counts[c_id].add(norm_yr)
                                
        for c_id in valid_company_ids:
            years = history_counts.get(c_id, set())
            if len(years) < 5:
                self.log_failure("companies", "company_id", "DQ-16", "WARNING", 
                                 f"Company {c_id} has less than 5 years of historical records ({len(years)} years found)", 
                                 c_id)

        # Output to CSV if output_path is provided
        failures_df = pd.DataFrame(self.failures)
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            failures_df.to_csv(output_path, index=False)
            
        return failures_df
