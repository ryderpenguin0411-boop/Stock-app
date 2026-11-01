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

# 2. 移除網頁預設雜訊
base_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding: 0rem;
        max-width: 100%;
    }
    div[data-testid="stMetric"] {
        background-color: #1e222d;
        padding: 12px 18px;
        border-radius: 12px;
        border: 1px solid #2a2e39;
    }
    </style>
"""
st.markdown(base_style, unsafe_allow_html=True)

# 3. 狀態管理
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "2330.TW"


# ==========================================
# 頁面 A：歡迎封面頁（點擊圖片上的 CONTINUE）
# ==========================================
if st.session_state.page == "welcome":
    # 讀取圖片並轉為 base64 編碼，確保圖片與按鈕能精準重疊
    try:
        with open("IMG_0865.jpeg", "rb") as img_file:
            encoded_img = base64.b64encode(img_file.read()).decode()
        img_src = f"data:image/jpeg;base64,{encoded_img}"
    except Exception:
        img_src = ""

    # 使用 CSS 將透明按鈕精準定位在圖片的 CONTINUE 方框位置
    overlay_css = f"""
    <style>
    .welcome-container {{
        position: relative;
        width: 100%;
        max-width: 950px;
        margin: 0 auto;
    }}
    .welcome-bg {{
        width: 100%;
        display: block;
        border-radius: 12px;
    }}
    /* 將 Streamlit 按鈕定位並完全覆蓋於圖片中央的 CONTINUE 方框 */
    div[data-testid="stButton"].overlay-btn {{
        position: absolute;
        top: 71.5%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 24%;
        height: 6%;
        z-index: 10;
    }}
    div[data-testid="stButton"].overlay-btn > button {{
        width: 100%;
        height: 100%;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        cursor: pointer;
        box-shadow: none !important;
    }}
    /* 點擊時的微反饋外框 */
    div[data-testid="stButton"].overlay-btn > button:active {{
        border: 1px dashed #666 !important;
    }}
    </style>
    """
    st.markdown(overlay_css, unsafe_allow_html=True)

    # 渲染包裝容器與透明觸控按鈕
    st.markdown(f'''
        <div class="welcome-container">
            <img src="{img_src}" class="welcome-bg" />
        </div>
    ''', unsafe_allow_html=True)

    # 放置透明按鈕（套用 overlay-btn 樣式）
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        # 標記按鈕外層容器
        st.markdown('<div class="overlay-btn">', unsafe_allow_html=True)
        if st.button(" ", key="hidden_continue_btn"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 頁面 B：看盤主看板（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    st.markdown('<div style="padding: 1.5rem 2rem;">', unsafe_allow_html=True)
    
    top_col1, top_col2 = st.columns([1, 6])
    with top_col1:
        if st.button("← 返回封面", key="btn_back"):
            st.session_state.page = "welcome"
            st.rerun()

    st.markdown("### 📊 市場看板")

    # 自選股列
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

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
            m2.metric("今日最高", f"{today_high:.2f}")
            m3.metric("今日最低", f"{today_low:.2f}")
            m4.metric("最新成交量", f"{int(latest_vol):,}")

            st.markdown("---")

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

    st.markdown('</div>', unsafe_allow_html=True)
