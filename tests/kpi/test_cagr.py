import pytest
from src.analytics.cagr import calculate_cagr

def test_cagr_normal():
    # start = 100.0, end = 161.051, n = 5 -> CAGR = 10.0%
    val, flag = calculate_cagr(161.051, 100.0, 5)
    assert val is not None
    assert round(val, 2) == 10.0
    assert flag is None

def test_cagr_decline_to_loss():
    # start = 100.0, end = -50.0 -> Decline to loss
    val, flag = calculate_cagr(-50.0, 100.0, 3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    # start = -100.0, end = 50.0 -> Turnaround
    val, flag = calculate_cagr(50.0, -100.0, 3)
    assert val is None
    assert flag == "TURNAROUND"

def test_cagr_both_negative():
    # start = -100.0, end = -50.0 -> Both negative
    val, flag = calculate_cagr(-50.0, -100.0, 3)
    assert val is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    # start = 0.0 -> Zero base
    val, flag = calculate_cagr(50.0, 0.0, 3)
    assert val is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient_data():
    # None or NaN values -> Insufficient
    val, flag = calculate_cagr(50.0, None, 3)
    assert val is None
    assert flag == "INSUFFICIENT"
    
    val2, flag2 = calculate_cagr(None, 100.0, 3)
    assert val2 is None
    assert flag2 == "INSUFFICIENT"
