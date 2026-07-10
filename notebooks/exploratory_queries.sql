-- Nifty 100 Financial Intelligence Database - 10 Exploratory SQL Queries
-- Sprint 1 Wrap-up and Validation

-- Query 1: Total Row Counts Across All 12 Tables
-- Verifies the load completeness against raw file benchmarks.
SELECT 'sectors' AS table_name, COUNT(*) AS row_count FROM sectors
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap;


-- Query 2: Coverage Check - Companies with Less Than 5 Years of Data
-- Flags companies with thin financial histories for special treatment in CAGRs.
SELECT company_id, COUNT(*) AS years_count
FROM profitandloss
GROUP BY company_id
HAVING years_count < 5
ORDER BY years_count ASC;


-- Query 3: Count of Distinct Years in each Time-Series Table
-- Validates temporal coverage alignment.
SELECT 
    (SELECT COUNT(DISTINCT year) FROM profitandloss) AS pnl_distinct_years,
    (SELECT COUNT(DISTINCT year) FROM balancesheet) AS bs_distinct_years,
    (SELECT COUNT(DISTINCT year) FROM cashflow) AS cf_distinct_years,
    (SELECT COUNT(DISTINCT year) FROM financial_ratios) AS ratios_distinct_years;


-- Query 4: Year-Month Distribution in P&L
-- Displays coverage density per financial calendar year-month close.
SELECT year, COUNT(*) AS company_count
FROM profitandloss
GROUP BY year
ORDER BY year DESC;


-- Query 5: Missing Annual Reports Audit (Tearsheet Availability)
-- Identifies document coverage gaps where companies have less than 10 report URLs.
SELECT company_id, COUNT(*) AS report_count
FROM documents
GROUP BY company_id
HAVING report_count < 10
ORDER BY report_count ASC;


-- Query 6: Companies Null Value Scan
-- Checks for completeness of crucial qualitative and profile columns.
SELECT 
    COUNT(*) - COUNT(company_logo) AS missing_logos,
    COUNT(*) - COUNT(website) AS missing_websites,
    COUNT(*) - COUNT(about_company) AS missing_about_text,
    COUNT(*) - COUNT(face_value) AS missing_face_values
FROM companies;


-- Query 7: SQL-Level Balance Sheet Balance Validation
-- Calculates strict out-of-balance rows where Assets != Liabilities.
SELECT company_id, year, total_assets, total_liabilities, (total_assets - total_liabilities) AS discrepancy
FROM balancesheet
WHERE total_assets != total_liabilities
ORDER BY ABS(discrepancy) DESC;


-- Query 8: Average/Max Book Value and Face Value by Broad Sector
-- Aggregates dimensions at the sector level.
SELECT s.broad_sector, 
       ROUND(AVG(c.face_value), 2) AS avg_face_value, 
       ROUND(AVG(c.book_value), 2) AS avg_book_value,
       COUNT(c.company_id) AS company_count
FROM companies c
JOIN sectors s ON c.sector_id = s.sector_id
GROUP BY s.broad_sector
ORDER BY avg_book_value DESC;


-- Query 9: Peer Group Membership Check
-- Counts members in each of the 11 defined peer groups.
SELECT peer_group_name, 
       COUNT(company_id) AS members_count, 
       SUM(is_benchmark) AS benchmark_count
FROM peer_groups
GROUP BY peer_group_name
ORDER BY members_count DESC;


-- Query 10: Top 10 Companies by Index Weight
-- Highlights the most influential companies in the conformed universe.
SELECT c.company_id, c.company_name, s.broad_sector, c.index_weight_pct
FROM companies c
JOIN sectors s ON c.sector_id = s.sector_id
ORDER BY c.index_weight_pct DESC
LIMIT 10;
