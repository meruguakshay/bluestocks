-- SQLite Database Schema for Nifty 100 Financial Intelligence Database
PRAGMA foreign_keys = ON;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS sectors;

-- 1. sectors table
CREATE TABLE sectors (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    broad_sector TEXT UNIQUE NOT NULL
);

-- 2. companies table
CREATE TABLE companies (
    company_id TEXT PRIMARY KEY, -- Real Ticker (e.g. ABB, RELIANCE)
    company_name TEXT NOT NULL,
    company_logo TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL,
    sector_id INTEGER,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY(sector_id) REFERENCES sectors(sector_id) ON DELETE CASCADE
);

-- 3. profitandloss table
CREATE TABLE profitandloss (
    company_id TEXT,
    year TEXT,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 4. balancesheet table
CREATE TABLE balancesheet (
    company_id TEXT,
    year TEXT,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 5. cashflow table
CREATE TABLE cashflow (
    company_id TEXT,
    year TEXT,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 6. financial_ratios table
CREATE TABLE financial_ratios (
    company_id TEXT,
    year TEXT,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 7. stock_prices table
CREATE TABLE stock_prices (
    company_id TEXT,
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 8. analysis table
CREATE TABLE analysis (
    company_id TEXT PRIMARY KEY,
    analysis_date TEXT,
    notes TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 9. documents table
CREATE TABLE documents (
    company_id TEXT,
    year TEXT,
    annual_report TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 10. prosandcons table
CREATE TABLE prosandcons (
    company_id TEXT PRIMARY KEY,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 11. peer_groups table
CREATE TABLE peer_groups (
    company_id TEXT PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    is_benchmark INTEGER NOT NULL, -- 0 or 1
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 12. market_cap table
CREATE TABLE market_cap (
    company_id TEXT,
    year TEXT,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
