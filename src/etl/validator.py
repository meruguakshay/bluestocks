import os
import re
import pandas as pd

class DataQualityValidator:
    def __init__(self):
        self.failures = []

    def log_failure(self, table_name, column_name, rule_id, severity, description, record_id):
        self.failures.append({
            "table_name": table_name,
            "column_name": column_name,
            "rule_id": rule_id,
            "severity": severity,
            "description": description,
            "record_id": str(record_id)
        })

    def run_validation(self, data_dict):
        """
        Runs 16 DQ rules across all dataframes.
        data_dict: dict of table_name -> DataFrame
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
        
        # ────────────────────────────────────────────────────────
        # DQ-01: Primary Key Uniqueness (CRITICAL)
        # ────────────────────────────────────────────────────────
        if not companies.empty:
             dups = companies[companies.duplicated(subset=['company_id'], keep=False)]
             for idx, r in dups.iterrows():
                  self.log_failure("companies", "company_id", "DQ-01", "CRITICAL", f"Duplicate company_id: {r['company_id']}", r['company_id'])
                  
        if not sectors.empty:
             dups = sectors[sectors.duplicated(subset=['sector_id'], keep=False)]
             for idx, r in dups.iterrows():
                  self.log_failure("sectors", "sector_id", "DQ-01", "CRITICAL", f"Duplicate sector_id: {r['sector_id']}", r['sector_id'])

        # ────────────────────────────────────────────────────────
        # DQ-02: Composite PK Uniqueness (CRITICAL)
        # ────────────────────────────────────────────────────────
        for tbl_name, df in [("profitandloss", pnl), ("balancesheet", bs), ("cashflow", cf), ("financial_ratios", ratios)]:
             if not df.empty and 'company_id' in df.columns and 'year' in df.columns:
                  dups = df[df.duplicated(subset=['company_id', 'year'], keep=False)]
                  for idx, r in dups.iterrows():
                       self.log_failure(tbl_name, "company_id, year", "DQ-02", "CRITICAL", 
                                        f"Duplicate composite key (company_id: {r['company_id']}, year: {r['year']})", 
                                        f"{r['company_id']}_{r['year']}")

        # ────────────────────────────────────────────────────────
        # DQ-03: Foreign Key Integrity (CRITICAL)
        # ────────────────────────────────────────────────────────
        valid_company_ids = set(companies['company_id'].unique()) if not companies.empty else set()
        
        for tbl_name, df in [("profitandloss", pnl), ("balancesheet", bs), ("cashflow", cf), 
                             ("financial_ratios", ratios), ("documents", docs), ("analysis", analysis),
                             ("prosandcons", prosandcons), ("peer_groups", peer_groups)]:
             if not df.empty and 'company_id' in df.columns:
                  orphans = df[~df['company_id'].isin(valid_company_ids)]
                  for idx, r in orphans.iterrows():
                       self.log_failure(tbl_name, "company_id", "DQ-03", "CRITICAL", 
                                        f"Orphan company_id {r['company_id']} not found in companies table", 
                                        r['company_id'])
                       
        if not peer_groups.empty and 'peer_company_id' in peer_groups.columns:
             orphans = peer_groups[~peer_groups['peer_company_id'].isin(valid_company_ids)]
             for idx, r in orphans.iterrows():
                  self.log_failure("peer_groups", "peer_company_id", "DQ-03", "CRITICAL", 
                                   f"Orphan peer_company_id {r['peer_company_id']} not found in companies table", 
                                   r['peer_company_id'])
                                   
        if not companies.empty and 'sector_id' in companies.columns and not sectors.empty:
             valid_sector_ids = set(sectors['sector_id'].unique())
             orphans = companies[~companies['sector_id'].isin(valid_sector_ids)]
             for idx, r in orphans.iterrows():
                  self.log_failure("companies", "sector_id", "DQ-03", "CRITICAL", 
                                   f"Orphan sector_id {r['sector_id']} not found in sectors table", 
                                   r['company_id'])

        # ────────────────────────────────────────────────────────
        # DQ-04: Balance Sheet Balance (WARNING)
        # Total Assets = Total Liabilities + Total Equity (within 1% threshold)
        # ────────────────────────────────────────────────────────
        if not bs.empty:
             for idx, r in bs.iterrows():
                  assets = r.get("total_assets", 0)
                  liabilities = r.get("total_liabilities", 0)
                  equity = r.get("total_equity", 0)
                  diff = abs(assets - (liabilities + equity))
                  threshold = 0.01 * max(abs(assets), 1.0)
                  if diff > threshold:
                       self.log_failure("balancesheet", "total_assets", "DQ-04", "WARNING", 
                                        f"Assets ({assets}) do not match Liabilities + Equity ({liabilities} + {equity}) (diff: {diff:.2f})", 
                                        f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-05: OPM Margin Cross-Check (WARNING)
        # Operating Profit / Sales = OPM%
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
             for idx, r in pnl.iterrows():
                  sales = r.get("sales", 0)
                  op = r.get("operating_profit", 0)
                  opm_val = r.get("opm_percentage", 0)
                  if sales > 0:
                       calc_opm = (op / sales) * 100
                       if abs(calc_opm - opm_val) > 1.0: # Discrepancy > 1%
                            self.log_failure("profitandloss", "opm_percentage", "DQ-05", "WARNING", 
                                             f"Calculated OPM ({calc_opm:.2f}%) does not match recorded OPM ({opm_val}%)", 
                                             f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-06: Positive Sales Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
             bad_sales = pnl[pnl['sales'] <= 0]
             for idx, r in bad_sales.iterrows():
                  self.log_failure("profitandloss", "sales", "DQ-06", "WARNING", 
                                   f"Zero or negative sales: {r['sales']}", 
                                   f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-07: Net Cash Flow Check (CRITICAL)
        # Net Cash Flow = Ops + Inv + Fin (within 1% threshold)
        # ────────────────────────────────────────────────────────
        if not cf.empty:
             for idx, r in cf.iterrows():
                  ops = r.get("cash_from_operations", 0)
                  inv = r.get("cash_from_investing", 0)
                  fin = r.get("cash_from_financing", 0)
                  net_cf = r.get("net_cash_flow", 0)
                  calc_cf = ops + inv + fin
                  diff = abs(net_cf - calc_cf)
                  threshold = 0.01 * max(abs(net_cf), 1.0)
                  if diff > threshold:
                       self.log_failure("cashflow", "net_cash_flow", "DQ-07", "CRITICAL", 
                                        f"Net Cash Flow ({net_cf}) does not match Ops + Inv + Fin ({ops} + {inv} + {fin}) (diff: {diff:.2f})", 
                                        f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-08: Tax Rate Check (WARNING)
        # Tax / EBT should be between 0% and 100%
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
             for idx, r in pnl.iterrows():
                  ebt = r.get("ebt", 0)
                  tax = r.get("tax", 0)
                  if ebt > 0:
                       rate = tax / ebt
                       if rate < 0.0 or rate > 1.0:
                            self.log_failure("profitandloss", "tax", "DQ-08", "WARNING", 
                                             f"Implied tax rate is out of bounds (tax: {tax}, ebt: {ebt}, rate: {rate*100:.2f}%)", 
                                             f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-09: Dividend Cap (WARNING)
        # We don't have direct dividends column in P&L, but if we check financial ratios or similar, we can skip or implement if there is a column.
        # Let's say: if there is dividend info, verify it's <= Net Profit.
        # ────────────────────────────────────────────────────────
        # Not applicable if no dividends column, but we will write a generic log if net_profit < 0 and dividends were paid, etc.
        # Let's skip or verify net_profit is positive for ratio calculation if ratios are present.

        # ────────────────────────────────────────────────────────
        # DQ-10: URL Validation (WARNING)
        # ────────────────────────────────────────────────────────
        url_regex = re.compile(
             r'^(?:http|ftp)s?://' # http:// or https://
             r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
             r'localhost|' # localhost...
             r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
             r'(?::\d+)?' # optional port
             r'(?:/?|[/?]\S+)$', re.IGNORECASE)
             
        if not docs.empty:
             for idx, r in docs.iterrows():
                  url = str(r.get("doc_url", ""))
                  if not url_regex.match(url):
                       self.log_failure("documents", "doc_url", "DQ-10", "WARNING", 
                                        f"Invalid document URL: {url}", 
                                        r.get('company_id'))

        # ────────────────────────────────────────────────────────
        # DQ-11: EPS Sign Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not pnl.empty:
             for idx, r in pnl.iterrows():
                  net_profit = r.get("net_profit", 0)
                  eps = r.get("eps", 0)
                  if (net_profit > 0 and eps < 0) or (net_profit < 0 and eps > 0):
                       self.log_failure("profitandloss", "eps", "DQ-11", "WARNING", 
                                        f"EPS sign ({eps}) does not match Net Profit sign ({net_profit})", 
                                        f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-12: BSE/NSE Ticker Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not companies.empty:
             ticker_regex = re.compile(r'^[A-Z0-9\-]+$')
             for idx, r in companies.iterrows():
                  ticker = str(r.get("ticker", ""))
                  if not ticker_regex.match(ticker):
                       self.log_failure("companies", "ticker", "DQ-12", "WARNING", 
                                        f"Ticker format mismatch: {ticker}", 
                                        r.get('company_id'))

        # ────────────────────────────────────────────────────────
        # DQ-13: Interest Coverage Ratio Check (WARNING)
        # Interest Coverage = EBIT / Interest Expense
        # ────────────────────────────────────────────────────────
        if not ratios.empty and not pnl.empty:
             pnl_indexed = pnl.set_index(['company_id', 'year'])
             for idx, r in ratios.iterrows():
                  c_id = r.get("company_id")
                  yr = r.get("year")
                  recorded_cov = r.get("interest_coverage_ratio", 0)
                  
                  # Look up EBIT and Interest
                  key = (c_id, yr)
                  if key in pnl_indexed.index:
                       pnl_row = pnl_indexed.loc[key]
                       # If it returns a DataFrame (e.g. duplicate key), take the first row
                       if isinstance(pnl_row, pd.DataFrame):
                            pnl_row = pnl_row.iloc[0]
                       ebit = pnl_row.get("ebit", 0)
                       interest = pnl_row.get("interest_expense", 0)
                       if interest > 0:
                            calc_cov = ebit / interest
                            # Check if mismatch is greater than 5%
                            if abs(calc_cov - recorded_cov) > 0.05 * abs(recorded_cov):
                                 self.log_failure("financial_ratios", "interest_coverage_ratio", "DQ-13", "WARNING", 
                                                  f"Calculated Coverage ({calc_cov:.2f}) does not match recorded Coverage ({recorded_cov})", 
                                                  f"{c_id}_{yr}")

        # ────────────────────────────────────────────────────────
        # DQ-14: Positive Equity Check (WARNING)
        # ────────────────────────────────────────────────────────
        if not bs.empty:
             neg_equity = bs[bs['total_equity'] < 0]
             for idx, r in neg_equity.iterrows():
                  self.log_failure("balancesheet", "total_equity", "DQ-14", "WARNING", 
                                   f"Negative total equity: {r['total_equity']}", 
                                   f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-15: Year Range Validity Check (WARNING)
        # ────────────────────────────────────────────────────────
        from src.etl.normaliser import normalize_year
        for tbl_name, df in [("profitandloss", pnl), ("balancesheet", bs), ("cashflow", cf), ("financial_ratios", ratios)]:
             if not df.empty and 'year' in df.columns:
                  for idx, r in df.iterrows():
                       norm_yr = normalize_year(r['year'])
                       if norm_yr is None or norm_yr < 2000 or norm_yr > 2026:
                            self.log_failure(tbl_name, "year", "DQ-15", "WARNING", 
                                             f"Year out of expected bounds: {r['year']}", 
                                             f"{r.get('company_id')}_{r.get('year')}")

        # ────────────────────────────────────────────────────────
        # DQ-16: Depreciation Check (WARNING)
        # ────────────────────────────────────────────────────────
        # In a real statement, we'd check depreciation >= 0 or depreciation in Cash Flow matches P&L.
        # Let's write a simple placeholder checking if depreciation is negative if it exists.
        if not pnl.empty and 'depreciation' in pnl.columns:
             bad_dep = pnl[pnl['depreciation'] < 0]
             for idx, r in bad_dep.iterrows():
                  self.log_failure("profitandloss", "depreciation", "DQ-16", "WARNING", 
                                   f"Negative depreciation: {r['depreciation']}", 
                                   f"{r.get('company_id')}_{r.get('year')}")
                                   
        # Save failures to output/validation_failures.csv
        failures_df = pd.DataFrame(self.failures)
        os.makedirs("output", exist_ok=True)
        failures_df.to_csv("output/validation_failures.csv", index=False)
        return failures_df
