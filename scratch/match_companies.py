import pandas as pd
import os

df_comp = pd.read_excel("data/raw/companies.xlsx")
df_sect = pd.read_excel("data/raw/sectors_drive.xlsx")

tickers = list(df_sect["company_id"].unique())
names = list(df_comp["company_name"].unique())

print(f"Number of tickers: {len(tickers)}, Number of names: {len(names)}")

matches = {}
unmatched_tickers = list(tickers)
unmatched_names = list(names)

# Helper function to normalize name for comparison
def norm(n):
    return n.lower().replace(" ", "").replace("&", "").replace("-", "").replace(".", "").replace("limited", "").replace("ltd", "")

for t in list(unmatched_tickers):
    for n in list(unmatched_names):
        n_norm = norm(n)
        t_norm = norm(t)
        # If ticker is a prefix of name, or vice versa, or name contains ticker
        if t_norm in n_norm or n_norm in t_norm or (len(t_norm) >= 4 and t_norm[:4] in n_norm):
            matches[t] = n
            unmatched_tickers.remove(t)
            unmatched_names.remove(n)
            break

print(f"Matched {len(matches)} companies:")
for t, n in sorted(matches.items()):
    print(f"  {t:<15} -> {n}")

print(f"\nUnmatched tickers ({len(unmatched_tickers)}):", unmatched_tickers)
print(f"Unmatched names ({len(unmatched_names)}):", unmatched_names)
