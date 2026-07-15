import pandas as pd

df_bs = pd.read_excel("data/raw/balancesheet.xlsx", skiprows=1)
print("Columns for Balance Sheet:", df_bs.columns.tolist())
print("\nBEL rows in balancesheet.xlsx:")
print(df_bs[df_bs['company_id'] == 'BEL'].to_string())

df_pnl = pd.read_excel("data/raw/profitandloss.xlsx", skiprows=1)
print("\nBEL rows in profitandloss.xlsx:")
print(df_pnl[df_pnl['company_id'] == 'BEL'].to_string())
