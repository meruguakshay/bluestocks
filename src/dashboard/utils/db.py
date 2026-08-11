import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


@st.cache_data(ttl=600)
def get_companies():
    """
    Returns all companies joined with their sector name.
    """
    response = requests.get(f"{API_URL}/companies")
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.rename(
            columns={
                "id": "company_id",
                "roe_pct": "roe_percentage",
                "roce_pct": "roce_percentage",
            }
        )
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Returns ratios for a company. If year is provided (e.g. 2024),
    returns a single de-duplicated record for that calendar year.
    """
    response = requests.get(f"{API_URL}/companies/{ticker}/ratios")
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()
    df = pd.DataFrame(data)
    if year and not df.empty:
        year_str = str(year)
        df = df[df["year"].str.startswith(year_str)]
        if not df.empty:
            df["is_null_roe"] = df["return_on_equity_pct"].isna()
            df["ends_with_03"] = df["year"].str.endswith("-03")
            df = df.sort_values(
                by=["is_null_roe", "ends_with_03"], ascending=[True, False]
            )
            df = df.iloc[[0]]
            df = df.drop(columns=["is_null_roe", "ends_with_03"])
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Returns profit and loss statements.
    """
    response = requests.get(f"{API_URL}/companies/{ticker}/pl")
    if response.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Returns balance sheet statements.
    """
    response = requests.get(f"{API_URL}/companies/{ticker}/bs")
    if response.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Returns cash flow statements.
    """
    response = requests.get(f"{API_URL}/companies/{ticker}/cashflow")
    if response.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=600)
def get_sectors():
    """
    Returns all distinct broad sectors from the sectors summary.
    """
    response = requests.get(f"{API_URL}/sectors")
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.rename(columns={"sector": "broad_sector"})
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Returns all peer details for the given group name.
    """
    # Fetch from peers endpoint
    response = requests.get(f"{API_URL}/peers/{group_name}")
    if response.status_code != 200:
        return pd.DataFrame()
    peers_data = response.json()

    # Get benchmark ticker by checking one ticker in comparison endpoint
    benchmark_ticker = None
    if peers_data:
        sample_ticker = peers_data[0]["company_id"]
        comp_resp = requests.get(f"{API_URL}/companies/{sample_ticker}/peers/compare")
        if comp_resp.status_code == 200:
            benchmark_ticker = comp_resp.json().get("benchmark_ticker")

    # Resolve names using get_companies()
    comp_df = get_companies()
    names_map = dict(zip(comp_df["company_id"], comp_df["company_name"]))
    sectors_map = dict(zip(comp_df["company_id"], comp_df["broad_sector"]))

    rows = []
    for item in peers_data:
        cid = item["company_id"]
        rows.append(
            {
                "company_id": cid,
                "peer_group_name": item["peer_group"],
                "is_benchmark": 1 if cid == benchmark_ticker else 0,
                "company_name": names_map.get(cid, cid),
                "broad_sector": sectors_map.get(cid, ""),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Returns market cap and valuation metrics for a given ticker.
    """
    response = requests.get(f"{API_URL}/market-cap/{ticker}")
    if response.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=600)
def get_all_ratios_for_year(year):
    """
    Returns de-duplicated ratios for all companies in a single calendar year.
    """
    # We can get this by running a screen with no filters (returns all ranked by composite score)
    # and converting fields to match the database ratios schema
    response = requests.get(f"{API_URL}/screener")
    if response.status_code != 200:
        return pd.DataFrame()

    screener_data = response.json()
    rows = []
    for item in screener_data:
        rows.append(
            {
                "company_id": item["ticker"],
                "return_on_equity_pct": item["roe"],
                "debt_to_equity": item["de"],
                "free_cash_flow_cr": item["fcf"],
                "revenue_cagr_5yr": item["revenue_cagr_5yr"],
                "pat_cagr_5yr": item["pat_cagr_5yr"],
                "composite_quality_score": item["composite_score"],
                "year": f"{year}-03",  # mock conformed year
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=600)
def get_all_market_cap_for_year(year):
    """
    Returns market cap records for all companies in a single year.
    """
    # Query all companies and get market-cap for each
    comp_df = get_companies()
    if comp_df.empty:
        return pd.DataFrame()

    rows = []
    for ticker in comp_df["company_id"]:
        response = requests.get(
            f"{API_URL}/market-cap/{ticker}?from_year={year}-01&to_year={year}-12"
        )
        if response.status_code == 200:
            data = response.json()
            for item in data:
                rows.append(item)
    return pd.DataFrame(rows)
