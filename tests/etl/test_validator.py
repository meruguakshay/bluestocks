import pytest
import pandas as pd
import os
from src.etl.validator import DataQualityValidator

def test_validator_rules():
    # Construct mock datasets with anomalies
    companies = pd.DataFrame([
        {"company_id": 1, "ticker": "RELIANCE", "company_name": "Reliance", "bse_code": "500325", "nse_code": "RELIANCE", "website_url": "https://reliance.com", "sector_id": 1},
        {"company_id": 1, "ticker": "RELIANCE-DUP", "company_name": "Reliance Dup", "bse_code": "500325", "nse_code": "RELIANCE", "website_url": "https://reliance.com", "sector_id": 1}, # DQ-01 dup PK
        {"company_id": 2, "ticker": "INVALID_TICKER$", "company_name": "Invalid Ticker", "bse_code": "500326", "nse_code": "INVALID", "website_url": "https://invalid.com", "sector_id": 99} # DQ-03 sector orphan, DQ-12 ticker format
    ])
    
    pnl = pd.DataFrame([
        {"company_id": 1, "year": 2023, "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 20.0, "interest_expense": 50.0, "ebit": 180.0, "ebt": 130.0, "tax": 30.0, "net_profit": 100.0, "eps": 10.0},
        {"company_id": 1, "year": 2023, "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 20.0, "interest_expense": 50.0, "ebit": 180.0, "ebt": 130.0, "tax": 30.0, "net_profit": 100.0, "eps": 10.0}, # DQ-02 composite PK dup
        {"company_id": 3, "year": 2023, "sales": -50.0, "operating_profit": 10.0, "opm_percentage": 10.0, "interest_expense": 2.0, "ebit": 8.0, "ebt": 6.0, "tax": 2.0, "net_profit": 4.0, "eps": 0.4}, # DQ-03 company orphan, DQ-06 negative sales
        {"company_id": 2, "year": 2023, "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 50.0, "interest_expense": 50.0, "ebit": 180.0, "ebt": 130.0, "tax": 200.0, "net_profit": -70.0, "eps": 5.0} # DQ-05 OPM mismatch, DQ-08 tax > 100%, DQ-11 EPS sign mismatch
    ])
    
    bs = pd.DataFrame([
        {"company_id": 1, "year": 2023, "total_assets": 5000.0, "total_liabilities": 2000.0, "total_equity": 3000.0},
        {"company_id": 2, "year": 2023, "total_assets": 5000.0, "total_liabilities": 2000.0, "total_equity": 4000.0}, # DQ-04 Assets != Liab + Equity
        {"company_id": 1, "year": 2024, "total_assets": 5000.0, "total_liabilities": 6000.0, "total_equity": -1000.0} # DQ-14 negative equity
    ])
    
    cf = pd.DataFrame([
        {"company_id": 1, "year": 2023, "cash_from_operations": 500.0, "cash_from_investing": -200.0, "cash_from_financing": -100.0, "net_cash_flow": 200.0},
        {"company_id": 2, "year": 2023, "cash_from_operations": 500.0, "cash_from_investing": -200.0, "cash_from_financing": -100.0, "net_cash_flow": 500.0} # DQ-07 net cash flow mismatch
    ])
    
    sectors = pd.DataFrame([
        {"sector_id": 1, "sector_name": "Technology"}
    ])
    
    docs = pd.DataFrame([
        {"company_id": 1, "doc_name": "Report", "doc_url": "invalid_url_format"} # DQ-10 invalid URL
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
    failures = validator.run_validation(data_dict)
    
    # Assert validation failures were logged
    assert len(failures) > 0
    assert "DQ-01" in failures['rule_id'].values
    assert "DQ-02" in failures['rule_id'].values
    assert "DQ-03" in failures['rule_id'].values
    assert "DQ-04" in failures['rule_id'].values
    assert "DQ-05" in failures['rule_id'].values
    assert "DQ-06" in failures['rule_id'].values
    assert "DQ-07" in failures['rule_id'].values
    assert "DQ-08" in failures['rule_id'].values
    assert "DQ-10" in failures['rule_id'].values
    assert "DQ-11" in failures['rule_id'].values
    assert "DQ-12" in failures['rule_id'].values
    assert "DQ-14" in failures['rule_id'].values
    
    # Check that output/validation_failures.csv was written
    assert os.path.exists("output/validation_failures.csv")
