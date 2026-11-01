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

# 2. 狀態管理
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "welcome")

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "2330.TW"

# 預設個人持股清單 (代號, 股數, 買入成本)
if "my_portfolio" not in st.session_state:
    st.session_state.my_portfolio = [
        {"symbol": "2330.TW", "shares": 1000, "cost": 950.0},
        {"symbol": "NVDA", "shares": 10, "cost": 115.0}
    ]


# ==========================================
# 頁面 1：手繪封面頁（Welcome Screen）
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

    # 點擊直接跳往第 2 頁：持股總覽
    st.markdown(f"""
    <div class="splash-container">
        <img src="{img_src}" class="splash-img" />
        <a href="?page=portfolio" target="_self" class="continue-hitbox" title="點擊進入持股庫"></a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 頁面 2：個人持股庫與投資組合（Portfolio Screen）
# ==========================================
elif st.session_state.page == "portfolio":
    theme_css = """
    <style>
    #MainMenu, header, footer, div[data-testid="stDecoration"] { visibility: hidden !important; }
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
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
    }
    div[data-testid="stButton"] > button {
        background-color: #E6E0CE !important;
        color: #2F3E34 !important;
        border: 1.5px solid #738A7A !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
    }
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1.5px solid #738A7A !important;
    }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

    # 頂部列
    nav_col1, nav_col2 = st.columns([1, 6])
    with nav_col1:
        if st.button("← 返回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    st.markdown("## 💼 我的投資持股庫")
    st.caption("管理持股部位、試算即時損益，點擊即可連動行情深入分析。")

    # 1. 新增股票面板 (收合式)
    with st.expander("➕ 新增股票到持股庫", expanded=False):
        c_sym, c_shares, c_cost, c_add = st.columns([2, 2, 2, 1])
        with c_sym:
            new_sym = st.text_input("股票代號 (如 2454.TW / TSLA)", key="input_add_sym").strip().upper()
        with c_shares:
            new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
        with c_cost:
            new_cost = st.number_input("買入平均成本", min_value=0.1, value=100.0, step=1.0)
        with c_add:
            st.write("")
            st.write("")
            if st.button("儲存", use_container_width=True):
                if new_sym:
                    st.session_state.my_portfolio.append({
                        "symbol": new_sym,
                        "shares": new_shares,
                        "cost": new_cost
                    })
                    st.success(f"已成功加入 {new_sym}！")
                    st.rerun()

    st.write("")

    # 2. 持股列表與即時損益計算
    if not st.session_state.my_portfolio:
        st.info("目前持股庫還是空的，請點選上方「新增股票到持股庫」開始記錄。")
    else:
        total_market_val = 0.0
        total_cost_val = 0.0

        st.markdown("### 📋 目前持股明細")
        
        # 標題行
        h1, h2, h3, h4, h5, h6 = st.columns([2, 1.5, 1.5, 1.5, 2, 2])
        h1.markdown("**股票代號**")
        h2.markdown("**持有股數**")
        h3.markdown("**買入成本**")
        h4.markdown("**即時現價**")
        h5.markdown("**未實現損益**")
        h6.markdown("**操作**")
        st.divider()

        # 逐列列出股票
        for idx, item in enumerate(st.session_state.my_portfolio):
            sym = item["symbol"]
            shares = item["shares"]
            cost = item["cost"]

            # 抓取即時價格
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="1d")
                curr_price = hist["Close"].iloc[-1] if not hist.empty else cost
            except Exception:
                curr_price = cost

            cost_subtotal = shares * cost
            market_subtotal = shares * curr_price
            diff = market_subtotal - cost_subtotal
            diff_pct = (diff / cost_subtotal) * 100 if cost_subtotal > 0 else 0

            total_market_val += market_subtotal
            total_cost_val += cost_subtotal

            r1, r2, r3, r4, r5, r6 = st.columns([2, 1.5, 1.5, 1.5, 2, 2])
            r1.write(f"**{sym}**")
            r2.write(f"{shares:,.0f}")
            r3.write(f"{cost:,.2f}")
            r4.write(f"{curr_price:,.2f}")
            
            # 損益色彩提示
            color = "#D32F2F" if diff < 0 else "#2E7D32"
            r5.markdown(f"<span style='color:{color}; font-weight:bold;'>{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

            with r6:
                btn_col1, btn_col2 = st.columns([2, 1])
                with btn_col1:
                    # 連動到第 3 頁：分析此檔股票
                    if st.button("📊 前往分析", key=f"go_analyze_{idx}", use_container_width=True):
                        st.session_state.active_ticker = sym
                        st.session_state.page = "dashboard"
                        st.query_params["page"] = "dashboard"
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.my_portfolio.pop(idx)
                        st.rerun()

        st.divider()

        # 底部總資產與總報酬概覽
        tot_diff = total_market_val - total_cost_val
        tot_pct = (tot_diff / total_cost_val) * 100 if total_cost_val > 0 else 0
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("持股總市值", f"{total_market_val:,.2f}")
        m_col2.metric("總投入成本", f"{total_cost_val:,.2f}")
        m_col3.metric("總未實現損益", f"{tot_diff:+,.2f}", f"{tot_pct:+.2f}%")


# ==========================================
# 頁面 3：深入行情與技術分析（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    dash_css = """
    <style>
    #MainMenu, header, footer, div[data-testid="stDecoration"] { visibility: hidden !important; }
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
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
    }
    div[data-testid="stButton"] > button {
        background-color: #E6E0CE !important;
        color: #2F3E34 !important;
        border: 1.5px solid #738A7A !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
    }
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1.5px solid #738A7A !important;
    }
    </style>
    """
    st.markdown(dash_css, unsafe_allow_html=True)

    # 頂部切換按鈕（可回持股庫或回封面）
    col_nav1, col_nav2, _ = st.columns([1.5, 1.5, 5])
    with col_nav1:
        if st.button("← 回持股庫"):
            st.session_state.page = "portfolio"
            st.query_params["page"] = "portfolio"
            st.rerun()
    with col_nav2:
        if st.button("🏠 回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    st.markdown("### 📊 股票行情與分析")

    # 搜尋與自選切換
    col_search_input, col_search_btn = st.columns([4, 1])
    with col_search_input:
        target_symbol = st.text_input(
            "請輸入欲查詢之股票代號：",
            value=st.session_state.active_ticker,
            key="ticker_input_field"
        )
    with col_search_btn:
        st.write("")
        st.write("")
        if st.button("🔍 分析", use_container_width=True, key="btn_trigger_analysis"):
            st.session_state.active_ticker = target_symbol.strip().upper()
            st.rerun()

    current_ticker = st.session_state.active_ticker

    # 載入詳細資訊
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

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
                m2.metric("今日最高", f"{today_high:.2f}")
                m3.metric("今日最低", f"{today_low:.2f}")
                m4.metric("最新成交量", f"{int(latest_vol):,}")

                st.markdown("---")

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
