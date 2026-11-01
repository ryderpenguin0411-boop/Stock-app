import streamlit as st
import yfinance as yf
import pandas as pd
import base64

# 1. 基礎頁面配置
st.set_page_config(
    page_title="Stock + Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 頁面切換狀態管理
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "welcome")

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "2330.TW"


# ==========================================
# 頁面 A：全螢幕歡迎封面頁
# ==========================================
if st.session_state.page == "welcome":
    try:
        with open("IMG_0865.jpeg", "rb") as img_file:
            encoded_img = base64.b64encode(img_file.read()).decode()
        img_src = f"data:image/jpeg;base64,{encoded_img}"
    except Exception:
        img_src = ""

    welcome_css = f"""
    <style>
    #MainMenu, header, footer, div[data-testid="stDecoration"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    .stApp {{
        margin: 0 !important;
        padding: 0 !important;
        background-color: #F7F4EA !important;
        overflow: hidden !important;
    }}
    .block-container {{
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
        height: 100vh !important;
    }}
    .splash-container {{
        position: relative;
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #F7F4EA;
    }}
    .splash-img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        display: block;
    }}
    .continue-hitbox {{
        position: absolute;
        top: 71.8%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 240px;
        height: 56px;
        cursor: pointer;
        z-index: 9999;
        text-decoration: none;
        background: transparent;
    }}
    .continue-hitbox:active {{
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
    }}
    </style>
    """
    st.markdown(welcome_css, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="splash-container">
        <img src="{img_src}" class="splash-img" />
        <a href="?page=dashboard" target="_self" class="continue-hitbox" title="點擊進入看盤系統"></a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 頁面 B：手繪米色系看盤看板（含「分析」按鈕）
# ==========================================
elif st.session_state.page == "dashboard":
    dash_css = """
    <style>
    #MainMenu, header, footer, div[data-testid="stDecoration"] {{
        visibility: hidden !important;
    }}
    /* 整體背景與字體顏色全套改為手繪封面同款米色系 */
    .stApp {
        background-color: #F7F4EA !important;
        color: #2F3E34 !important;
    }
    .block-container {
        padding: 2rem 2.5rem !important;
        max-width: 1200px !important;
    }
    h1, h2, h3, h4, label, p, span {
        color: #2F3E34 !important;
    }
    /* 卡片區塊：採用清爽素雅米白底配合柔和邊框 */
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #5B6B60 !important;
        font-weight: bold;
    }
    /* 按鈕樣式：手繪墨綠素雅風格 */
    div[data-testid="stButton"] > button {
        background-color: #E6E0CE !important;
        color: #2F3E34 !important;
        border: 1.5px solid #738A7A !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: 0.2s all !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
        border-color: #2F3E34 !important;
    }
    /* 輸入框風格自訂 */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1.5px solid #738A7A !important;
    }
    </style>
    """
    st.markdown(dash_css, unsafe_allow_html=True)

    # 頂部導覽列
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← 返回封面", key="btn_back"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    st.markdown("### 📊 股票行情與分析")

    # 快捷自選按鈕區
    st.caption("⚡ 常用自選股")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("台積電 2330", use_container_width=True):
        st.session_state.active_ticker = "2330.TW"
        st.rerun()
    if b2.button("鴻海 2317", use_container_width=True):
        st.session_state.active_ticker = "2317.TW"
        st.rerun()
    if b3.button("輝達 NVDA", use_container_width=True):
        st.session_state.active_ticker = "NVDA"
        st.rerun()
    if b4.button("蘋果 AAPL", use_container_width=True):
        st.session_state.active_ticker = "AAPL"
        st.rerun()

    st.write("")

    # 股票代號輸入框 + 「分析」按鈕
    col_search_input, col_search_btn = st.columns([4, 1])
    with col_search_input:
        target_symbol = st.text_input(
            "請輸入欲查詢之股票代號（台股如 2330.TW，美股如 AAPL）：",
            value=st.session_state.active_ticker,
            key="ticker_input_field"
        )
    with col_search_btn:
        st.write("")
        st.write("")  # 垂直對齊按鈕
        start_analyze = st.button("🔍 分析", use_container_width=True, key="btn_trigger_analysis")

    # 當點擊「分析」或變更目標時更新股票狀態
    if start_analyze:
        st.session_state.active_ticker = target_symbol.strip()

    current_ticker = st.session_state.active_ticker

    # 載入並呈現分析資訊
    with st.spinner(f"正在分析 {current_ticker} 數據..."):
        try:
            stock = yf.Ticker(current_ticker)
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

                company_name = info.get("shortName", current_ticker)
                st.markdown(f"## {company_name} ({current_ticker})")

                # 4 格數據卡片
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
                m2.metric("今日最高", f"{today_high:.2f}")
                m3.metric("今日最低", f"{today_low:.2f}")
                m4.metric("最新成交量", f"{int(latest_vol):,}")

                st.markdown("---")

                # 分頁導覽
                tab_chart, tab_data, tab_info = st.tabs(["📈 技術走勢", "📋 歷史明細", "🏢 公司概況"])

                with tab_chart:
                    period_selected = st.selectbox(
                        "選擇走勢區間",
                        ["1mo", "3mo", "6mo", "1y"],
                        index=2
                    )
                    chart_df = stock.history(period=period_selected)
                    st.line_chart(chart_df["Close"], use_container_width=True)

                with tab_data:
                    st.caption("最近 30 個交易日資料明細")
                    display_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(30).sort_index(ascending=False)
                    st.dataframe(display_df, use_container_width=True)

                with tab_info:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**產業類別：** {info.get('sector', '無資料')}")
                        st.write(f"**細分行業：** {info.get('industry', '無資料')}")
                        st.write(f"**貨幣單位：** {info.get('currency', '無資料')}")
                    with c2:
                        market_cap = info.get("marketCap", None)
                        if market_cap:
                            st.write(f"**總市值：** {market_cap:,}")
                        pe_ratio = info.get("trailingPE", None)
                        if pe_ratio:
                            st.write(f"**本益比 (PE)：** {pe_ratio:.2f}")
                    
                    st.markdown("#### 業務概況")
                    st.write(info.get("longBusinessSummary", "暫無簡介資料。"))

            else:
                st.error(f"查無「{current_ticker}」的行情資料，請確認股票代號是否正確。")

        except Exception as e:
            st.error(f"讀取失敗：{e}")
