import pytest
from src.analytics.cashflow_kpis import (
    calculate_fcf,
    calculate_cfo_quality,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation
)

def test_fcf_normal():
    # operating = 100.0, investing = -40.0 -> FCF = 60.0
    assert calculate_fcf(100.0, -40.0) == 60.0
    # negative FCF is allowed
    assert calculate_fcf(50.0, -90.0) == -40.0

def test_cfo_quality_bands():
    # CFO Quality Score is average of last 5 years ratios
    # 1. High Quality (>1.0)
    cfo_h = [120, 150, 110, 130, 140]
    pat_h = [100, 100, 100, 100, 100]
    avg, label = calculate_cfo_quality(cfo_h, pat_h)
    assert avg == 1.3
    assert label == "High Quality"

    # 2. Moderate (0.5 to 1.0)
    cfo_m = [70, 80, 75, 85, 90]
    pat_m = [100, 100, 100, 100, 100]
    avg, label = calculate_cfo_quality(cfo_m, pat_m)
    assert avg == 0.8
    assert label == "Moderate"

    # 3. Accrual Risk (<0.5)
    cfo_a = [30, 40, 20, 45, 15]
    pat_a = [100, 100, 100, 100, 100]
    avg, label = calculate_cfo_quality(cfo_a, pat_a)
    assert avg == 0.3
    assert label == "Accrual Risk"

def test_cfo_quality_zero_pat():
    cfo_h = [120, 150, 110, 130, 140]
    pat_h = [100, 100, 100, 100, 0.0]
    avg, label = calculate_cfo_quality(cfo_h, pat_h)
    assert avg is None
    assert label is None

def test_capex_intensity():
    # CFI = -20.0, sales = 1000.0 -> intensity = (20 / 1000) * 100 = 2.0% (Asset Light)
    pct, label = calculate_capex_intensity(-20.0, 1000.0)
    assert pct == 2.0
    assert label == "Asset Light"

    # CFI = -50.0, sales = 1000.0 -> intensity = 5.0% (Moderate)
    pct, label = calculate_capex_intensity(-50.0, 1000.0)
    assert pct == 5.0
    assert label == "Moderate"

    # CFI = -100.0, sales = 1000.0 -> intensity = 10.0% (Capital Intensive)
    pct, label = calculate_capex_intensity(-100.0, 1000.0)
    assert pct == 10.0
    assert label == "Capital Intensive"

def test_fcf_conversion():
    assert calculate_fcf_conversion(50.0, 100.0) == 50.0
    assert calculate_fcf_conversion(50.0, 0.0) is None

def test_capital_allocation_classifier():
    # (+,-,-) with high CFO/PAT (CFO=120, PAT=100 -> ratio=1.2) -> Shareholder Returns
    cfo, cfi, cff, label = classify_capital_allocation(120.0, -40.0, -30.0, 100.0)
    assert label == "Shareholder Returns"

    # (+,-,-) with normal CFO/PAT -> Reinvestor
    cfo, cfi, cff, label = classify_capital_allocation(80.0, -40.0, -30.0, 100.0)
    assert label == "Reinvestor"

    # (+,+,-) -> Liquidating Assets
    cfo, cfi, cff, label = classify_capital_allocation(80.0, 40.0, -30.0, 100.0)
    assert label == "Liquidating Assets"

    # (-,+,+) -> Distress Signal
    cfo, cfi, cff, label = classify_capital_allocation(-80.0, 40.0, 30.0, 100.0)
    assert label == "Distress Signal"
