import pandas as pd

for name in ["balancesheet", "profitandloss", "companies"]:
    df = pd.read_excel(f"data/raw/{name}.xlsx")
    print(f"Columns for {name}:", df.columns.tolist())
    print(df.head(2).to_string())
    print("-"*40)
