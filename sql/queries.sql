-- 10 Analytical SQL Queries for Bluestock Mutual Fund Analytics

-- 1. Top 5 Funds by AUM
-- Description: Retrieves the top 5 funds with the highest Assets Under Management (AUM) by joining the fund dimension and the AUM fact table.
SELECT 
    f.scheme_code, 
    f.scheme_name, 
    f.fund_house, 
    a.aum_crores AS aum_in_crores
FROM dim_fund f
JOIN fact_aum a ON f.fund_house = a.amc_name
ORDER BY a.aum_crores DESC
LIMIT 5;


-- 2. Average NAV Per Month
-- Description: Computes the average Net Asset Value (NAV) per month for each scheme code, showing the trend over time.
SELECT 
    scheme_code,
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav), 4) AS average_nav
FROM fact_nav
GROUP BY scheme_code, month
ORDER BY scheme_code, month;


-- 3. SIP YoY Growth
-- Description: Calculates the Year-over-Year (YoY) growth of aggregate SIP transaction amount.
WITH YearlySIP AS (
    SELECT 
        strftime('%Y', date) AS year,
        SUM(amount) AS total_sip_amount
    FROM fact_transactions
    WHERE transaction_type = 'SIP'
    GROUP BY year
)
SELECT 
    y1.year AS current_year,
    ROUND(y1.total_sip_amount, 2) AS current_year_amount,
    y2.year AS previous_year,
    ROUND(y2.total_sip_amount, 2) AS previous_year_amount,
    ROUND(((y1.total_sip_amount - y2.total_sip_amount) / y2.total_sip_amount) * 100, 2) AS yoy_growth_percent
FROM YearlySIP y1
LEFT JOIN YearlySIP y2 ON CAST(y1.year AS INTEGER) = CAST(y2.year AS INTEGER) + 1
ORDER BY current_year;


-- 4. Transactions by State
-- Description: Aggregates the total number of transactions and total transaction amount across different geographical states.
SELECT 
    state,
    COUNT(transaction_id) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_transaction_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_transaction_amount DESC;


-- 5. Funds with Expense Ratio < 1%
-- Description: Identifies mutual fund schemes with an expense ratio below 1.0%, indicating low cost.
SELECT 
    f.scheme_code, 
    f.scheme_name, 
    f.fund_house, 
    f.category,
    p.expense_ratio AS expense_ratio_percent
FROM dim_fund f
JOIN fact_performance p ON f.scheme_code = p.scheme_code
WHERE p.expense_ratio < 1.0
ORDER BY p.expense_ratio ASC;


-- 6. Top 5 Best Performing Funds (5-Year Return)
-- Description: Retrieves the top 5 funds with the highest 5-year return from the performance fact table.
SELECT 
    f.scheme_code, 
    f.scheme_name, 
    f.category,
    p.return_5yr AS return_5yr_percent
FROM dim_fund f
JOIN fact_performance p ON f.scheme_code = p.scheme_code
ORDER BY p.return_5yr DESC
LIMIT 5;


-- 7. High Value Investors with Pending KYC
-- Description: Identifies investors who have high total transaction amounts but whose KYC status is still pending, highlighting risk.
SELECT 
    investor_id,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_amount,
    kyc_status
FROM fact_transactions
WHERE kyc_status = 'Pending'
GROUP BY investor_id
HAVING total_amount > 50000
ORDER BY total_amount DESC;


-- 8. Weekend vs. Weekday Transaction Analysis
-- Description: Analyses transaction frequency and average amount on weekends vs. weekdays using the date dimension.
SELECT 
    d.is_weekend,
    CASE d.is_weekend WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(SUM(t.amount), 2) AS total_amount,
    ROUND(AVG(t.amount), 2) AS average_amount
FROM fact_transactions t
JOIN dim_date d ON t.date = d.date
GROUP BY d.is_weekend;


-- 9. Scheme Risk-Return Profiles (Sharpe Ratio and Returns)
-- Description: Pulls the 3-year performance returns together with Sharpe Ratio and Beta to see which schemes deliver better risk-adjusted returns.
SELECT 
    f.scheme_code, 
    f.scheme_name, 
    p.return_3yr AS return_3yr_percent,
    r.sharpe_ratio,
    r.beta
FROM dim_fund f
JOIN fact_performance p ON f.scheme_code = p.scheme_code
JOIN risk_metrics r ON f.scheme_code = r.scheme_code
ORDER BY r.sharpe_ratio DESC;


-- 10. Sector Exposure Weightage per Scheme Category
-- Description: Summarizes sector-wise total weightage and holdings count across mutual fund categories from portfolio holdings.
SELECT 
    f.category,
    ph.sector,
    COUNT(ph.company_name) AS stock_holdings_count,
    ROUND(SUM(ph.weightage), 2) AS total_weightage_percent
FROM portfolio_holdings ph
JOIN dim_fund f ON ph.scheme_code = f.scheme_code
GROUP BY f.category, ph.sector
ORDER BY f.category, total_weightage_percent DESC;
