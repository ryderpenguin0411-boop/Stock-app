import streamlit as st
import yfinance as yf
import pandas as pd
import base64

# 1. 頁面基礎設置
st.set_page_config(
    page_title="Stock + Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 透過 URL 參數與 session_state 雙重判定當前頁面，防止點擊失效
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "welcome")

if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "2330.TW"


# ==========================================
# 頁面 A：全螢幕滿版封面頁（可直接點擊 CONTINUE）
# ==========================================
if st.session_state.page == "welcome":
    # 讀取圖片轉為 Base64
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
        background-color: #f7f4ea !important;
        overflow: hidden !important;
    }}
    .block-container {{
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
        height: 100vh !important;
    }}
    /* 滿版圖片置中容器 */
    .splash-container {{
        position: relative;
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f7f4ea;
    }}
    .splash-img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        display: block;
    }}
    /* 覆蓋在 CONTINUE 上的原生連結按鈕，保證 iPad 觸控 100% 觸發 */
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

    # 渲染滿版背景與精準疊加的 HTML 觸控按鈕
    st.markdown(f"""
    <div class="splash-container">
        <img src="{img_src}" class="splash-img" />
        <a href="?page=dashboard" target="_self" class="continue-hitbox" title="點擊進入看盤系統"></a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 頁面 B：看盤主看板（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    dash_css = """
    <style>
    #MainMenu, header, footer { visibility: hidden !important; }
    .stApp {
        background-color: #0e1117 !important;
    }
    .block-container {
        padding: 2rem 2.5rem !important;
        max-width: 1300px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1e222d;
        padding: 12px 18px;
        border-radius: 12px;
        border: 1px solid #2a2e39;
    }
    </style>
    """
    st.markdown(dash_css, unsafe_allow_html=True)

    # 頂部返回封面按鈕（點擊回到首頁）
    top_col1, top_col2 = st.columns([1, 5])
    with top_col1:
        if st.button("← 返回封面", key="btn_back"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    st.markdown("### 📊 市場看板")

    # 常用自選股與搜尋欄
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

    # 載入股票數據
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

            # 4 格指標卡片
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
            m2.metric("今日最高", f"{today_high:.2f}")
            m3.metric("今日最低", f"{today_low:.2f}")
            m4.metric("最新成交量", f"{int(latest_vol):,}")

            st.markdown("---")

            # 分頁
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
            st.error(f"查無 {target_symbol} 的交易數據。")

    except Exception as e:
        st.error(f"數據載入失敗：{e}")
