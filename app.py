import streamlit as st
import yfinance as yf
import pandas as pd
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎頁面配置
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

if "market_rules" not in st.session_state:
    st.session_state.market_rules = {
        "台股": "漲紅跌綠",
        "美股": "漲綠跌紅",
        "日股": "漲綠跌紅"
    }

if "my_portfolio" not in st.session_state:
    st.session_state.my_portfolio = [
        {"symbol": "2330.TW", "market": "台股", "shares": 1000, "cost": 950.0},
        {"symbol": "NVDA", "market": "美股", "shares": 10, "cost": 115.0},
        {"symbol": "7203.T", "market": "日股", "shares": 100, "cost": 2800.0}
    ]

def detect_market(symbol: str) -> str:
    sym = symbol.upper().strip()
    if sym.endswith(".TW") or sym.endswith(".TWO"):
        return "台股"
    elif sym.endswith(".T"):
        return "日股"
    else:
        return "美股"

def get_market_color(market_name: str, is_up: bool) -> str:
    rule = st.session_state.market_rules.get(market_name, "漲綠跌紅")
    if rule == "漲紅跌綠":
        return "#E53935" if is_up else "#2E7D32"
    else:
        return "#2E7D32" if is_up else "#E53935"

def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


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
# 頁面 2：持股庫與總資產（Portfolio Screen）
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
        max-width: 1250px !important;
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

    nav_col1, _, nav_col3 = st.columns([1.5, 4, 2.5])
    with nav_col1:
        if st.button("← 返回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()
    with nav_col3:
        if st.button("🚀 前往個股深度分析", use_container_width=True):
            st.session_state.page = "dashboard"
            st.query_params["page"] = "dashboard"
            st.rerun()

    st.markdown("## 💼 全球投資持股庫")
    st.caption("支援多國股票分類、即時多維度損益與配置佔比。")

    with st.expander("➕ 新增股票到持股庫", expanded=False):
        c_sym, c_mkt_select, c_shares, c_cost = st.columns([2, 2, 2, 2])
        with c_sym:
            new_sym = st.text_input("股票代號 (例: 2330.TW / NVDA / 7203.T)", key="input_add_sym").strip().upper()
        with c_mkt_select:
            known_markets = list(st.session_state.market_rules.keys())
            auto_idx = known_markets.index(detect_market(new_sym)) if detect_market(new_sym) in known_markets else 0
            market_options = known_markets + ["➕ 自訂其他國家/市場..."]
            chosen_market = st.selectbox("市場國別", market_options, index=auto_idx)
        with c_shares:
            new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
        with c_cost:
            new_cost = st.number_input("買入平均成本", min_value=0.01, value=100.0, step=1.0)

        final_market = chosen_market
        if chosen_market == "➕ 自訂其他國家/市場...":
            c_custom1, c_custom2 = st.columns(2)
            with c_custom1:
                custom_name = st.text_input("輸入市場名稱 (例如：韓股、英股)", value="其他市場").strip()
                final_market = custom_name
            with c_custom2:
                custom_color_rule = st.radio("漲跌顏色偏好：", ["漲紅跌綠", "漲綠跌紅"], horizontal=True)
                st.session_state.market_rules[custom_name] = custom_color_rule

        st.write("")
        if st.button("確認加入持股庫", use_container_width=True):
            if new_sym:
                st.session_state.my_portfolio.append({
                    "symbol": new_sym,
                    "market": final_market,
                    "shares": new_shares,
                    "cost": new_cost
                })
                st.success(f"已成功加入 [{final_market}] {new_sym}！")
                st.rerun()

    st.write("")

    all_markets = sorted(list(set([item.get("market", "未分類") for item in st.session_state.my_portfolio])))
    tab_list = ["🌐 全部持股"] + [f"📍 {m}" for m in all_markets]
    tabs = st.tabs(tab_list)

    for i, current_tab in enumerate(tabs):
        with current_tab:
            target_filter = None if i == 0 else all_markets[i - 1]
            filtered_items = [
                (idx, item) for idx, item in enumerate(st.session_state.my_portfolio)
                if target_filter is None or item.get("market") == target_filter
            ]

            if not filtered_items:
                st.info("此分類目前尚無任何持股資料。")
            else:
                total_market_val = 0.0
                total_cost_val = 0.0
                today_total_change = 0.0

                h1, h2, h3, h4, h5, h6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                h1.markdown("**代號 (市場)**")
                h2.markdown("**持有股數**")
                h3.markdown("**買入成本**")
                h4.markdown("**即時現價**")
                h5.markdown("**未實現累積損益**")
                h6.markdown("**操作**")
                st.divider()

                for orig_idx, item in filtered_items:
                    sym = item["symbol"]
                    mkt = item.get("market", "未分類")
                    shares = item["shares"]
                    cost = item["cost"]

                    try:
                        t = yf.Ticker(sym)
                        hist = t.history(period="2d")
                        if not hist.empty:
                            curr_price = hist["Close"].iloc[-1]
                            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else curr_price
                        else:
                            curr_price, prev_close = cost, cost
                    except Exception:
                        curr_price, prev_close = cost, cost

                    cost_sub = shares * cost
                    mkt_sub = shares * curr_price
                    diff = mkt_sub - cost_sub
                    diff_pct = (diff / cost_sub) * 100 if cost_sub > 0 else 0

                    day_diff_sub = (curr_price - prev_close) * shares
                    today_total_change += day_diff_sub

                    total_market_val += mkt_sub
                    total_cost_val += cost_sub

                    profit_color = get_market_color(mkt, is_up=(diff >= 0))

                    r1, r2, r3, r4, r5, r6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                    r1.write(f"**{sym}** ({mkt})")
                    r2.write(f"{shares:,.0f}")
                    r3.write(f"{cost:,.2f}")
                    r4.write(f"{curr_price:,.2f}")
                    r5.markdown(f"<span style='color:{profit_color}; font-weight:bold;'>{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

                    with r6:
                        b_col1, b_col2 = st.columns([2, 1])
                        with b_col1:
                            if st.button("📊 深度分析", key=f"btn_an_{i}_{orig_idx}", use_container_width=True):
                                st.session_state.active_ticker = sym
                                st.session_state.page = "dashboard"
                                st.query_params["page"] = "dashboard"
                                st.rerun()
                        with b_col2:
                            if st.button("🗑️", key=f"btn_del_{i}_{orig_idx}"):
                                st.session_state.my_portfolio.pop(orig_idx)
                                st.rerun()

                st.divider()
                tot_diff = total_market_val - total_cost_val
                tot_pct = (tot_diff / total_cost_val) * 100 if total_cost_val > 0 else 0
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("持股總現值", f"{total_market_val:,.2f}")
                m2.metric("投入總成本", f"{total_cost_val:,.2f}")
                m3.metric("累積未實現損益", f"{tot_diff:+,.2f}", f"{tot_pct:+.2f}%")
                m4.metric("今日單日總波動", f"{today_total_change:+,.2f}")


# ==========================================
# 頁面 3：個股行情與 3D 浮現進場走勢圖（Dashboard Screen）
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
        max-width: 1250px !important;
    }
    h1, h2, h3, h4, label, p, span {
        color: #2F3E34 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
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

    /* 科技感載入動畫：微光呼吸波紋效果 */
    .premium-loader {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2.5rem 1rem;
        gap: 14px;
    }
    .pulse-ring {
        width: 48px;
        height: 48px;
        border: 3.5px solid rgba(115, 138, 122, 0.25);
        border-top-color: #2F3E34;
        border-radius: 50%;
        animation: spin 0.85s linear infinite;
    }
    .pulse-text {
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        color: #556B5D;
        animation: text-pulse 1.4s ease-in-out infinite alternate;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    @keyframes text-pulse {
        from { opacity: 0.45; }
        to { opacity: 1; }
    }

    /* 圖表外層立體景深容器：徹底消除閃爍，並賦予由後向前浮現效果 */
    .chart-3d-stage {
        perspective: 1200px;
        width: 100%;
        background-color: #F7F4EA;
        border-radius: 14px;
        overflow: hidden;
    }

    /* 華麗進場動畫：從後方深處 (scale 0.88, opacity 0, blur) 平滑推進到眼前 (scale 1.0) */
    .chart-forward-anim {
        animation: zoomForwardPop 1.1s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
        transform-origin: center center;
        will-change: transform, opacity, filter;
    }

    @keyframes zoomForwardPop {
        0% {
            opacity: 0;
            transform: scale(0.88) translateZ(-60px);
            filter: blur(8px);
        }
        50% {
            opacity: 0.85;
            filter: blur(1.5px);
        }
        100% {
            opacity: 1;
            transform: scale(1.0) translateZ(0);
            filter: blur(0px);
        }
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

    st.markdown("### 📊 股票全方位數據指標與技術分析")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        target_symbol = st.text_input(
            "輸入股票代號（例如 2330.TW、AAPL、7203.T）：",
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

    loader_placeholder = st.empty()
    loader_placeholder.markdown(f"""
        <div class="premium-loader">
            <div class="pulse-ring"></div>
            <div class="pulse-text">即時抓取 {current_ticker} ({market_type}) 數據與繪製走勢...</div>
        </div>
    """, unsafe_allow_html=True)

    try:
        stock = yf.Ticker(current_ticker)
        full_df = stock.history(period="max")
        info = stock.info
        loader_placeholder.empty()

        if not full_df.empty:
            latest_close = full_df["Close"].iloc[-1]
            prev_close = full_df["Close"].iloc[-2] if len(full_df) > 1 else latest_close
            diff = latest_close - prev_close
            diff_pct = (diff / prev_close) * 100
            is_up = (diff >= 0)
            theme_color = get_market_color(market_type, is_up)

            company_name = info.get("shortName", current_ticker)
            st.markdown(f"## {company_name} ({current_ticker}) · <span style='font-size:1.1rem; color:#738A7A;'>{market_type}</span>", unsafe_allow_html=True)

            # 8 大重點指標
            r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
            r1_c1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
            r1_c2.metric("今日最高 / 最低", f"{full_df['High'].iloc[-1]:.2f} / {full_df['Low'].iloc[-1]:.2f}")
            r1_c3.metric("52 週最高", f"{info.get('fiftyTwoWeekHigh', full_df['High'].tail(252).max()):.2f}")
            r1_c4.metric("52 週最低", f"{info.get('fiftyTwoWeekLow', full_df['Low'].tail(252).min()):.2f}")

            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
            pe_val = info.get('trailingPE', None)
            r2_c1.metric("本益比 (PE)", f"{pe_val:.2f}" if pe_val else "N/A")
            eps_val = info.get('trailingEps', None)
            r2_c2.metric("每股盈餘 (EPS)", f"{eps_val:.2f}" if eps_val else "N/A")
            div_yield = info.get('dividendYield', None)
            r2_c3.metric("現金殖利率", f"{div_yield * 100:.2f}%" if div_yield else "0.00%")
            beta_val = info.get('beta', None)
            r2_c4.metric("波動度 (Beta)", f"{beta_val:.2f}" if beta_val else "N/A")

            st.markdown("---")

            tab_chart, tab_data, tab_info = st.tabs(["📈 動態走勢與技術線", "📋 歷史明細", "🏢 公司財務與基本面"])

            with tab_chart:
                c_mode, c_tools = st.columns([3, 2])
                with c_mode:
                    preset_view = st.selectbox(
                        "預設聚焦區間（可直接在圖上縮放以看更多時間）：",
                        ["最近 1 個月", "最近 3 個月", "最近 6 個月", "最近 1 年", "最近 4 年", "上市以來全部"],
                        index=1
                    )
                with c_tools:
                    show_indicators = st.multiselect("疊加技術指標", ["20 日均線 (MA20)", "60 日季線 (MA60)", "RSI 強弱指標"], default=["20 日均線 (MA20)"])

                plot_data = full_df.copy()
                if "20 日均線 (MA20)" in show_indicators and len(plot_data) >= 20:
                    plot_data["MA20"] = plot_data["Close"].rolling(window=20).mean()
                if "60 日季線 (MA60)" in show_indicators and len(plot_data) >= 60:
                    plot_data["MA60"] = plot_data["Close"].rolling(window=60).mean()
                if "RSI 強弱指標" in show_indicators and len(plot_data) >= 14:
                    plot_data["RSI"] = compute_rsi(plot_data["Close"])

                latest_date = plot_data.index.max()
                delta_map = {
                    "最近 1 個月": timedelta(days=30),
                    "最近 3 個月": timedelta(days=90),
                    "最近 6 個月": timedelta(days=180),
                    "最近 1 年": timedelta(days=365),
                    "最近 4 年": timedelta(days=365 * 4),
                    "上市以來全部": None
                }
                init_delta = delta_map[preset_view]
                init_start = (latest_date - init_delta) if init_delta else plot_data.index.min()

                has_rsi = "RSI 強弱指標" in show_indicators and "RSI" in plot_data
                rows = 2 if has_rsi else 1
                fig = make_subplots(
                    rows=rows, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.08,
                    row_heights=[0.75, 0.25] if has_rsi else [1.0]
                )

                fig.add_trace(go.Scatter(
                    x=plot_data.index, y=plot_data["Close"], mode='lines', name='收盤價',
                    line=dict(color=theme_color, width=2.5),
                    fill='tozeroy',
                    fillcolor=f"rgba({int(theme_color[1:3], 16)}, {int(theme_color[3:5], 16)}, {int(theme_color[5:7], 16)}, 0.08)"
                ), row=1, col=1)

                if "MA20" in plot_data:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["MA20"], mode='lines', name='MA20 (月線)', line=dict(color='#E67E22', width=1.5)), row=1, col=1)
                if "MA60" in plot_data:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["MA60"], mode='lines', name='MA60 (季線)', line=dict(color='#8E44AD', width=1.5)), row=1, col=1)

                if has_rsi:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["RSI"], mode='lines', name='RSI(14)', line=dict(color='#2980B9', width=1.8)), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="#C0392B", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="#27AE60", row=2, col=1)

                fig.update_layout(
                    paper_bgcolor="#F7F4EA",
                    plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=15, b=10),
                    height=510,
                    hovermode="x unified",
                    dragmode="pan",
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="#E3DEC8",
                        color="#2F3E34",
                        range=[init_start, latest_date],
                        rangeslider=dict(
                            visible=True,
                            thickness=0.07,
                            bgcolor="#EFEADB"
                        ),
                        type="date"
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="#E3DEC8",
                        color="#2F3E34",
                        autorange=True,
                        fixedrange=False
                    )
                )

                # 套用 3D 景深前推外層容器
                st.markdown('<div class="chart-3d-stage"><div class="chart-forward-anim">', unsafe_allow_html=True)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={
                        'scrollZoom': True,
                        'displayModeBar': False,
                        'showTips': False
                    }
                )
                st.markdown('</div></div>', unsafe_allow_html=True)

                st.caption("💡 提示：在 iPad 上可用 **雙指捏合縮小** 展開歷史時間，單指左右滑動移動時間軸，或直接拖曳底部的時間滑桿。")

            with tab_data:
                st.caption("最近 30 個交易日資料明細")
                display_df = full_df[["Open", "High", "Low", "Close", "Volume"]].tail(30).sort_index(ascending=False)
                st.dataframe(display_df, use_container_width=True)

            with tab_info:
                st.markdown("#### 🏢 公司核心財務與基本面數據")
                f1, f2, f3 = st.columns(3)
                with f1:
                    st.write(f"**所屬市場：** {market_type}")
                    st.write(f"**產業類別：** {info.get('sector', '無資料')}")
                    st.write(f"**細分行業：** {info.get('industry', '無資料')}")
                    st.write(f"**計價貨幣：** {info.get('currency', '無資料')}")
                with f2:
                    market_cap = info.get("marketCap", None)
                    st.write(f"**總市值：** {market_cap:,}" if market_cap else "**總市值：** 無資料")
                    st.write(f"**股價淨值比 (PB)：** {info.get('priceToBook', 'N/A')}")
                    st.write(f"**在外流通股數：** {info.get('sharesOutstanding', 'N/A'):,}" if info.get('sharesOutstanding') else "**在外流通股數：** N/A")
                with f3:
                    st.write(f"**營業利益率：** {info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "**營業利益率：** N/A")
                    st.write(f"**毛利率：** {info.get('grossMargins', 0)*100:.2f}%" if info.get('grossMargins') else "**毛利率：** N/A")
                    st.write(f"**目標中位價：** {info.get('targetMedianPrice', 'N/A')}")

                st.markdown("#### 業務概況")
                st.write(info.get("longBusinessSummary", "暫無簡介資料。"))

        else:
            loader_placeholder.empty()
            st.error(f"查無「{current_ticker}」的行情資料，請確認股票代號是否正確。")

    except Exception as e:
        loader_placeholder.empty()
        st.error(f"讀取失敗：{e}")
