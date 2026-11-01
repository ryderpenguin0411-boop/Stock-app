import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import plotly.graph_objects as go

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

# 預設個人持股清單 (包含市場國別)
if "my_portfolio" not in st.session_state:
    st.session_state.my_portfolio = [
        {"symbol": "2330.TW", "market": "台股", "shares": 1000, "cost": 950.0},
        {"symbol": "NVDA", "market": "美股", "shares": 10, "cost": 115.0},
        {"symbol": "7203.T", "market": "日股", "shares": 100, "cost": 2800.0}
    ]

# 輔助函式：判斷股票所屬國家市場
def detect_market(symbol: str) -> str:
    sym = symbol.upper().strip()
    if sym.endswith(".TW") or sym.endswith(".TWO"):
        return "台股"
    elif sym.endswith(".T"):
        return "日股"
    else:
        return "美股"

# 輔助函式：依國家市場與漲跌回傳線圖顏色
def get_chart_color(market: str, is_up: bool) -> str:
    if market == "台股":
        # 台股：漲紅、跌綠
        return "#E53935" if is_up else "#2E7D32"
    elif market == "美股":
        # 美股：漲綠、跌紅
        return "#2E7D32" if is_up else "#E53935"
    elif market == "日股":
        # 日股：依國際慣例，漲綠、跌紅
        return "#00A86B" if is_up else "#D32F2F"
    else:
        return "#2E7D32" if is_up else "#E53935"


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

    st.markdown(f"""
    <div class="splash-container">
        <img src="{img_src}" class="splash-img" />
        <a href="?page=portfolio" target="_self" class="continue-hitbox" title="點擊進入持股庫"></a>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 頁面 2：多國持股庫與投資總覽（Portfolio Screen）
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
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

    # 頂部導覽與分析觸發按鍵
    nav_col1, nav_col2, nav_col3 = st.columns([1.5, 3.5, 2])
    with nav_col1:
        if st.button("← 返回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()
    with nav_col3:
        # 新增全局分析按鍵
        if st.button("🚀 前往行情查詢與分析", use_container_width=True):
            st.session_state.page = "dashboard"
            st.query_params["page"] = "dashboard"
            st.rerun()

    st.markdown("## 💼 全球投資持股庫")
    st.caption("依國家分類管理持股，即時掌握台股、美股與日股損益。")

    # 1. 新增股票面板
    with st.expander("➕ 新增股票到持股庫", expanded=False):
        c_sym, c_mkt, c_shares, c_cost, c_add = st.columns([2, 1.5, 2, 2, 1])
        with c_sym:
            new_sym = st.text_input("代號 (如 2330.TW / TSLA / 7203.T)", key="input_add_sym").strip().upper()
        with c_mkt:
            auto_market = detect_market(new_sym) if new_sym else "美股"
            selected_market = st.selectbox("市場國別", ["台股", "美股", "日股"], index=["台股", "美股", "日股"].index(auto_market))
        with c_shares:
            new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
        with c_cost:
            new_cost = st.number_input("買入平均成本", min_value=0.01, value=100.0, step=1.0)
        with c_add:
            st.write("")
            st.write("")
            if st.button("儲存", use_container_width=True):
                if new_sym:
                    st.session_state.my_portfolio.append({
                        "symbol": new_sym,
                        "market": selected_market,
                        "shares": new_shares,
                        "cost": new_cost
                    })
                    st.success(f"已成功加入 [{selected_market}] {new_sym}！")
                    st.rerun()

    st.write("")

    # 2. 依國家分類分頁檢視
    tab_all, tab_tw, tab_us, tab_jp = st.tabs(["🌐 全部持股", "🇹🇼 台股部位", "🇺🇸 美股部位", "🇯🇵 日股部位"])
    
    tab_filter_map = {
        tab_all: None,
        tab_tw: "台股",
        tab_us: "美股",
        tab_jp: "日股"
    }

    for active_tab, target_filter in tab_filter_map.items():
        with active_tab:
            # 篩選持股
            filtered_items = [
                (i, item) for i, item in enumerate(st.session_state.my_portfolio)
                if target_filter is None or item.get("market") == target_filter
            ]

            if not filtered_items:
                st.info("此分類目前尚無持股部位。")
            else:
                total_market_val = 0.0
                total_cost_val = 0.0

                h1, h2, h3, h4, h5, h6 = st.columns([2, 1.2, 1.5, 1.5, 2, 2])
                h1.markdown("**代號 (市場)**")
                h2.markdown("**持有股數**")
                h3.markdown("**買入成本**")
                h4.markdown("**即時現價**")
                h5.markdown("**未實現損益**")
                h6.markdown("**操作**")
                st.divider()

                for orig_idx, item in filtered_items:
                    sym = item["symbol"]
                    mkt = item.get("market", detect_market(sym))
                    shares = item["shares"]
                    cost = item["cost"]

                    try:
                        t = yf.Ticker(sym)
                        hist = t.history(period="1d")
                        curr_price = hist["Close"].iloc[-1] if not hist.empty else cost
                    except Exception:
                        curr_price = cost

                    cost_sub = shares * cost
                    mkt_sub = shares * curr_price
                    diff = mkt_sub - cost_sub
                    diff_pct = (diff / cost_sub) * 100 if cost_sub > 0 else 0

                    total_market_val += mkt_sub
                    total_cost_val += cost_sub

                    # 損益顯示顏色（台股漲紅跌綠，美日股漲綠跌紅）
                    profit_color = get_chart_color(mkt, is_up=(diff >= 0))

                    r1, r2, r3, r4, r5, r6 = st.columns([2, 1.2, 1.5, 1.5, 2, 2])
                    r1.write(f"**{sym}** ({mkt})")
                    r2.write(f"{shares:,.0f}")
                    r3.write(f"{cost:,.2f}")
                    r4.write(f"{curr_price:,.2f}")
                    r5.markdown(f"<span style='color:{profit_color}; font-weight:bold;'>{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

                    with r6:
                        b_col1, b_col2 = st.columns([2, 1])
                        with b_col1:
                            if st.button("📊 分析", key=f"btn_an_{target_filter}_{orig_idx}", use_container_width=True):
                                st.session_state.active_ticker = sym
                                st.session_state.page = "dashboard"
                                st.query_params["page"] = "dashboard"
                                st.rerun()
                        with b_col2:
                            if st.button("🗑️", key=f"btn_del_{target_filter}_{orig_idx}"):
                                st.session_state.my_portfolio.pop(orig_idx)
                                st.rerun()

                st.divider()
                tot_diff = total_market_val - total_cost_val
                tot_pct = (tot_diff / total_cost_val) * 100 if total_cost_val > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("持股總現值", f"{total_market_val:,.2f}")
                m2.metric("投入總成本", f"{total_cost_val:,.2f}")
                m3.metric("總損益額", f"{tot_diff:+,.2f}", f"{tot_pct:+.2f}%")


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

    st.markdown("### 📊 股票行情與技術分析")

    # 代號輸入與「分析」按鍵
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        target_symbol = st.text_input(
            "輸入股票代號（台股如 2330.TW、美股如 AAPL、日股如 7203.T）：",
            value=st.session_state.active_ticker,
            key="ticker_input_field"
        )
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔍 分析", use_container_width=True, key="btn_trigger_analysis"):
            st.session_state.active_ticker = target_symbol.strip().upper()
            st.rerun()

    current_ticker = st.session_state.active_ticker
    market_type = detect_market(current_ticker)

    with st.spinner(f"正在分析 {current_ticker} ({market_type}) 數據..."):
        try:
            stock = yf.Ticker(current_ticker)
            df = stock.history(period="6mo")
            info = stock.info

            if not df.empty:
                latest_close = df["Close"].iloc[-1]
                prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close
                diff = latest_close - prev_close
                diff_pct = (diff / prev_close) * 100
                is_up = (diff >= 0)

                # 依市場取得走勢線顏色
                theme_color = get_chart_color(market_type, is_up)

                today_high = df["High"].iloc[-1]
                today_low = df["Low"].iloc[-1]
                latest_vol = df["Volume"].iloc[-1]

                company_name = info.get("shortName", current_ticker)
                st.markdown(f"## {company_name} ({current_ticker}) · <span style='font-size:1.1rem; color:#738A7A;'>{market_type}</span>", unsafe_allow_html=True)

                # 4 格數據卡片
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
                m2.metric("今日最高", f"{today_high:.2f}")
                m3.metric("今日最低", f"{today_low:.2f}")
                m4.metric("最新成交量", f"{int(latest_vol):,}")

                st.markdown("---")

                tab_chart, tab_data, tab_info = st.tabs(["📈 動態走勢圖", "📋 歷史明細", "🏢 公司概況"])

                with tab_chart:
                    period_col, _ = st.columns([1, 4])
                    with period_col:
                        period_selected = st.selectbox(
                            "走勢區間",
                            ["1mo", "3mo", "6mo", "1y"],
                            index=2
                        )
                    chart_df = stock.history(period=period_selected)

                    # 建立依市場動態變色的專業 Plotly 走勢圖
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=chart_df.index,
                        y=chart_df["Close"],
                        mode='lines',
                        name='收盤價',
                        line=dict(color=theme_color, width=2.5),
                        fill='tozeroy',
                        fillcolor=f"rgba({int(theme_color[1:3], 16)}, {int(theme_color[3:5], 16)}, {int(theme_color[5:7], 16)}, 0.08)"
                    ))

                    # 融入米色調背景
                    fig.update_layout(
                        paper_bgcolor="#F7F4EA",
                        plot_bgcolor="#F7F4EA",
                        margin=dict(l=10, r=10, t=20, b=10),
                        height=420,
                        hovermode="x unified",
                        xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                        yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with tab_data:
                    st.caption("最近 30 個交易日資料明細")
                    display_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(30).sort_index(ascending=False)
                    st.dataframe(display_df, use_container_width=True)

                with tab_info:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**所屬市場：** {market_type}")
                        st.write(f"**產業類別：** {info.get('sector', '無資料')}")
                        st.write(f"**細分行業：** {info.get('industry', '無資料')}")
                        st.write(f"**計價貨幣：** {info.get('currency', '無資料')}")
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
