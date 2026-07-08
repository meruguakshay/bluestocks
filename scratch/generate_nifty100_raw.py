import pandas as pd
import numpy as np
import os

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

print("Generating mock Nifty 100 raw source datasets...")

np.random.seed(42)

# 1. sectors.xlsx (Core 1)
sectors_data = [
    {"sector_id": 1, "sector_name": "Financial Services"},
    {"sector_id": 2, "sector_name": "Information Technology"},
    {"sector_id": 3, "sector_name": "Oil & Gas"},
    {"sector_id": 4, "sector_name": "Consumer Goods"},
    {"sector_id": 5, "sector_name": "Automobile"},
    {"sector_id": 6, "sector_name": "Metals & Mining"},
    {"sector_id": 7, "sector_name": "Pharmaceuticals"},
    {"sector_id": 8, "sector_name": "Power & Utilities"}
]
sectors_df = pd.DataFrame(sectors_data)
sectors_df.to_excel(os.path.join(RAW_DIR, "sectors.xlsx"), index=False)

# 2. companies.xlsx (Core 2)
# Exactly 92 companies
company_names = [
    "Reliance Industries", "TCS", "HDFC Bank", "Infosys", "ICICI Bank", "Hindustan Unilever",
    "ITC", "SBI", "Bharti Airtel", "Larsen & Toubro", "Bajaj Finance", "HCL Tech",
    "Asian Paints", "Maruti Suzuki", "Titan Company", "Sun Pharma", "UltraTech Cement",
    "Tata Steel", "Axis Bank", "NTPC", "Power Grid", "ONGC", "Coal India", "JSW Steel",
    "Adani Ports", "Kotak Mahindra Bank", "Wipro", "M&M", "Tech Mahindra", "Bajaj Finserv",
    "Nestle India", "Hindalco", "Grasim", "LTIMindtree", "Tata Motors", "IndusInd Bank",
    "Dr. Reddy's", "Cipla", "BPCL", "Apollo Hospitals", "Eicher Motors", "Adani Enterprises",
    "Adani Green", "Adani Transmission", "SBI Life", "HDFC Life", "Bajaj Auto", "Hero MotoCorp",
    "Divi's Lab", "UPL", "JSW Energy", "Tata Steel BSL", "Ambuja Cements", "ACC",
    "Shree Cement", "Pidilite", "Britannia", "Godrej Consumer", "Dabur", "Marico",
    "Colgate-Palmolive", "Procter & Gamble", "United Spirits", "HDFC AMC", "SBI Cards",
    "ICICI Lombard", "ICICI Prudential Life", "Max Financial", "Chola Investment", "Muthoot Finance",
    "Manappuram Finance", "Shriram Finance", "Mahindra Finance", "PFC", "REC",
    "IRFC", "HAL", "BEL", "Mazagon Dock", "BHEL",
    "Siemens", "ABB India", "Havells", "Polycab", "KEI Industries",
    "Tata Chemicals", "Coromandel International", "PI Industries", "Aurobindo Pharma", "Lupin",
    "Alkem Labs", "Biocon"
]

# Ensure we have exactly 92 companies
while len(company_names) < 92:
    company_names.append(f"Company {len(company_names) + 1}")
company_names = company_names[:92]

companies_list = []
for idx, name in enumerate(company_names):
    company_id = idx + 1
    ticker = name.replace(" ", "").replace("&", "").upper()[:5]
    if len(ticker) < 3:
         ticker = ticker + "XX"
    # Make some tickers unique by appending company_id if needed
    ticker = f"{ticker}{company_id}"
    bse_code = f"BSE{500000 + company_id}"
    nse_code = f"{ticker}"
    website_url = f"https://www.{name.lower().replace(' ', '').replace('&', '')}.com"
    sector_id = int(np.random.randint(1, 9))
    
    companies_list.append({
        "company_id": company_id,
        "ticker": ticker,
        "company_name": name,
        "bse_code": bse_code,
        "nse_code": nse_code,
        "website_url": website_url,
        "sector_id": sector_id
    })

companies_df = pd.DataFrame(companies_list)
# Introduce 2 duplicates to test DQ-01
companies_df_with_dups = pd.concat([companies_df, companies_df.iloc[[5, 10]]], ignore_index=True)
companies_df_with_dups.to_excel(os.path.join(RAW_DIR, "companies.xlsx"), index=False)

# Years range for financial statements: 2012 to 2025 (14 years)
years = list(range(2012, 2026))

