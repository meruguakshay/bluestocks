-- SQLite Database Schema for Nifty 100 Financial Intelligence Database

-- Ensure Foreign Key Constraints are enabled at session level
PRAGMA foreign_keys = ON;

-- 1. sectors table
CREATE TABLE IF NOT EXISTS sectors (
    sector_id INTEGER PRIMARY KEY,
    sector_name TEXT NOT NULL
);

-- 2. companies table
CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    bse_code TEXT,
    nse_code TEXT,
    website_url TEXT,
    sector_id INTEGER,
    FOREIGN KEY(sector_id) REFERENCES sectors(sector_id) ON DELETE CASCADE
);

-- 3. profitandloss table
CREATE TABLE IF NOT EXISTS profitandloss (
    company_id INTEGER,
    year INTEGER,
    sales REAL,
    operating_profit REAL,
    opm_percentage REAL,
    interest_expense REAL,
    ebit REAL,
    ebt REAL,
    tax REAL,
    net_profit REAL,
    eps REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 4. balancesheet table
CREATE TABLE IF NOT EXISTS balancesheet (
    company_id INTEGER,
    year INTEGER,
    total_assets REAL,
    total_liabilities REAL,
    total_equity REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 5. cashflow table
CREATE TABLE IF NOT EXISTS cashflow (
    company_id INTEGER,
    year INTEGER,
    cash_from_operations REAL,
    cash_from_investing REAL,
    cash_from_financing REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 6. financial_ratios table
CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id INTEGER,
    year INTEGER,
    interest_coverage_ratio REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 7. stock_prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    ticker TEXT,
    date TEXT,
    close_price REAL,
    PRIMARY KEY (ticker, date),
    FOREIGN KEY(ticker) REFERENCES companies(ticker) ON DELETE CASCADE
);

-- 8. analysis table
CREATE TABLE IF NOT EXISTS analysis (
    company_id INTEGER PRIMARY KEY,
    analysis_date TEXT,
    notes TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 9. documents table
CREATE TABLE IF NOT EXISTS documents (
    company_id INTEGER,
    doc_name TEXT,
    doc_url TEXT,
    PRIMARY KEY (company_id, doc_name),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 10. prosandcons table
CREATE TABLE IF NOT EXISTS prosandcons (
    company_id INTEGER PRIMARY KEY,
    pro TEXT,
    con TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- 11. peer_groups table
CREATE TABLE IF NOT EXISTS peer_groups (
    company_id INTEGER,
    peer_company_id INTEGER,
    PRIMARY KEY (company_id, peer_company_id),
    FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY(peer_company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
