import pytest
from src.etl.normaliser import normalize_year

def test_already_normalised():
    assert normalize_year("2023-03") == "2023-03"
    assert normalize_year("2022-12") == "2022-12"

def test_fy_prefix():
    assert normalize_year("FY23") == "2023-03"
    assert normalize_year("FY 23") == "2023-03"
    assert normalize_year("FY-23") == "2023-03"

def test_year_ranges():
    assert normalize_year("2022-23") == "2023-03"
    assert normalize_year("2022/2023") == "2023-03"

def test_pure_digits():
    assert normalize_year("2023") == "2023-03"
    assert normalize_year("23") == "2023-03"
    assert normalize_year("2024") == "2024-03"

def test_month_name_and_year():
    assert normalize_year("Dec-22") == "2022-12"
    assert normalize_year("Jun-23") == "2023-06"
    assert normalize_year("March-2023") == "2023-03"
    assert normalize_year("Dec 2022") == "2022-12"
    assert normalize_year("Mar-23") == "2023-03"

def test_reversed_month_format():
    assert normalize_year("23-Mar") == "2023-03"
    assert normalize_year("2023-March") == "2023-03"

def test_ttm_and_none():
    assert normalize_year("TTM") is None
    assert normalize_year("ttm") is None
    assert normalize_year(None) is None
    assert normalize_year("") is None

def test_invalid_strings():
    assert normalize_year("invalid") is None
    assert normalize_year("abc") is None
    assert normalize_year("  ") is None
