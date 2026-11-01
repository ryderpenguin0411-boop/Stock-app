import subprocess
import sys

# 如果找不到 yfinance，就強制讓系統自動安裝
try:
    import yfinance as yf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="股票數據整理器", layout="centered")
st.title("📈 個人股票數據整理器")

ticker_symbol = st.text_input("請輸入股票代號（台股如 2330.TW，美股如 AAPL）：", value="2330.TW")

if st.button("查詢數據"):
    with st.spinner("資料抓取中..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            history_data = stock.history(period="1mo")

            if not history_data.empty:
                latest_price = history_data["Close"].iloc[-1]
                st.metric(label=f"{ticker_symbol} 最新收盤價", value=f"{latest_price:.2f}")

                st.subheader("📊 近一個月收盤走勢")
                st.line_chart(history_data["Close"])

                st.subheader("📋 交易數據清單")
                st.dataframe(history_data[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False))
            else:
                st.error("查無此代號資料，請確認輸入代號是否正確。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")
