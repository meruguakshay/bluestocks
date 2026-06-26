# Data Dictionary — Bluestock Mutual Fund Database

This data dictionary documents the structure, columns, data types, business rules, and source references for the SQLite star schema and support tables in `bluestock_mf.db`.

---

## 1. dim_fund (Dimension Table)
* **Description**: Dimension table containing mutual fund scheme configurations and categories.
* **Source References**: Merged from raw `fund_master.csv` and `scheme_details.csv`.
* **Primary Key**: `scheme_code`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | PK | No | Unique AMFI code of the mutual fund scheme. |
| `isin` | TEXT | - | No | International Securities Identification Number for the scheme. |
| `scheme_name` | TEXT | - | No | Official name of the mutual fund scheme. |
| `fund_house` | TEXT | - | No | Asset Management Company (AMC) managing the fund. |
| `category` | TEXT | - | No | Broad asset class category (e.g., Equity, Debt, Hybrid). |
| `sub_category`| TEXT | - | No | Sub-classification category (e.g., Large Cap, Mid Cap, Balanced). |
| `risk_grade` | TEXT | - | No | Evaluated risk profile level (e.g., Low, Moderate, High, Very High). |

---

## 2. dim_date (Dimension Table)
* **Description**: Conformed date dimension table for temporal slicing and indexing.
* **Source References**: Generated from unique date ranges inside `nav_history.csv` and `investor_transactions.csv`.
* **Primary Key**: `date`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date` | TEXT | PK | No | Calendar date in `YYYY-MM-DD` string format. |
| `year` | INTEGER | - | No | Calendar year (e.g., 2025). |
| `month` | INTEGER | - | No | Calendar month index (1 to 12). |
| `day` | INTEGER | - | No | Day of the month (1 to 31). |
| `quarter` | INTEGER | - | No | Year quarter index (1 to 4). |
| `day_of_week` | INTEGER | - | No | Day index of the week (1 = Monday, 7 = Sunday). |
| `is_weekend` | INTEGER | - | No | Binary flag: `1` if weekend (Saturday/Sunday), `0` otherwise. |

---

## 3. fact_nav (Fact Table)
* **Description**: Historical daily Net Asset Value (NAV) records of schemes. Orphan schemes (999991, 999992) not in `dim_fund` have been filtered out to ensure referential integrity.
* **Source References**: Cleaned from raw `nav_history.csv` (forward-filled on weekends/holidays, then filtered for valid scheme codes in `dim_fund`).
* **Primary Key**: `(scheme_code, date)`
* **Foreign Keys**: 
  - `scheme_code` references `dim_fund(scheme_code)`
  - `date` references `dim_date(date)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | PK, FK | No | AMFI scheme identifier. |
| `date` | TEXT | PK, FK | No | Transaction/valuation date in `YYYY-MM-DD`. |
| `nav` | REAL | - | No | Cleaned, forward-filled Net Asset Value of the scheme. Must be > 0. |

---

## 4. fact_transactions (Fact Table)
* **Description**: Transaction ledger tracking investor purchases, redemptions, and SIPs.
* **Source References**: Cleaned from raw `investor_transactions.csv`.
* **Primary Key**: `transaction_id`
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`
  - `date` references `dim_date(date)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PK | No | Unique auto-incrementing transaction ledger identifier. |
| `investor_id` | INTEGER | - | No | Identifier for the investing client. |
| `scheme_code` | INTEGER | FK | No | AMFI scheme code purchased or redeemed. |
| `date` | TEXT | FK | No | Execution date in `YYYY-MM-DD`. |
| `transaction_type`| TEXT | - | No | Standardized type: `SIP`, `Lumpsum`, or `Redemption`. |
| `amount` | REAL | - | No | Absolute monetary value of the transaction. Must be > 0. |
| `kyc_status` | TEXT | - | No | Standardized customer KYC status: `Verified`, `Pending`, `Failed`. |
| `state` | TEXT | - | No | Geographical state of the transaction/investor. |

---

