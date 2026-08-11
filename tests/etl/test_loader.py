import pytest
import os
import pandas as pd
from src.etl.loader import read_raw_file

def test_load_sectors():
    df = read_raw_file("sectors.xlsx", has_banner=False)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "broad_sector" in df.columns

def test_load_companies():
    df = read_raw_file("companies.xlsx", has_banner=True)
    assert len(df) > 0
    assert "id" in df.columns
    assert "company_name" in df.columns

def test_load_profitandloss():
    df = read_raw_file("profitandloss.xlsx", has_banner=True)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "sales" in df.columns
    assert "net_profit" in df.columns

def test_load_balancesheet():
    df = read_raw_file("balancesheet.xlsx", has_banner=True)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "equity_capital" in df.columns
    assert "reserves" in df.columns

def test_load_cashflow():
    df = read_raw_file("cashflow.xlsx", has_banner=True)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "operating_activity" in df.columns

def test_load_financial_ratios():
    df = read_raw_file("financial_ratios.xlsx", has_banner=False)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "return_on_equity_pct" in df.columns

def test_load_stock_prices():
    df = read_raw_file("stock_prices.xlsx", has_banner=False)
    assert len(df) > 0
    assert "ticker" in df.columns or "company_id" in df.columns
    assert "close_price" in df.columns

def test_load_documents():
    df = read_raw_file("documents.xlsx", has_banner=True)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "Annual_Report" in df.columns

def test_load_prosandcons():
    df = read_raw_file("prosandcons.xlsx", has_banner=True)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "pros" in df.columns

def test_load_market_cap():
    df = read_raw_file("market_cap.xlsx", has_banner=False)
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "market_cap_crore" in df.columns
