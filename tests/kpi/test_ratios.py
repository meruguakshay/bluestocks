import pytest
import numpy as np
import pandas as pd
from src.analytics.ratios import calculate_roe, calculate_de, calculate_icr, calculate_opm
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import calculate_cfo_quality

# 1. ROE Tests (positive, negative, zero equity)
def test_roe_positive_equity():
    # profit=10, equity=2, reserves=8 -> total_eq=10 -> ROE = 100%
    assert calculate_roe(10.0, 2.0, 8.0) == 100.0
    assert calculate_roe(5.0, 10.0, 15.0) == 20.0

def test_roe_negative_equity():
    # reserves=-5, equity=2 -> total_eq=-3 -> returns None
    assert calculate_roe(10.0, 2.0, -5.0) is None
    assert calculate_roe(10.0, -2.0, -8.0) is None

def test_roe_zero_equity():
    assert calculate_roe(10.0, 0.0, 0.0) is None

def test_roe_none_inputs():
    assert calculate_roe(None, 2.0, 8.0) is None
    assert calculate_roe(10.0, None, None) is None

# 2. Debt-to-Equity (D/E) Tests
def test_de_debt_free():
    # borrowings=0 -> returns 0.0
    assert calculate_de(0.0, 10.0, 20.0) == 0.0
    assert calculate_de(None, 10.0, 20.0) == 0.0

def test_de_with_debt():
    # borrowings=10, total_eq=20 -> returns 0.5
    assert calculate_de(10.0, 5.0, 15.0) == 0.5

def test_de_invalid_equity():
    # total_eq <= 0 -> returns None
    assert calculate_de(10.0, -5.0, 2.0) is None
    assert calculate_de(10.0, 0.0, 0.0) is None

# 3. Interest Coverage Ratio (ICR) Tests
def test_icr_zero_interest():
    # interest = 0 -> returns None (or handled specially by caller as Debt Free)
    assert calculate_icr(100.0, 10.0, 0.0) is None
    assert calculate_icr(100.0, 10.0, None) is None

def test_icr_normal():
    # (OP + Other) / Interest = (100 + 20) / 10 = 12.0
    assert calculate_icr(100.0, 20.0, 10.0) == 12.0

# 4. CAGR Tests (turnarounds, declines, normal)
def test_cagr_insufficient_data():
    val, flag = calculate_cagr(100, None, 5)
    assert flag == "INSUFFICIENT"
    assert val is None

def test_cagr_zero_base():
    val, flag = calculate_cagr(100, 0, 5)
    assert flag == "ZERO_BASE"
    assert val is None

def test_cagr_decline_to_loss():
    val, flag = calculate_cagr(-50, 100, 5)
    assert flag == "DECLINE_TO_LOSS"
    assert val is None

def test_cagr_turnaround():
    val, flag = calculate_cagr(100, -50, 5)
    assert flag == "TURNAROUND"
    assert val is None

def test_cagr_both_negative():
    val, flag = calculate_cagr(-10, -50, 5)
    assert flag == "BOTH_NEGATIVE"
    assert val is None

def test_cagr_normal():
    # (32 / 2) ** (1 / 4) - 1 = 2 ** 1 - 1 = 1 -> 100%
    val, flag = calculate_cagr(32.0, 2.0, 4)
    assert flag is None
    assert pytest.approx(val) == 100.0

# 5. OPM Tests
def test_opm_normal():
    assert calculate_opm(20.0, 100.0) == 20.0

def test_opm_zero_sales():
    assert calculate_opm(20.0, 0.0) is None

# 6. CFO Quality Score Tests
def test_cfo_quality_normal():
    # cfo_list, pat_list
    # average ratio > 1.0 -> High Quality
    cfo = [120, 110, 130, 140, 150]
    pat = [100, 100, 100, 100, 100]
    score, label = calculate_cfo_quality(cfo, pat)
    assert label == "High Quality"
    assert score > 1.0

def test_cfo_quality_low():
    # average ratio < 0.5 -> Accrual Risk
    cfo = [40, 30, 20, 10, 5]
    pat = [100, 100, 100, 100, 100]
    score, label = calculate_cfo_quality(cfo, pat)
    assert label == "Accrual Risk"
    assert score < 0.5
