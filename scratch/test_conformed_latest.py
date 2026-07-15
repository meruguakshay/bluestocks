import sqlite3
import pandas as pd
import numpy as np

# Load ratios code logic
from src.analytics.ratios import calculate_roce, calculate_roe

conn = sqlite3.connect("db/nifty100.db")

companies = pd.read_sql_query("SELECT * FROM companies", conn)
pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)

pnl_idx = pnl.set_index(["company_id", "year"])
bs_idx = bs.set_index(["company_id", "year"])

# Let's check RELIANCE for 2024-03
key_2024_03 = ("RELIANCE", "2024-03")
op_2024 = pnl_idx.loc[key_2024_03]["operating_profit"]
dep_2024 = pnl_idx.loc[key_2024_03]["depreciation"]
eq_2024 = bs_idx.loc[key_2024_03]["equity_capital"]
res_2024 = bs_idx.loc[key_2024_03]["reserves"]
borrow_2024 = bs_idx.loc[key_2024_03]["borrowings"]
np_2024 = pnl_idx.loc[key_2024_03]["net_profit"]

roce_2024_03 = calculate_roce(op_2024, dep_2024, eq_2024, res_2024, borrow_2024)
roe_2024_03 = calculate_roe(np_2024, eq_2024, res_2024)

# Get companies ref
rel_ref = companies[companies["company_id"] == "RELIANCE"].iloc[0]
ref_roce = rel_ref["roce_percentage"]
ref_roe = rel_ref["roe_percentage"]

print("RELIANCE 2024-03:")
print(f"  Computed ROCE: {roce_2024_03:.2f}% | Ref ROCE: {ref_roce:.2f}%")
print(f"  Computed ROE: {roe_2024_03:.2f}% | Ref ROE: {ref_roe:.2f}%")

conn.close()
