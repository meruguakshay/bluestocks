import pytest
from src.analytics.ratios import (
    calculate_de,
    calculate_icr,
    calculate_asset_turnover,
    calculate_book_value_per_share
)

def test_de_normal():
    # borrowings = 50.0, equity = 10.0 + reserves = 90.0 -> D/E = 0.5
    assert calculate_de(50.0, 10.0, 90.0) == 0.5

def test_de_debt_free():
    # D/E must return 0.0 (not None) if borrowings = 0
    assert calculate_de(0.0, 10.0, 90.0) == 0.0
    assert calculate_de(0.0, -10.0, 0.0) == 0.0

def test_de_negative_equity():
    assert calculate_de(50.0, -10.0, 5.0) is None

def test_icr_normal():
    # operating_profit = 30.0, other_income = 10.0 -> earnings = 40.0
    # interest = 8.0 -> ICR = 5.0
    assert calculate_icr(30.0, 10.0, 8.0) == 5.0

def test_icr_debt_free():
    # interest = 0 returns None
    assert calculate_icr(30.0, 10.0, 0.0) is None

def test_asset_turnover_normal():
    # sales = 150.0, total_assets = 100.0 -> turnover = 1.5
    assert calculate_asset_turnover(150.0, 100.0) == 1.5

def test_asset_turnover_zero():
    assert calculate_asset_turnover(150.0, 0.0) is None

def test_book_value_per_share_normal():
    # equity_capital = 10.0, reserves = 90.0, face_value = 10.0 -> BVPS = (100 / 10) * 10 = 100.0
    assert calculate_book_value_per_share(10.0, 90.0, 10.0) == 100.0

def test_book_value_per_share_zero():
    assert calculate_book_value_per_share(0.0, 90.0, 10.0) is None
