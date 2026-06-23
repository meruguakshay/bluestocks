"""
Day 1 — Live NAV Fetch
Tasks 4 & 5: Fetch NAV from mfapi.in for HDFC Top 100 + 5 Bluechip schemes
"""

import requests
import pandas as pd
import os
import time

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf"


# ─────────────────────────────────────────────
# TASK 4 — Fetch HDFC Top 100 Direct NAV
# ─────────────────────────────────────────────

def fetch_single_nav(scheme_code, scheme_name=""):
    url = f"{BASE_URL}/{scheme_code}"
    print(f"\n  Fetching: {scheme_name or scheme_code} → {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        meta        = data.get("meta", {})
        nav_records = data.get("data", [])

        if not nav_records:
            print(f"  ⚠  No NAV data returned for {scheme_code}")
            return None

        df = pd.DataFrame(nav_records)
        df["scheme_code"] = scheme_code
        df["scheme_name"] = meta.get("scheme_name", scheme_name)
        df["fund_house"]  = meta.get("fund_house", "")
        df["scheme_type"] = meta.get("scheme_type", "")

        # Convert types
        df["nav"]  = pd.to_numeric(df["nav"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        print(f"  ✓  {len(df)} NAV records | Latest NAV: {df.iloc[-1]['nav']} on {df.iloc[-1]['date'].date()}")
        return df

    except requests.exceptions.RequestException as e:
        print(f"  ✗  Request failed for {scheme_code}: {e}")
        return None


def task4_hdfc_top100():
    print("=" * 60)
    print("TASK 4 — HDFC Top 100 Direct NAV Fetch")
    print("=" * 60)

    df = fetch_single_nav(125497, "HDFC Top 100 Direct")

    if df is not None:
        path = os.path.join(RAW_DIR, "hdfc_top100_nav.csv")
        df.to_csv(path, index=False)
        print(f"\n  ✓ Saved to {path}")
        print(df.head())

    return df


# ─────────────────────────────────────────────
# TASK 5 — Fetch 5 Bluechip Scheme NAVs
# ─────────────────────────────────────────────

BLUECHIP_SCHEMES = {
    119551: "SBI Bluechip Direct",
    120503: "ICICI Pru Bluechip Direct",
    118632: "Nippon India Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}

def task5_bluechip_funds():
    print("\n" + "=" * 60)
    print("TASK 5 — Bluechip Funds NAV Fetch")
    print("=" * 60)

    all_dfs = []

    for code, name in BLUECHIP_SCHEMES.items():
        df = fetch_single_nav(code, name)
        if df is not None:
            all_dfs.append(df)
        time.sleep(0.5)   # be polite to the API

    if not all_dfs:
        print("\n  ✗ No data fetched")
        return None

    master_df = pd.concat(all_dfs, ignore_index=True)

    path = os.path.join(RAW_DIR, "bluechip_nav_all.csv")
    master_df.to_csv(path, index=False)

    print(f"\n  ✓ Combined dataset: {master_df.shape}")
    print(f"  ✓ Saved to {path}")

    # Quick summary per fund
    print("\n  Per-Fund Record Count:")
    print(master_df.groupby("scheme_name")["nav"].count().to_string())

    return master_df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    task4_hdfc_top100()
    task5_bluechip_funds()
    print("\n✅ live_nav_fetch.py complete")
