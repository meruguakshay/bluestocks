import pytest
import pandas as pd
from src.etl.loader import clean_companies, clean_financials, clean_stock_prices

def test_clean_companies():
    # Setup data with duplicates and tickers in various casings
    df = pd.DataFrame([
        {"company_id": 1, "ticker": "reliance.ns", "company_name": "Reliance", "sector_id": 1},
        {"company_id": 1, "ticker": "RELIANCE", "company_name": "Reliance Dup", "sector_id": 1}, # duplicate company_id
        {"company_id": 2, "ticker": "  tcs.bo  ", "company_name": "TCS", "sector_id": 2}
    ])
    
    cleaned = clean_companies(df)
    
    # Assert row count is 2 (duplicates removed)
    assert len(cleaned) == 2
    assert set(cleaned['company_id']) == {1, 2}
    # Assert ticker normalization
    assert cleaned.loc[cleaned['company_id'] == 1, 'ticker'].values[0] == "RELIANCE"
    assert cleaned.loc[cleaned['company_id'] == 2, 'ticker'].values[0] == "TCS"

def test_clean_financials():
    df = pd.DataFrame([
        {"company_id": 1, "year": "FY23", "sales": 1000.0},
        {"company_id": 1, "year": "2023", "sales": 1200.0}, # duplicate (company_id, year)
        {"company_id": 1, "year": "2022-23", "sales": 1000.0}, # duplicate after normalization (FY23 and 2022-23 both resolve to 2023)
        {"company_id": 1, "year": "2024", "sales": 1500.0},
        {"company_id": 2, "year": "invalid_year", "sales": 800.0} # invalid year should be dropped
    ])
    
    cleaned = clean_financials(df)
    
    # Assert duplicates/invalid years are cleaned
    # "FY23", "2023", "2022-23" all map to year "2023-03". Only the first (FY23) is kept.
    # "2024" maps to "2024-03".
    # "invalid_year" -> year is None -> dropped.
    assert len(cleaned) == 2
    assert set(cleaned['year'].values) == {"2023-03", "2024-03"}

def test_clean_stock_prices():
    df = pd.DataFrame([
        {"ticker": "reliance.ns", "date": "2026-07-01", "close_price": 2400.0},
        {"ticker": "RELIANCE", "date": "2026-07-01", "close_price": 2405.0}, # duplicate ticker + date
        {"ticker": "tcs.bo", "date": "2026-07-01", "close_price": 3200.0}
    ])
    
    cleaned = clean_stock_prices(df)
    
    assert len(cleaned) == 2
    assert cleaned.loc[cleaned['company_id'] == "RELIANCE", 'close_price'].values[0] == 2400.0
