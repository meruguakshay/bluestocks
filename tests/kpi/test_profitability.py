import pytest
from src.analytics.ratios import (
    calculate_npm,
    calculate_opm,
    calculate_roe,
    calculate_roce,
    calculate_roa
)

def test_npm_normal():
    # net_profit = 15.0, sales = 100.0 -> NPM = 15.0%
    assert calculate_npm(15.0, 100.0) == 15.0
    assert calculate_npm(-5.0, 50.0) == -10.0

def test_npm_zero_sales():
    # NPM returns None if sales is 0
    assert calculate_npm(15.0, 0.0) is None
    assert calculate_npm(15.0, None) is None

def test_opm_normal():
    # operating_profit = 20.0, sales = 100.0 -> OPM = 20.0%
    assert calculate_opm(20.0, 100.0) == 20.0

def test_opm_zero_sales():
    assert calculate_opm(20.0, 0.0) is None

def test_roe_normal():
    # net_profit = 30.0, equity = 100.0 + reserves = 100.0 -> ROE = 15.0%
    assert calculate_roe(30.0, 100.0, 100.0) == 15.0

def test_roe_negative_or_zero_equity():
    # returns None if equity + reserves <= 0
    assert calculate_roe(30.0, -50.0, 10.0) is None
    assert calculate_roe(30.0, 0.0, 0.0) is None

def test_roce_normal():
    # operating_profit = 50.0, depr = 10.0 -> EBIT = 40.0
    # equity = 100.0, reserves = 100.0, borrowings = 200.0 -> Capital Employed = 400.0
    # ROCE = 40.0 / 400.0 x 100 = 10.0%
    assert calculate_roce(50.0, 10.0, 100.0, 100.0, 200.0) == 10.0

def test_roce_zero_capital():
    assert calculate_roce(50.0, 10.0, 0.0, 0.0, 0.0) is None
    assert calculate_roce(50.0, 10.0, -100.0, 50.0, 10.0) is None

def test_roa_normal():
    # net_profit = 10.0, total_assets = 200.0 -> ROA = 5.0%
    assert calculate_roa(10.0, 200.0) == 5.0

def test_roa_zero_assets():
    assert calculate_roa(10.0, 0.0) is None
