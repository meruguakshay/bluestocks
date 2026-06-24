-- SQLite Star Schema for Bluestock Mutual Fund Analytics

-- Drop tables if they exist to ensure clean setup
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS portfolio_holdings;
DROP TABLE IF EXISTS risk_metrics;
DROP TABLE IF EXISTS sip_data;
DROP TABLE IF EXISTS investor_data;
DROP TABLE IF EXISTS benchmark_data;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS dim_fund;
DROP TABLE IF EXISTS dim_date;

-- 1. dim_fund Table
CREATE TABLE dim_fund (
    scheme_code INTEGER PRIMARY KEY,
    isin TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    risk_grade TEXT NOT NULL
);

-- 2. dim_date Table
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY, -- format: YYYY-MM-DD
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL
);

-- 3. fact_nav Table
CREATE TABLE fact_nav (
    scheme_code INTEGER,
    date TEXT,
    nav REAL NOT NULL,
    PRIMARY KEY (scheme_code, date),
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 4. fact_transactions Table
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY,
    investor_id INTEGER NOT NULL,
    scheme_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    kyc_status TEXT NOT NULL,
    state TEXT NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 5. fact_performance Table
CREATE TABLE fact_performance (
    scheme_code INTEGER PRIMARY KEY,
    return_1yr REAL,
    return_3yr REAL,
    return_5yr REAL,
    expense_ratio REAL NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 6. fact_aum Table (AMC details with AUM)
CREATE TABLE fact_aum (
    amc_id INTEGER PRIMARY KEY,
    amc_name TEXT NOT NULL,
    aum_crores REAL NOT NULL
);

-- 7. portfolio_holdings Table
CREATE TABLE portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    isin TEXT NOT NULL,
    weightage REAL NOT NULL,
    sector TEXT NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 8. benchmark_data Table
CREATE TABLE benchmark_data (
    benchmark_id INTEGER PRIMARY KEY,
    benchmark_name TEXT NOT NULL,
    daily_return REAL NOT NULL
);

-- 9. risk_metrics Table
CREATE TABLE risk_metrics (
    scheme_code INTEGER PRIMARY KEY,
    beta REAL,
    sharpe_ratio REAL,
    alpha REAL,
    standard_deviation REAL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 10. sip_data Table
CREATE TABLE sip_data (
    scheme_code INTEGER PRIMARY KEY,
    sip_return_1yr REAL,
    sip_return_3yr REAL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 11. investor_data Table (original investor master info)
CREATE TABLE investor_data (
    investor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    scheme_code INTEGER NOT NULL,
    investment_amount REAL NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);
