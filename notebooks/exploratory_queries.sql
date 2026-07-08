-- Nifty 100 Exploratory Analysis SQL Queries

-- 1. Total count of companies in each sector
SELECT s.sector_name, COUNT(c.company_id) AS company_count
FROM sectors s
JOIN companies c ON s.sector_id = c.sector_id
GROUP BY s.sector_name
ORDER BY company_count DESC;

-- 2. Top 10 companies by sales in FY2025
SELECT c.company_name, p.sales, p.net_profit, p.opm_percentage
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
WHERE p.year = 2025
ORDER BY p.sales DESC
LIMIT 10;

-- 3. Calculate average OPM% by sector for FY2025
SELECT s.sector_name, ROUND(AVG(p.opm_percentage), 2) AS avg_opm_pct
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
JOIN sectors s ON c.sector_id = s.sector_id
WHERE p.year = 2025
GROUP BY s.sector_name
ORDER BY avg_opm_pct DESC;

-- 4. Find companies with average stock close price in 2026
SELECT c.company_name, c.ticker, ROUND(AVG(sp.close_price), 2) AS avg_close_price
FROM stock_prices sp
JOIN companies c ON sp.ticker = c.ticker
GROUP BY c.company_name, c.ticker
ORDER BY avg_close_price DESC
LIMIT 10;

-- 5. Track cash flow statements summary for Reliance (ID 1)
SELECT year, cash_from_operations, cash_from_investing, cash_from_financing, net_cash_flow
FROM cashflow
WHERE company_id = 1
ORDER BY year;

-- 6. Check companies with negative total equity in any year
SELECT c.company_name, b.year, b.total_assets, b.total_liabilities, b.total_equity
FROM balancesheet b
JOIN companies c ON b.company_id = c.company_id
WHERE b.total_equity < 0
ORDER BY b.total_equity ASC;

-- 7. Document registry and status
SELECT c.company_name, d.doc_name, d.doc_url
FROM documents d
JOIN companies c ON d.company_id = c.company_id
LIMIT 10;

-- 8. Fetch peer groups mappings showing company names and their peers
SELECT c1.company_name AS company, c2.company_name AS peer
FROM peer_groups pg
JOIN companies c1 ON pg.company_id = c1.company_id
JOIN companies c2 ON pg.peer_company_id = c2.company_id
LIMIT 10;

-- 9. Rank companies by interest coverage ratio in FY2025
SELECT c.company_name, fr.interest_coverage_ratio
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.company_id
WHERE fr.year = 2025
ORDER BY fr.interest_coverage_ratio DESC
LIMIT 10;

-- 10. Audit balance sheet total asset size vs total liabilities for FY2025
SELECT c.company_name, b.total_assets, b.total_liabilities, b.total_equity, 
       ROUND(b.total_assets - (b.total_liabilities + b.total_equity), 2) AS balance_mismatch
FROM balancesheet b
JOIN companies c ON b.company_id = c.company_id
WHERE b.year = 2025
ORDER BY ABS(balance_mismatch) DESC
LIMIT 10;