## 5. fact_performance (Fact Table)
* **Description**: Annualized returns and expense ratio metrics for schemes.
* **Source References**: Cleaned from raw `scheme_performance.csv`.
* **Primary Key**: `scheme_code`
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | PK, FK | No | AMFI scheme identifier. |
| `return_1yr` | REAL | - | Yes | Annualized return percentage over 1 year (e.g. 15.4). |
| `return_3yr` | REAL | - | Yes | Annualized return percentage over 3 years. |
| `return_5yr` | REAL | - | Yes | Annualized return percentage over 5 years. |
| `expense_ratio` | REAL | - | No | Yearly cost percentage charged to investors (clipped to 0.1% – 2.5%). |

---

## 6. fact_aum (Fact Table)
* **Description**: Total Assets Under Management (AUM) per AMC fund house.
* **Source References**: Cleaned from raw `amc_details.csv`.
* **Primary Key**: `amc_id`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `amc_id` | INTEGER | PK | No | Unique AMC identifier. |
| `amc_name` | TEXT | - | No | Name of the Asset Management Company. |
| `aum_crores` | REAL | - | No | Total Assets Under Management in Crores (INR). |

---

## 7. portfolio_holdings (Supporting Table)
* **Description**: Portfolio allocations detailing top company stocks held under each scheme.
* **Source References**: Cleaned from raw `portfolio_holdings.csv`.
* **Primary Key**: `id` (Auto-increment)
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | PK | No | Auto-incrementing row identifier. |
| `scheme_code` | INTEGER | FK | No | AMFI scheme code. |
| `company_name` | TEXT | - | No | Name of the corporate equity stock held. |
| `isin` | TEXT | - | No | ISIN code of the held security. |
| `weightage` | REAL | - | No | Portfolio weight allocation percentage (e.g., 8.5). |
| `sector` | TEXT | - | No | Industry sector classification of the security. |

---

## 8. benchmark_data (Supporting Table)
* **Description**: Comparative reference indexes and daily returns.
* **Source References**: Cleaned from raw `benchmark_data.csv`.
* **Primary Key**: `benchmark_id`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `benchmark_id` | INTEGER | PK | No | Unique index identifier. |
| `benchmark_name` | TEXT | - | No | Name of reference benchmark index (e.g. Nifty 50 TRI). |
| `daily_return` | REAL | - | No | Reference daily returns fraction (e.g. 0.0012). |

---

## 9. risk_metrics (Supporting Table)
* **Description**: Advanced statistical risk variables for each scheme.
* **Source References**: Cleaned from raw `risk_metrics.csv`.
* **Primary Key**: `scheme_code`
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | PK, FK | No | AMFI scheme identifier. |
| `beta` | REAL | - | Yes | Volatility metric relative to market benchmark. |
| `sharpe_ratio` | REAL | - | Yes | Performance efficiency metric relative to risk. |
| `alpha` | REAL | - | Yes | Excess risk-adjusted returns performance indicator. |
| `standard_deviation`| REAL | - | Yes | Standard deviation percentage indicating variance/risk. |

---

## 10. sip_data (Supporting Table)
* **Description**: Historical Systematic Investment Plan (SIP) returns for schemes.
* **Source References**: Cleaned from raw `sip_data.csv`.
* **Primary Key**: `scheme_code`
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | PK, FK | No | AMFI scheme identifier. |
| `sip_return_1yr` | REAL | - | Yes | Annualized return percentage of SIP over 1 year. |
| `sip_return_3yr` | REAL | - | Yes | Annualized return percentage of SIP over 3 years. |

---

## 11. investor_data (Supporting Table)
* **Description**: Client ledger matching investors with scheme and default investment values.
* **Source References**: Cleaned from raw `investor_data.csv`.
* **Primary Key**: `investor_id`
* **Foreign Keys**:
  - `scheme_code` references `dim_fund(scheme_code)`

| Column Name | Data Type | Key Type | Allow Null | Description |
| :--- | :--- | :--- | :--- | :--- |
| `investor_id` | INTEGER | PK | No | Unique investor identifier. |
| `name` | TEXT | - | No | Investor full client name. |
| `scheme_code` | INTEGER | FK | No | Default AMFI scheme code associated with client. |
| `investment_amount`| REAL | - | No | Default target investment size. |