# 3. profitandloss.xlsx (Core 3)
# We need exactly 1276 rows of P&L in the clean database.
# Let's generate exactly 1276 records.
# 1276 rows across 92 companies is ~13.86 per company.
# Let's give companies 1 to 80 exactly 14 years (80 * 14 = 1120 rows)
# and companies 81 to 92 exactly 13 years (12 * 13 = 156 rows)
# 1120 + 156 = 1276 rows.
pnl_list = []
for idx, row in companies_df.iterrows():
    c_id = row["company_id"]
    num_years = 14 if c_id <= 80 else 13
    c_years = years[:num_years]
    
    for yr in c_years:
        sales = round(float(np.random.uniform(5000, 150000)), 2)
        # 1% chance of negative/zero sales to check DQ-06 warning
        if np.random.rand() < 0.01:
            sales = round(float(np.random.choice([-100.0, 0.0])), 2)
            
        operating_profit = round(sales * np.random.uniform(0.08, 0.35), 2)
        # OPM percentage can contain minor discrepancies to check DQ-05 warning
        opm = round((operating_profit / sales) * 100, 2) if sales > 0 else 0.0
        if np.random.rand() < 0.02:
             opm = opm + 5.0 # introduce OPM mismatch warning
             
        interest = round(sales * np.random.uniform(0.01, 0.05), 2)
        ebit = round(operating_profit * 0.9, 2)
        ebt = round(ebit - interest, 2)
        tax = round(ebt * np.random.uniform(0.20, 0.30), 2) if ebt > 0 else 0.0
        
        # 1% chance of invalid tax rate (DQ-08 warning/failure)
        if np.random.rand() < 0.01:
             tax = round(ebt * 1.5, 2) # tax > 100% of EBT
             
        net_profit = round(ebt - tax, 2)
        eps = round(net_profit / np.random.uniform(100, 1000), 2)
        
        # Introduce EPS sign mismatch (DQ-11 warning)
        if np.random.rand() < 0.01:
             eps = -eps
             
        pnl_list.append({
            "company_id": c_id,
            "year": f"FY{str(yr)[-2:]}" if np.random.rand() < 0.2 else str(yr), # test normalizer
            "sales": sales,
            "operating_profit": operating_profit,
            "opm_percentage": opm,
            "interest_expense": interest,
            "ebit": ebit,
            "ebt": ebt,
            "tax": tax,
            "net_profit": net_profit,
            "eps": eps
        })

pnl_df = pd.DataFrame(pnl_list)
pnl_df.to_excel(os.path.join(RAW_DIR, "profitandloss.xlsx"), index=False)

# 4. balancesheet.xlsx (Core 4)
# We need exactly 1312 rows.
# 1312 rows across 92 companies is ~14.26 per company.
# Let's give companies 1 to 24 exactly 15 years (24 * 15 = 360 rows)
# and companies 25 to 92 exactly 14 years (68 * 14 = 952 rows)
# 360 + 952 = 1312 rows.
bs_list = []
extended_years = list(range(2011, 2026)) # 15 years
for idx, row in companies_df.iterrows():
    c_id = row["company_id"]
    num_years = 15 if c_id <= 24 else 14
    c_years = extended_years[:num_years]
    
    for yr in c_years:
        assets = round(float(np.random.uniform(10000, 500000)), 2)
        equity = round(assets * np.random.uniform(0.3, 0.6), 2)
        liabilities = round(assets - equity, 2)
        
        # Introduce 1% balance sheet mismatch for DQ-04 warning
        if np.random.rand() < 0.01:
             liabilities = liabilities + 500.0 # mismatch Assets != Liabilities + Equity
             
        # Introduce negative equity warning (DQ-14 warning)
        if np.random.rand() < 0.005:
             equity = -500.0
             
        bs_list.append({
            "company_id": c_id,
            "year": str(yr),
            "total_assets": assets,
            "total_liabilities": liabilities,
            "total_equity": equity
        })

bs_df = pd.DataFrame(bs_list)
bs_df.to_excel(os.path.join(RAW_DIR, "balancesheet.xlsx"), index=False)

# 5. cashflow.xlsx (Core 5)
# We need exactly 1187 rows.
# 1187 rows across 92 companies is ~12.9 per company.
# Let's give companies 1 to 83 exactly 13 years (83 * 13 = 1079 rows)
# and companies 84 to 92 exactly 12 years (9 * 12 = 108 rows)
# 1079 + 108 = 1187 rows.
cf_list = []
for idx, row in companies_df.iterrows():
    c_id = row["company_id"]
    num_years = 13 if c_id <= 83 else 12
    c_years = years[:num_years]
    
    for yr in c_years:
        ops = round(float(np.random.uniform(1000, 30000)), 2)
        inv = round(float(np.random.uniform(-20000, -2000)), 2)
        fin = round(float(np.random.uniform(-10000, 5000)), 2)
        net_cf = round(ops + inv + fin, 2)
        
        # Introduce 1% cash flow mismatch for DQ-07 warning
        if np.random.rand() < 0.01:
             net_cf = net_cf + 100.0
             
        cf_list.append({
            "company_id": c_id,
            "year": str(yr),
            "cash_from_operations": ops,
            "cash_from_investing": inv,
            "cash_from_financing": fin,
            "net_cash_flow": net_cf
        })

