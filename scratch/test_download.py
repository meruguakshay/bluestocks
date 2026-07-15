import urllib.request
import os

url = "https://docs.google.com/spreadsheets/d/128BcUaeF-KIH8QMaBbG6JpYRFLdcrD_A/export?format=xlsx"
output = "data/raw/market_cap_test.xlsx"

print(f"Downloading {url} to {output}...")
try:
    urllib.request.urlretrieve(url, output)
    print("Success! File size:", os.path.getsize(output))
except Exception as e:
    print("Error:", e)
