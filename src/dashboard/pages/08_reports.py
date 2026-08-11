import pandas as pd
import requests
import streamlit as st
from utils.db import get_companies, get_connection

st.title("📋 Annual Reports")

# Load all companies
df_companies = get_companies()


@st.cache_data(ttl=86400)
def check_report_status(url):
    """
    Checks if the annual report URL is active or returns 404/error.
    Uses headers to prevent blocking by server security rules.
    Caches results for 24 hours to keep page loads fast.
    """
    if not url or not url.startswith("http"):
        return False
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        # Send a HEAD request with a short timeout to prevent UI lag
        res = requests.head(url, headers=headers, timeout=1.5, allow_redirects=True)
        if res.status_code == 404:
            return False
        # If HEAD fails or is not allowed, try a streaming GET (first few bytes)
        if res.status_code >= 400:
            res_get = requests.get(url, headers=headers, timeout=1.5, stream=True)
            if res_get.status_code == 404:
                return False
        return True
    except Exception:
        # If connection errors or timeouts happen, treat as unavailable
        return False


if df_companies.empty:
    st.error("No companies found in the database.")
else:
    # Autocomplete company search
    company_options = [
        f"{row['company_id']} - {row['company_name']}"
        for _, row in df_companies.iterrows()
    ]

    selected_option = st.selectbox(
        "Search Company for Annual Reports",
        options=[""] + company_options,
        index=0,
        placeholder="Type company name or ticker...",
    )

    if selected_option == "":
        st.info("Please select a company to view available annual reports.")
    else:
        ticker = selected_option.split(" - ")[0]

        st.markdown("---")

        # Query documents from the database
        conn = get_connection()
        query_docs = f"SELECT year, annual_report FROM documents WHERE company_id = '{ticker}' ORDER BY year DESC"
        df_docs = pd.read_sql(query_docs, conn)
        conn.close()

        if df_docs.empty:
            st.warning("No annual reports registered in the database for this company.")
        else:
            st.markdown(f"### Available Annual Reports for `{ticker}`")
            st.markdown(
                "We verify the availability of these BSE annual report PDF links dynamically."
            )

            # Iterate and display links
            for idx, row in df_docs.iterrows():
                year = row["year"]
                url = row["annual_report"]

                # Check status
                is_available = check_report_status(url)

                # Display layout
                col_yr, col_status, col_btn = st.columns([1, 1.5, 3])

                col_yr.markdown(f"**FY {year}**")

                if is_available:
                    col_status.markdown("🟢 **Active Report**")
                    col_btn.markdown(f"[📥 Download PDF Link]({url})")
                else:
                    col_status.markdown(
                        "🔴 <span style='color: #EF4444; font-weight: bold; background-color: #FEE2E2; padding: 2px 6px; border-radius: 4px;'>Report unavailable</span>",
                        unsafe_allow_html=True,
                    )
                    # Show disabled visual or text
                    col_btn.markdown("~~Download PDF Link~~ (URL Broken)")

                st.markdown(
                    "<hr style='margin: 8px 0; border: 0.5px solid #E5E7EB;' />",
                    unsafe_allow_html=True,
                )