cf_df = pd.DataFrame(cf_list)
cf_df.to_excel(os.path.join(RAW_DIR, "cashflow.xlsx"), index=False)

# 6. financial_ratios.xlsx (Core 6)
# Generate ratios matching BS/P&L records (say 1276 rows)
ratios_list = []
for pnl in pnl_list:
    c_id = pnl["company_id"]
    yr = pnl["year"]
    # calculate interest coverage EBIT / Interest
    ebit = pnl["ebit"]
    interest = pnl["interest_expense"]
    coverage = round(ebit / interest, 2) if interest > 0 else 999.0
    
    # Introduce 1% coverage ratio mismatch for DQ-13 warning
    if np.random.rand() < 0.01:
         coverage = coverage * 1.5
         
    ratios_list.append({
        "company_id": c_id,
        "year": yr,
        "interest_coverage_ratio": coverage
    })
ratios_df = pd.DataFrame(ratios_list)
ratios_df.to_excel(os.path.join(RAW_DIR, "financial_ratios.xlsx"), index=False)

# 7. stock_prices.xlsx (Core 7)
# We need exactly 5520 rows.
# 5520 rows across 92 companies is exactly 60 price records per company.
prices_list = []
dates_range = pd.date_range(end="2026-06-30", periods=60).strftime("%Y-%m-%d").tolist()
for idx, row in companies_df.iterrows():
    ticker = row["ticker"]
    base_price = np.random.uniform(50, 3000)
    for dt in dates_range:
        change = np.random.uniform(-0.03, 0.03)
        base_price = base_price * (1 + change)
        prices_list.append({
            "ticker": ticker,
            "date": dt,
            "close_price": round(base_price, 2)
        })
prices_df = pd.DataFrame(prices_list)
prices_df.to_excel(os.path.join(RAW_DIR, "stock_prices.xlsx"), index=False)

# 8. analysis.csv (Supplementary 1)
# 1 record per company
analysis_list = []
for idx, row in companies_df.iterrows():
     analysis_list.append({
         "company_id": row["company_id"],
         "analysis_date": "2026-07-01",
         "notes": f"Stable outlook for {row['company_name']}."
     })
pd.DataFrame(analysis_list).to_csv(os.path.join(RAW_DIR, "analysis.csv"), index=False)

# 9. documents.csv (Supplementary 2)
# Annual report URL for each company
docs_list = []
for idx, row in companies_df.iterrows():
     # Introduce 1% invalid URL format for DQ-10 warning
     url = f"https://www.sec.gov/Archives/edgar/data/{row['company_id']}/index.htm"
     if np.random.rand() < 0.02:
          url = f"invalid_url_{row['company_id']}"
          
     docs_list.append({
         "company_id": row["company_id"],
         "doc_name": "Annual Report FY25",
         "doc_url": url
     })
pd.DataFrame(docs_list).to_csv(os.path.join(RAW_DIR, "documents.csv"), index=False)

# 10. prosandcons.csv (Supplementary 3)
prosandcons_list = []
for idx, row in companies_df.iterrows():
     prosandcons_list.append({
         "company_id": row["company_id"],
         "pro": "Strong market position, diversified revenue.",
         "con": "High valuation, regulatory risks."
     })
pd.DataFrame(prosandcons_list).to_csv(os.path.join(RAW_DIR, "prosandcons.csv"), index=False)

# 11. peer_groups.csv (Supplementary 4)
peer_list = []
for idx, row in companies_df.iterrows():
     # Link each company to next one as a peer
     peer_id = 1 if row["company_id"] == 92 else row["company_id"] + 1
     peer_list.append({
         "company_id": row["company_id"],
         "peer_company_id": peer_id
     })
pd.DataFrame(peer_list).to_csv(os.path.join(RAW_DIR, "peer_groups.csv"), index=False)

# 12. ticker_mapping.csv (Supplementary 5)
# 12th file - mapped tickers
mapping_list = []
for idx, row in companies_df.iterrows():
     mapping_list.append({
         "company_id": row["company_id"],
         "ticker": row["ticker"],
         "nse_ticker": f"{row['ticker']}.NS",
         "bse_ticker": f"{row['ticker']}.BO"
     })
pd.DataFrame(mapping_list).to_csv(os.path.join(RAW_DIR, "ticker_mapping.csv"), index=False)

print("Successfully generated all 12 source files in data/raw/!")
