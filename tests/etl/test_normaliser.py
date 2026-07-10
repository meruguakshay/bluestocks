import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

# =====================================================================
# 20+ UNIT TESTS FOR normalize_year()
# =====================================================================

@pytest.mark.parametrize("input_val, expected", [
    ("2023", "2023-03"),
    (2023, "2023-03"),
    ("FY23", "2023-03"),
    ("FY 23", "2023-03"),
    ("FY2023", "2023-03"),
    ("FY 2023", "2023-03"),
    ("23", "2023-03"),
    ("2022-23", "2023-03"),
    ("2022-2023", "2023-03"),
    ("FY 2022-23", "2023-03"),
    ("2022/23", "2023-03"),
    ("2022/2023", "2023-03"),
    ("FY 2022/2023", "2023-03"),
    ("2011", "2011-03"),
    ("11", "2011-03"),
    ("FY11", "2011-03"),
    ("Dec-22", "2022-12"),
    ("Mar-23", "2023-03"),
    ("Mar 23", "2023-03"),
    ("March-2023", "2023-03"),
    ("Jun-23", "2023-06"),
    ("2023-03", "2023-03"),
    ("TTM", None),
    (None, None),
    ("", None),
    ("   ", None),
    ("abc", None),
    ("FY-abc", None),
    ("12345", "2345-03"),
    ("2026", "2026-03"),
    ("   2024   ", "2024-03"),
    ("FY  25", "2025-03")
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
    ("M&M", "M&M"),
    ("m&m.ns", "M&M"),
    ("BAJAJ-AUTO.NS", "BAJAJ-AUTO"),
    ("bajaj-auto", "BAJAJ-AUTO"),
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
