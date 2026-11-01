import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 基礎頁面配置
st.set_page_config(
    page_title="Stock + Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 移除網頁預設雜訊，美化按鈕外觀
custom_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    /* 美化 CONTINUE 按鈕，呈現簡約外框風格 */
    div[data-testid="stButton"] > button {
        border: 2px solid #555555;
        background-color: transparent;
        color: inherit;
        font-size: 1.2rem;
        letter-spacing: 2px;
        padding: 0.6rem 2rem;
        border-radius: 8px;
        transition: all 0.3s;
    }
    div[data-testid="stMetric"] {
        background-color: #1e222d;
        padding: 12px 18px;
        border-radius: 12px;
        border: 1px solid #2a2e39;
    }
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# 3. 頁面狀態管理：預設停留在歡迎封面
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# 4. 股票查詢預設代號管理
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "2330.TW"


# ==========================================
# 頁面 A：歡迎封面頁（Welcome Screen）
# ==========================================
if st.session_state.page == "welcome":
    left_pad, center_col, right_pad = st.columns([1, 4, 1])

    with center_col:
        try:
            # 讀取剛剛上傳的圖片檔案
            st.image("IMG_0865.jpeg", use_container_width=True)
        except Exception:
            st.markdown("<h1 style='text-align: center;'>Stock + Analyze</h1>", unsafe_allow_html=True)

        # 封面中央的 CONTINUE 按鈕
        if st.button("CONTINUE", use_container_width=True, key="btn_continue"):
            st.session_state.page = "dashboard"
            st.rerun()


# ==========================================
# 頁面 B：看盤主看板（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    # 頂部導覽工具列與返回封面按鈕
    top_col1, top_col2 = st.columns([1, 5])
    with top_col1:
        if st.button("← 返回封面", key="btn_back"):
            st.session_state.page = "welcome"
            st.rerun()

    st.markdown("### 📊 市場看板")

    # 快捷自選列與搜尋框
    col_quick, col_input = st.columns([2, 1])
    with col_quick:
        st.caption("⚡ 常用自選股")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("台積電 2330", use_container_width=True):
            st.session_state.current_ticker = "2330.TW"
        if b2.button("鴻海 2317", use_container_width=True):
            st.session_state.current_ticker = "2317.TW"
        if b3.button("輝達 NVDA", use_container_width=True):
            st.session_state.current_ticker = "NVDA"
        if b4.button("蘋果 AAPL", use_container_width=True):
            st.session_state.current_ticker = "AAPL"

    with col_input:
        st.caption("🔍 代號搜尋")
        user_ticker = st.text_input(
            "輸入代號",
            value=st.session_state.current_ticker,
            label_visibility="collapsed"
        )
        if user_ticker != st.session_state.current_ticker:
            st.session_state.current_ticker = user_ticker

    target_symbol = st.session_state.current_ticker

    # 載入股票資訊
    try:
        stock = yf.Ticker(target_symbol)
        df = stock.history(period="6mo")
        info = stock.info

        if not df.empty:
            latest_close = df["Close"].iloc[-1]
            prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close
            diff = latest_close - prev_close
            diff_pct = (diff / prev_close) * 100
            today_high = df["High"].iloc[-1]
            today_low = df["Low"].iloc[-1]
            latest_vol = df["Volume"].iloc[-1]

            company_name = info.get("shortName", target_symbol)
            st.markdown(f"## {company_name} ({target_symbol})")

            # 4 格指標資訊網格
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
            m2.metric("今日最高", f"{today_high:.2f}")
            m3.metric("今日最低", f"{today_low:.2f}")
            m4.metric("最新成交量", f"{int(latest_vol):,}")

            st.markdown("---")

            # 多分頁操作
            tab_chart, tab_data, tab_info = st.tabs(["📈 技術走勢", "📋 歷史明細", "🏢 公司概況"])

            with tab_chart:
                period_col1, period_col2 = st.columns([1, 4])
                with period_col1:
                    period_selected = st.selectbox(
                        "選擇區間",
                        ["1mo", "3mo", "6mo", "1y"],
                        index=2
                    )
                chart_df = stock.history(period=period_selected)
                st.line_chart(chart_df["Close"], use_container_width=True)

            with tab_data:
                st.caption("最近 30 個交易日資料")
                display_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(30).sort_index(ascending=False)
                st.dataframe(display_df, use_container_width=True)

            with tab_info:
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**產業類別：** {info.get('sector', '無資料')}")
                    st.write(f"**細分行業：** {info.get('industry', '無資料')}")
                    st.write(f"**貨幣計價：** {info.get('currency', '無資料')}")
                with c2:
                    market_cap = info.get("marketCap", None)
                    if market_cap:
                        st.write(f"**總市值：** {market_cap:,}")
                    pe_ratio = info.get("trailingPE", None)
                    if pe_ratio:
                        st.write(f"**本益比 (PE)：** {pe_ratio:.2f}")
                
                st.markdown("#### 公司業務簡介")
                st.write(info.get("longBusinessSummary", "暫無簡介資料。"))

        else:
            st.error(f"查無 {target_symbol} 的交易數據，請確認代號是否正確。")

    except Exception as e:
        st.error(f"數據載入失敗：{e}")
