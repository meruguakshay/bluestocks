import os
import sqlite3
import pandas as pd
import streamlit as st

# Locate the database file relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "db", "nifty100.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

@st.cache_data(ttl=600)
def get_companies():
    """
    Returns all companies joined with their sector name.
    """
    conn = get_connection()
    query = """
    SELECT c.*, s.broad_sector
    FROM companies c
    LEFT JOIN sectors s ON c.sector_id = s.sector_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Returns ratios for a company. If year is provided (e.g. 2024), 
    returns a single de-duplicated record for that calendar year.
    """
    conn = get_connection()
    if year:
        year_str = str(year)
        query = f"""
        SELECT * FROM financial_ratios 
        WHERE company_id = '{ticker}' AND year LIKE '{year_str}-%'
        """
        df = pd.read_sql(query, conn)
        if not df.empty:
            # Sort: non-null return_on_equity_pct first, then prefer ends with -03
            df["is_null_roe"] = df["return_on_equity_pct"].isna()
            df["ends_with_03"] = df["year"].str.endswith("-03")
            df = df.sort_values(by=["is_null_roe", "ends_with_03"], ascending=[True, False])
            df = df.iloc[[0]]
            df = df.drop(columns=["is_null_roe", "ends_with_03"])
    else:
        query = f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}' ORDER BY year"
        df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Returns profit and loss statements.
    """
    conn = get_connection()
    query = f"SELECT * FROM profitandloss WHERE company_id = '{ticker}' ORDER BY year"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Returns balance sheet statements.
    """
    conn = get_connection()
    query = f"SELECT * FROM balancesheet WHERE company_id = '{ticker}' ORDER BY year"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Returns cash flow statements.
    """
    conn = get_connection()
    query = f"SELECT * FROM cashflow WHERE company_id = '{ticker}' ORDER BY year"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():
    """
    Returns all distinct broad sectors from the sectors table.
    """
    conn = get_connection()
    query = "SELECT * FROM sectors"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Returns all peer details for the given group name.
    """
    conn = get_connection()
    query = f"""
    SELECT pg.company_id, pg.peer_group_name, pg.is_benchmark, c.company_name, s.broad_sector
    FROM peer_groups pg
    LEFT JOIN companies c ON pg.company_id = c.company_id
    LEFT JOIN sectors s ON c.sector_id = s.sector_id
    WHERE pg.peer_group_name = '{group_name}'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Returns market cap and valuation metrics for a given ticker from the market_cap table.
    """
    conn = get_connection()
    query = f"SELECT * FROM market_cap WHERE company_id = '{ticker}' ORDER BY year"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_all_ratios_for_year(year):
    """
    Returns de-duplicated ratios for all companies in a single calendar year.
    Useful for overview and screener pages.
    """
    conn = get_connection()
    year_str = str(year)
    query = f"SELECT * FROM financial_ratios WHERE year LIKE '{year_str}-%'"
    df = pd.read_sql(query, conn)
    if not df.empty:
        df["is_null_roe"] = df["return_on_equity_pct"].isna()
        df["ends_with_03"] = df["year"].str.endswith("-03")
        df = df.sort_values(by=["company_id", "is_null_roe", "ends_with_03"], ascending=[True, True, False])
        df = df.drop_duplicates(subset=["company_id"], keep="first")
        df = df.drop(columns=["is_null_roe", "ends_with_03"])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_all_market_cap_for_year(year):
    """
    Returns market cap records for all companies in a single year.
    """
    conn = get_connection()
    year_str = str(year)
    query = f"SELECT * FROM market_cap WHERE year LIKE '{year_str}-%'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
