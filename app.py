import streamlit as st
import yfinance as yf
import pandas as pd
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

# 2. 狀態管理
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "welcome")

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "2330.TW"

# 自訂市場顏色規則庫（預設內建市場規則）
if "market_rules" not in st.session_state:
    st.session_state.market_rules = {
        "台股": "漲紅跌綠",
        "美股": "漲綠跌紅",
        "日股": "漲綠跌紅"
    }

# 預設個人持股清單
if "my_portfolio" not in st.session_state:
    st.session_state.my_portfolio = [
        {"symbol": "2330.TW", "market": "台股", "shares": 1000, "cost": 950.0},
        {"symbol": "NVDA", "market": "美股", "shares": 10, "cost": 115.0},
        {"symbol": "7203.T", "market": "日股", "shares": 100, "cost": 2800.0}
    ]

# 輔助函式：自動判斷預設市場
def detect_market(symbol: str) -> str:
    sym = symbol.upper().strip()
    if sym.endswith(".TW") or sym.endswith(".TWO"):
        return "台股"
    elif sym.endswith(".T"):
        return "日股"
    else:
        return "美股"

# 輔助函式：依市場規則取得漲跌顏色
def get_market_color(market_name: str, is_up: bool) -> str:
    rule = st.session_state.market_rules.get(market_name, "漲綠跌紅")
    if rule == "漲紅跌綠":
        return "#E53935" if is_up else "#2E7D32"  # 紅漲綠跌
    else:
        return "#2E7D32" if is_up else "#E53935"  # 綠漲紅跌


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
# 頁面 2：全球多元持股庫（支援自訂任意國家）
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

    # 頂部操作按鈕
    nav_col1, _, nav_col3 = st.columns([1.5, 4, 2.5])
    with nav_col1:
        if st.button("← 返回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()
    with nav_col3:
        if st.button("🚀 前往行情查詢與分析", use_container_width=True):
            st.session_state.page = "dashboard"
            st.query_params["page"] = "dashboard"
            st.rerun()

    st.markdown("## 💼 全球投資持股庫")
    st.caption("支援自訂多國股票與漲跌配色習慣，點擊「📊 分析」無縫切換走勢。")

    # 1. 新增股票面板（含自訂市場國別）
    with st.expander("➕ 新增股票到持股庫", expanded=False):
        c_sym, c_mkt_select, c_shares, c_cost = st.columns([2, 2, 2, 2])
        
        with c_sym:
            new_sym = st.text_input("股票代號 (例: 2330.TW / NVDA / 005930.KS)", key="input_add_sym").strip().upper()
        
        with c_mkt_select:
            known_markets = list(st.session_state.market_rules.keys())
            auto_idx = known_markets.index(detect_market(new_sym)) if detect_market(new_sym) in known_markets else 0
            market_options = known_markets + ["➕ 自訂其他國家/市場..."]
            chosen_market = st.selectbox("市場國別", market_options, index=auto_idx)
            
        with c_shares:
            new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
        with c_cost:
            new_cost = st.number_input("買入平均成本", min_value=0.01, value=100.0, step=1.0)

        # 若使用者勾選了自訂國家
        final_market = chosen_market
        if chosen_market == "➕ 自訂其他國家/市場...":
            c_custom1, c_custom2 = st.columns(2)
            with c_custom1:
                custom_name = st.text_input("輸入國家 / 市場名稱 (例如：韓股、英股、港股)", value="其他市場").strip()
                final_market = custom_name
            with c_custom2:
                custom_color_rule = st.radio("該市場漲跌顏色偏好：", ["漲紅跌綠", "漲綠跌紅"], horizontal=True)
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

    # 2. 自動收集所有持股庫出現過的國家分類
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
                    mkt = item.get("market", "未分類")
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

                    # 取得該市場的專屬顏色
                    profit_color = get_market_color(mkt, is_up=(diff >= 0))

                    r1, r2, r3, r4, r5, r6 = st.columns([2, 1.2, 1.5, 1.5, 2, 2])
                    r1.write(f"**{sym}** ({mkt})")
                    r2.write(f"{shares:,.0f}")
                    r3.write(f"{cost:,.2f}")
                    r4.write(f"{curr_price:,.2f}")
                    r5.markdown(f"<span style='color:{profit_color}; font-weight:bold;'>{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

                    with r6:
                        b_col1, b_col2 = st.columns([2, 1])
                        with b_col1:
                            if st.button("📊 分析", key=f"btn_an_{i}_{orig_idx}", use_container_width=True):
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
                
                m1, m2, m3 = st.columns(3)
                m1.metric("持股總現值", f"{total_market_val:,.2f}")
                m2.metric("投入總成本", f"{total_cost_val:,.2f}")
                m3.metric("總損益額", f"{tot_diff:+,.2f}", f"{tot_pct:+.2f}%")


# ==========================================
# 頁面 3：深入行情與技術分析（自由時間區間折線圖）
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
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
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

    # 代號搜尋與分析按鍵
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        target_symbol = st.text_input(
            "輸入股票代號（例如 2330.TW、AAPL、7203.T、005930.KS）：",
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
            df_snapshot = stock.history(period="5d")
            info = stock.info

            if not df_snapshot.empty:
                latest_close = df_snapshot["Close"].iloc[-1]
                prev_close = df_snapshot["Close"].iloc[-2] if len(df_snapshot) > 1 else latest_close
                diff = latest_close - prev_close
                diff_pct = (diff / prev_close) * 100
                is_up = (diff >= 0)

                # 依市場規則自動取得漲跌線條色彩
                theme_color = get_market_color(market_type, is_up)

                company_name = info.get("shortName", current_ticker)
                st.markdown(f"## {company_name} ({current_ticker}) · <span style='font-size:1.1rem; color:#738A7A;'>{market_type}</span>", unsafe_allow_html=True)

                # 4 格數據指標卡片
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("最新收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
                m2.metric("今日最高", f"{df_snapshot['High'].iloc[-1]:.2f}")
                m3.metric("今日最低", f"{df_snapshot['Low'].iloc[-1]:.2f}")
                m4.metric("最新成交量", f"{int(df_snapshot['Volume'].iloc[-1]):,}")

                st.markdown("---")

                tab_chart, tab_data, tab_info = st.tabs(["📈 動態走勢圖", "📋 歷史明細", "🏢 公司概況"])

                with tab_chart:
                    # 自由輸入 / 選擇時間區間
                    st.write("**選擇走勢圖時間區間：**")
                    time_mode = st.radio("區間模式", ["快速選擇常用時間", "自訂任意起訖日期"], horizontal=True, label_visibility="collapsed")
                    
                    chart_df = pd.DataFrame()

                    if time_mode == "快速選擇常用時間":
                        period_opts = {
                            "1 天 (1d)": "1d",
                            "1 個月 (1mo)": "1mo",
                            "2 個月 (2mo)": "2mo",
                            "3 個月 (3mo)": "3mo",
                            "4 年 (4y)": "4y",
                            "上市以來全部 (Max)": "max"
                        }
                        selected_label = st.selectbox("選擇區間", list(period_opts.keys()), index=3)
                        p_val = period_opts[selected_label]
                        interval_val = "5m" if p_val == "1d" else "1d"
                        chart_df = stock.history(period=p_val, interval=interval_val)

                    else:
                        c_start, c_end = st.columns(2)
                        with c_start:
                            start_date = st.date_input("開始日期", datetime.now() - timedelta(days=60))
                        with c_end:
                            end_date = st.date_input("結束日期", datetime.now())

                        if start_date < end_date:
                            chart_df = stock.history(start=start_date.strftime("%Y-%m-%d"), end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"))
                        else:
                            st.error("開始日期必須早於結束日期！")

                    # 繪製 Plotly 折線走勢圖
                    if not chart_df.empty:
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

                        fig.update_layout(
                            paper_bgcolor="#F7F4EA",
                            plot_bgcolor="#F7F4EA",
                            margin=dict(l=10, r=10, t=20, b=10),
                            height=430,
                            hovermode="x unified",
                            xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                            yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34")
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("此時間區間內查無交易數據。")

                with tab_data:
                    st.caption("最近 30 個交易日資料明細")
                    df_all = stock.history(period="2mo")
                    display_df = df_all[["Open", "High", "Low", "Close", "Volume"]].tail(30).sort_index(ascending=False)
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
