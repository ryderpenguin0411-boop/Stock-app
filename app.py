import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. 基礎頁面配置
st.set_page_config(
    page_title="Stock + Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 全域防閃爍樣式
st.markdown("""
<style>
:root, html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .stApp {
    background-color: #F7F4EA !important;
    background: #F7F4EA !important;
}
#MainMenu, header, footer, div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}
* {
    -webkit-tap-highlight-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# 3. 檔案常數設定（必須放在 load_portfolio_data 之前）
DATA_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"

# 4. 本地資料持久化存取函式
def load_portfolio_data():
    default_data = [
        {"symbol": "2330.TW", "market": "台股", "shares": 100, "cost": 950.0, "stop_loss": -10.0, "take_profit": 20.0},
        {"symbol": "NVDA", "market": "美股", "shares": 25, "cost": 115.0, "stop_loss": -15.0, "take_profit": 30.0},
        {"symbol": "7203.T", "market": "日股", "shares": 300, "cost": 2800.0, "stop_loss": -10.0, "take_profit": 20.0}
    ]
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data
