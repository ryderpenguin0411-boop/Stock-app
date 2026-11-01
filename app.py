import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="股票數據整理器", layout="centered")
st.title("📈 個人股票數據整理器")

# 股票代號輸入框（預設台積電 2330.TW）
代號 = st.text_input("請輸入股票代號（台股如 2330.TW，美股如 AAPL）：", value="2330.TW")

if st.button("查詢數據"):
    with st.spinner("資料抓取中..."):
        try:
            stock = yf.Ticker(代號)
            歷史資料 = stock.history(period="1mo")

            if not 歷史資料.empty:
                最新價格 = 歷史資料["Close"].iloc[-1]
                st.metric(label=f"{代號} 最新收盤價", value=f"{最新價格:.2f}")

                st.subheader("📊 近一個月收盤走勢")
                st.line_chart(歷史資料["Close"])

                st.subheader("📋 交易數據清單")
                st.dataframe(歷史資料[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False))
            else:
                st.error("查無此代號資料，請確認輸入代號是否正確。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")
