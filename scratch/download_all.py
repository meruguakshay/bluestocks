import urllib.request
import os

files = {
    "financial_ratios_drive.xlsx": "1ubUE2GhMiuwesqpjNneVupWaky7bmSY7",
    "market_cap_drive.xlsx": "128BcUaeF-KIH8QMaBbG6JpYRFLdcrD_A",
    "peer_groups_drive.xlsx": "11xjpsbdP8Oi8Vh3EhL9TaCLxD7yLqVC9",
    "sectors_drive.xlsx": "1UTDuo5Qu84GuMOAT7Ttsrdfhj47KLYLD",
    "stock_prices_drive.xlsx": "1C7yK795D2_RffJGQmku0tOl7aQX5N9R8"
}

os.makedirs("data/raw", exist_ok=True)

for filename, doc_id in files.items():
    url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
    dest = os.path.join("data/raw", filename)
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [OK] Saved to {dest} ({os.path.getsize(dest)} bytes)")
    except Exception as e:
        print(f"  [ERROR] Failed to download {filename}: {e}")
