import pandas as pd

df = pd.read_excel("data/raw/financial_ratios.xlsx")
print("BEL ratios in financial_ratios.xlsx:")
print(df[df['company_id'] == 'BEL'].to_string())
