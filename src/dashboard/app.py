import streamlit as st

# Set Streamlit page config
st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Welcome Page Content
st.markdown("""
    <style>
        .main-header {
            font-size: 40px;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 5px;
        }
        .sub-header {
            font-size: 20px;
            color: #4B5563;
            margin-bottom: 25px;
        }
        .card {
            background-color: #F3F4F6;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1E3A8A;
            margin-bottom: 15px;
        }
        .card-title {
            font-weight: 600;
            color: #111827;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .card-text {
            color: #374151;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Nifty 100 Financial Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Premium Corporate Valuation & Analytics Dashboard</div>', unsafe_allow_html=True)

st.markdown("""
Welcome to the Nifty 100 Analytics dashboard. This platform provides institutional-grade tools to filter, compare, and analyze the financial health of the top 92 non-financial and financial companies listed on the NSE.

### Please select a screen from the sidebar to begin:
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">📊 01 Home / Overview</div>
        <div class="card-text">Overall market KPIs (Average ROE, Median P/E), sector breakdown donut charts, and top-5 quality stocks.</div>
    </div>
    <div class="card">
        <div class="card-title">🏢 02 Company Profile</div>
        <div class="card-text">Search for any company to view its detailed about card, latest KPIs, 10-year P&L growth, dual-axis ROE/ROCE charts, and pros/cons checklist.</div>
    </div>
    <div class="card">
        <div class="card-title">🔍 03 Financial Screener</div>
        <div class="card-text">Filter Nifty 100 companies using 10 custom metrics and sliders. Use preset configurations (Quality, Value, Growth) and export results to CSV.</div>
    </div>
    <div class="card">
        <div class="card-title">👥 04 Peer Comparison</div>
        <div class="card-text">Select peer groups and analyze how a company stack up against the group average via radar charts and tabular comparisons.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">📈 05 Trend Analysis</div>
        <div class="card-text">Plot and compare historical 10-year metrics side-by-side with YoY growth rates and indicators.</div>
    </div>
    <div class="card">
        <div class="card-title">🍕 06 Sector Analysis</div>
        <div class="card-text">Interactive bubble chart showing ROE vs Revenue (bubble sized by Market Cap) and median sub-sector KPIs.</div>
    </div>
    <div class="card">
        <div class="card-title">🌳 07 Capital Allocation Map</div>
        <div class="card-text">Interactive treemap of Nifty 100 companies categorized into 8 cash flow allocation patterns.</div>
    </div>
    <div class="card">
        <div class="card-title">📋 08 Annual Reports</div>
        <div class="card-text">Access annual report PDF links from BSE with automatic validation of link status.</div>
    </div>
    """, unsafe_allow_html=True)
