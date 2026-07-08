import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

# =====================================================================
# 20+ UNIT TESTS FOR normalize_year()
# =====================================================================

@pytest.mark.parametrize("input_val, expected", [
    ("2023", 2023),
    (2023, 2023),
    ("FY23", 2023),
    ("FY 23", 2023),
    ("FY2023", 2023),
    ("FY 2023", 2023),
    ("23", 2023),
    ("2022-23", 2023),
    ("2022-2023", 2023),
    ("FY 2022-23", 2023),
    ("2022/23", 2023),
    ("2022/2023", 2023),
    ("FY 2022/2023", 2023),
    ("2011", 2011),
    ("11", 2011),
    ("FY11", 2011),
    (None, None),
    ("", None),
    ("abc", None),
    ("FY-abc", None),
    ("12345", 2345),
    ("2026", 2026),
    ("   2024   ", 2024),
    ("FY  25", 2025)
])
def test_normalize_year(input_val, expected):
    assert normalize_year(input_val) == expected


# =====================================================================
# 15+ UNIT TESTS FOR normalize_ticker()
# =====================================================================

@pytest.mark.parametrize("input_val, expected", [
    ("RELIANCE", "RELIANCE"),
    ("reliance", "RELIANCE"),
    ("  TCS  ", "TCS"),
    ("INFY.NS", "INFY"),
    ("500325.BO", "500325"),
    ("RELIANCE.NS", "RELIANCE"),
    ("reliance.ns", "RELIANCE"),
    ("TCS.BO", "TCS"),
    ("HDFCBANK.NS", "HDFCBANK"),
    ("SBIN.NS", "SBIN"),
    ("TATAMOTORS.NS", "TATAMOTORS"),
    ("ITC.BO", "ITC"),
    (None, None),
    ("", None),
    ("   ", None),
    (".NS", None),
    ("A B C", "ABC"),
    ("TICKER-A", "TICKER-A"),
    ("WIPRO.NS", "WIPRO"),
    ("  INFY.NS  ", "INFY")
])
def test_normalize_ticker(input_val, expected):
    assert normalize_ticker(input_val) == expected
