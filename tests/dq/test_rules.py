import pytest
import pandas as pd
from src.etl.validator import DataQualityValidator

@pytest.fixture
def empty_dict():
    return {
        "companies": pd.DataFrame(columns=["company_id", "company_name", "sector_id", "roe_percentage", "roce_percentage", "market_cap_category"]),
        "profitandloss": pd.DataFrame(columns=["company_id", "year", "sales", "operating_profit", "opm_percentage", "net_profit", "eps", "tax_percentage", "dividend_payout"]),
        "balancesheet": pd.DataFrame(columns=["company_id", "year", "total_assets", "total_liabilities", "fixed_assets", "equity_capital", "reserves", "borrowings"]),
        "cashflow": pd.DataFrame(columns=["company_id", "year", "operating_activity", "investing_activity", "financing_activity", "net_cash_flow"]),
        "stock_prices": pd.DataFrame(columns=["company_id", "close_price"]),
        "sectors": pd.DataFrame(columns=["company_id", "broad_sector"]),
        "financial_ratios": pd.DataFrame(columns=["company_id", "year", "return_on_equity_pct", "debt_to_equity"]),
        "documents": pd.DataFrame(columns=["company_id", "year", "annual_report"]),
        "analysis": pd.DataFrame(columns=["company_id", "report_date"]),
        "prosandcons": pd.DataFrame(columns=["company_id", "pros", "cons"]),
        "peer_groups": pd.DataFrame(columns=["company_id", "peer_group_name"]),
        "market_cap": pd.DataFrame(columns=["company_id", "year", "market_cap_crore"])
    }

def test_rule_dq01_company_pk_uniqueness(empty_dict):
    validator = DataQualityValidator()
    # Duplicate companies
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "Tata Consultancy Services Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"},
        {"company_id": "TCS", "company_name": "TCS Dup", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    failures = validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-01" and f["severity"] == "CRITICAL" for f in validator.failures)

def test_rule_dq02_annual_pk_uniqueness(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # Duplicate annual records
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 50.0},
        {"company_id": "TCS", "year": "2024-03", "sales": 110.0, "operating_profit": 22.0, "opm_percentage": 20.0, "net_profit": 16.0, "eps": 11.0, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-02" and f["severity"] == "CRITICAL" for f in validator.failures)

def test_rule_dq03_foreign_key_integrity(empty_dict):
    validator = DataQualityValidator()
    # Company TCS exists, but we have pnl for orphan INF
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "INF", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-03" and f["severity"] == "CRITICAL" for f in validator.failures)

def test_rule_dq04_balance_sheet_balance(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # total_assets=100, total_liabilities=120 (diff=20%)
    empty_dict["balancesheet"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "total_assets": 100.0, "total_liabilities": 120.0, "fixed_assets": 50.0, "equity_capital": 10.0, "reserves": 90.0, "borrowings": 20.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-04" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq05_opm_cross_check(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # sales=100, op=20 -> calc_opm=20%. But opm_percentage=15%
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 15.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-05" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq06_positive_sales(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    empty_dict["sectors"] = pd.DataFrame([
        {"company_id": "TCS", "broad_sector": "IT"} # Non-bank
    ])
    # sales <= 0
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 0.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-06" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq07_year_format(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # Invalid year
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "invalid_year", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-07" and f["severity"] == "CRITICAL" for f in validator.failures)

def test_rule_dq08_ticker_format(empty_dict):
    validator = DataQualityValidator()
    # Invalid ticker format (too short)
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "A", "company_name": "A Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-08" and f["severity"] == "CRITICAL" for f in validator.failures)

def test_rule_dq09_net_cash_check(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # CFO=10, CFI=10, CFF=10 -> sum=30. Net cash=50 (diff=20 > 10)
    empty_dict["cashflow"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "operating_activity": 10.0, "investing_activity": 10.0, "financing_activity": 10.0, "net_cash_flow": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-09" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq10_fixed_assets_non_negative(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # negative fixed assets
    empty_dict["balancesheet"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "total_assets": 100.0, "total_liabilities": 100.0, "fixed_assets": -5.0, "equity_capital": 10.0, "reserves": 90.0, "borrowings": 0.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-10" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq11_tax_rate_range(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # tax rate = 70% (outside 0-60%)
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 70.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-11" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq12_dividend_payout_cap(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # dividend payout = 250% (exceeds 200%)
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 15.0, "eps": 10.0, "tax_percentage": 25.0, "dividend_payout": 250.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-12" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq13_url_validity(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # invalid url
    empty_dict["documents"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "annual_report": "invalid_url"}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-13" and f["severity"] == "WARNING" for f in validator.failures)

def test_rule_dq14_eps_sign_consistency(empty_dict):
    validator = DataQualityValidator()
    empty_dict["companies"] = pd.DataFrame([
        {"company_id": "TCS", "company_name": "TCS Ltd", "sector_id": 1, "roe_percentage": 30.0, "roce_percentage": 35.0, "market_cap_category": "Large Cap"}
    ])
    # net_profit=10, eps=-1.5 (inconsistent signs)
    empty_dict["profitandloss"] = pd.DataFrame([
        {"company_id": "TCS", "year": "2024-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 20.0, "net_profit": 10.0, "eps": -1.5, "tax_percentage": 25.0, "dividend_payout": 50.0}
    ])
    validator.run_validation(empty_dict, output_path=None)
    assert any(f["rule_id"] == "DQ-14" and f["severity"] == "WARNING" for f in validator.failures)
