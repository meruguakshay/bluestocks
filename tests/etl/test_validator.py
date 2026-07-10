import pytest
import pandas as pd
import os
from src.etl.validator import DataQualityValidator

def test_validator_rules():
    # Construct mock datasets with anomalies matching conformed DQ rules
    companies = pd.DataFrame([
        {"company_id": "RELIANCE", "company_name": "Reliance"},
        {"company_id": "RELIANCE", "company_name": "Reliance Dup"},  # DQ-01 dup PK
        {"company_id": "TCS", "company_name": "TCS"},
        {"company_id": "INV@LID_TICKER_NAME_TOO_LONG", "company_name": "Invalid Ticker"}  # DQ-08 ticker format length / chars
    ])
    
    pnl = pd.DataFrame([
        {"company_id": "RELIANCE", "year": "2023-03", "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 20.0, "net_profit": 100.0, "eps": 10.0, "dividend_payout": 20.0, "tax_percentage": 25.0},
        {"company_id": "RELIANCE", "year": "2023-03", "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 20.0, "net_profit": 100.0, "eps": 10.0, "dividend_payout": 20.0, "tax_percentage": 25.0},  # DQ-02 composite PK dup
        {"company_id": "ORPHAN", "year": "2023-03", "sales": 500.0, "operating_profit": 100.0, "opm_percentage": 20.0, "net_profit": 50.0, "eps": 5.0, "dividend_payout": 10.0, "tax_percentage": 20.0},  # DQ-03 company orphan
        {"company_id": "TCS", "year": "2023-03", "sales": -50.0, "operating_profit": 10.0, "opm_percentage": -20.0, "net_profit": 5.0, "eps": 0.5, "dividend_payout": 0.0, "tax_percentage": 20.0},  # DQ-06 negative sales for non-bank
        {"company_id": "TCS", "year": "2024-03", "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 50.0, "net_profit": 100.0, "eps": 10.0, "dividend_payout": 250.0, "tax_percentage": 25.0},  # DQ-05 OPM mismatch, DQ-12 div payout > 200
        {"company_id": "TCS", "year": "2025-03", "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 20.0, "net_profit": 100.0, "eps": -10.0, "dividend_payout": 20.0, "tax_percentage": 85.0}  # DQ-11 tax > 60%, DQ-14 EPS sign mismatch
    ])
    
    bs = pd.DataFrame([
        {"company_id": "RELIANCE", "year": "2023-03", "total_assets": 5000.0, "total_liabilities": 5000.0, "fixed_assets": -10.0},  # DQ-10 negative fixed assets
        {"company_id": "TCS", "year": "2023-03", "total_assets": 5000.0, "total_liabilities": 2000.0, "fixed_assets": 1000.0}  # DQ-04 Assets != Liabilities, DQ-15 strict mismatch
    ])
    
    cf = pd.DataFrame([
        {"company_id": "RELIANCE", "year": "2023-03", "operating_activity": 500.0, "investing_activity": -200.0, "financing_activity": -100.0, "net_cash_flow": 500.0},  # DQ-09 net cash flow mismatch (sum=200)
        {"company_id": "TCS", "year": "2023-03", "operating_activity": 500.0, "investing_activity": -200.0, "financing_activity": -100.0, "net_cash_flow": 200.0}
    ])
    
    sectors = pd.DataFrame([
        {"company_id": "RELIANCE", "broad_sector": "Energy"},
        {"company_id": "TCS", "broad_sector": "IT"}
    ])
    
    docs = pd.DataFrame([
        {"company_id": "RELIANCE", "year": "2023-03", "annual_report": "invalid_url_format"}  # DQ-13 invalid URL
    ])
    
    data_dict = {
        "companies": companies,
        "profitandloss": pnl,
        "balancesheet": bs,
        "cashflow": cf,
        "sectors": sectors,
        "documents": docs
    }
    
    validator = DataQualityValidator()
    test_out = "output/test_validation_failures.csv"
    if os.path.exists(test_out):
        os.remove(test_out)
        
    failures = validator.run_validation(data_dict, output_path=test_out)
    
    # Assert validation failures were logged
    assert len(failures) > 0
    assert "DQ-01" in failures['rule_id'].values
    assert "DQ-02" in failures['rule_id'].values
    assert "DQ-03" in failures['rule_id'].values
    assert "DQ-04" in failures['rule_id'].values
    assert "DQ-05" in failures['rule_id'].values
    assert "DQ-06" in failures['rule_id'].values
    assert "DQ-08" in failures['rule_id'].values
    assert "DQ-09" in failures['rule_id'].values
    assert "DQ-10" in failures['rule_id'].values
    assert "DQ-11" in failures['rule_id'].values
    assert "DQ-12" in failures['rule_id'].values
    assert "DQ-13" in failures['rule_id'].values
    assert "DQ-14" in failures['rule_id'].values
    assert "DQ-15" in failures['rule_id'].values
    assert "DQ-16" in failures['rule_id'].values
    
    # Check that test failures file was written
    assert os.path.exists(test_out)
    os.remove(test_out)
