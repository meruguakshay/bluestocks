import pandas as pd

# Load companies.xlsx
df_comp = pd.read_excel("data/raw/companies.xlsx")
print("First 5 rows of companies.xlsx:")
print(df_comp.head(5))

# Let's read by skipping the first row if there is a title row
df_comp2 = pd.read_excel("data/raw/companies.xlsx", skiprows=1)
print("\nFirst 5 rows with skiprows=1:")
print(df_comp2.head(5))
print("Columns with skiprows=1:", df_comp2.columns.tolist())

# Load financial_ratios.xlsx
df_ratios = pd.read_excel("data/raw/financial_ratios.xlsx")
print("\nfinancial_ratios.xlsx columns:", df_ratios.columns.tolist())
print(df_ratios.head(5))
