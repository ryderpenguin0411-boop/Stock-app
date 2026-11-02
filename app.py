import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. 基礎頁面配置（必須為第一個執行的 Streamlit 指令）
st.set_page_config(
    page_title="Stock + Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 全域防閃爍與手繪米色主題鎖定樣式
st.markdown("""
<style>
:root, html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .stApp {
    background-color: #F7F4EA !important;
    background: #F7F4EA !important;
}

#MainMenu, header, footer, div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}

* {
    -webkit-tap-highlight-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# 3. 檔案持久化常數定義（必須置於函式調用前）
DATA_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"

# 4. 本地資料持久化存取函式
def load_portfolio_data():
    default_data = [
        {"symbol": "2330.TW", "market": "台股", "shares": 100, "cost": 950.0, "stop_loss": -10.0, "take_profit": 20.0},
        {"symbol": "NVDA", "market": "美股", "shares": 25, "cost": 115.0, "stop_loss": -15.0, "take_profit": 30.0},
        {"symbol": "7203.T", "market": "日股", "shares": 300, "cost": 2800.0, "stop_loss": -10.0, "take_profit": 20.0}
    ]
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data

def save_portfolio_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"儲存持股失敗：{e}")

def load_watchlist_data():
    default_watch = ["2454.TW", "AAPL", "MSFT", "9984.T"]
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_watch
    return default_watch

def save_watchlist_data(data):
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"儲存自選名單失敗：{e}")

# 5. 狀態管理
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "welcome")

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "2330.TW"

if "chart_range_preset" not in st.session_state:
    st.session_state.chart_range_preset = "3M"

if "market_rules" not in st.session_state:
    st.session_state.market_rules = {
        "台股": "漲紅跌綠",
        "美股": "漲綠跌紅",
        "日股": "漲綠跌紅"
    }

if "my_portfolio" not in st.session_state:
    st.session_state.my_portfolio = load_portfolio_data()

if "my_watchlist" not in st.session_state:
    st.session_state.my_watchlist = load_watchlist_data()

if "show_portfolio_analyzer" not in st.session_state:
    st.session_state.show_portfolio_analyzer = False

def detect_market(symbol: str) -> str:
    sym = symbol.upper().strip()
    if sym.endswith(".TW") or sym.endswith(".TWO"):
        return "台股"
    elif sym.endswith(".T"):
        return "日股"
    else:
        return "美股"

def get_market_benchmark(market_name: str) -> tuple:
    if market_name == "台股":
        return "^TWII", "台股加權指數"
    elif market_name == "日股":
        return "^N225", "日經 225 指數"
    else:
        return "^GSPC", "標普 500 (S&P 500)"

def get_market_color(market_name: str, is_up: bool) -> str:
    rule = st.session_state.market_rules.get(market_name, "漲綠跌紅")
    if rule == "漲紅跌綠":
        return "#E53935" if is_up else "#2E7D32"
    else:
        return "#2E7D32" if is_up else "#E53935"

@st.cache_data(ttl=300)
def fetch_stock_full_data(symbol: str):
    stock = yf.Ticker(symbol)
    df = stock.history(period="max")
    info = stock.info
    news = getattr(stock, "news", [])
    return df, info, news

@st.cache_data(ttl=300)
def fetch_benchmark_data(benchmark_symbol: str, start_date):
    bm = yf.Ticker(benchmark_symbol)
    df = bm.history(start=start_date)
    return df

@st.cache_data(ttl=600)
def fetch_exchange_rates():
    rates = {"USD": 32.0, "JPY": 0.21, "TWD": 1.0}
    try:
        usdtwd = yf.Ticker("USDTWD=X").history(period="1d")
        if not usdtwd.empty:
            rates["USD"] = float(usdtwd["Close"].iloc[-1])
        jpytwd = yf.Ticker("JPYTWD=X").history(period="1d")
        if not jpytwd.empty:
            rates["JPY"] = float(jpytwd["Close"].iloc[-1])
    except Exception:
        pass
    return rates

@st.cache_data(ttl=300)
def fetch_global_indices():
    indices = [
        {"name": "台股加權", "sym": "^TWII"},
        {"name": "標普 500", "sym": "^GSPC"},
        {"name": "日經 225", "sym": "^N225"},
        {"name": "美元/台幣", "sym": "USDTWD=X"}
    ]
    results = []
    for item in indices:
        try:
            h = yf.Ticker(item["sym"]).history(period="2d")
            if len(h) >= 2:
                c = h["Close"].iloc[-1]
                p = h["Close"].iloc[-2]
                diff = c - p
                pct = (diff / p) * 100
                results.append({"name": item["name"], "price": c, "diff": diff, "pct": pct})
            elif len(h) == 1:
                results.append({"name": item["name"], "price": h["Close"].iloc[-1], "diff": 0.0, "pct": 0.0})
        except Exception:
            continue
    return results

def render_global_ticker():
    items = fetch_global_indices()
    if items:
        cols = st.columns(len(items))
        for col, it in zip(cols, items):
            color = "#E53935" if it["diff"] > 0 else ("#2E7D32" if it["diff"] < 0 else "#7F8C8D")
            with col:
                st.markdown(f"""
                <div style="background:#EFEADB; padding:5px 10px; border-radius:8px; border:1px solid #D8D2C0; text-align:center;">
                    <span style="font-size:0.75rem; color:#556B5D; font-weight:bold;">{it['name']}</span><br>
                    <span style="font-size:0.9rem; font-weight:bold; color:#2F3E34;">{it['price']:,.2f}</span>
                    <span style="font-size:0.75rem; color:{color}; font-weight:bold;">({it['pct']:+.2f}%)</span>
                </div>
                """, unsafe_allow_html=True)
        st.write("")


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

    welcome_css = """
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #F7F4EA !important;
    }
    #MainMenu, header, footer, div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
        height: 100vh !important;
    }
    .splash-container {
        position: relative;
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #F7F4EA;
    }
    .splash-img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        display: block;
    }
    .continue-hitbox {
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
    }
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
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #F7F4EA !important;
        color: #2F3E34 !important;
    }
    #MainMenu, header, footer, div[data-testid="stDecoration"] { visibility: hidden !important; }
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 1350px !important;
    }
    h1, h2, h3, h4, label, p, span {
        color: #2F3E34 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 10px !important;
        padding: 8px 14px !important;
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
    .analyzer-card {
        background-color: #EFEADB;
        border: 1.5px solid #738A7A;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .alert-tag {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .alert-profit { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
    .alert-loss { background-color: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

    render_global_ticker()
    rates = fetch_exchange_rates()

    nav_col1, nav_col2, nav_col3 = st.columns([1.5, 3.5, 3])
    with nav_col1:
        if st.button("← 返回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    with nav_col3:
        btn_text = "❌ 關閉量化試算" if st.session_state.show_portfolio_analyzer else "🧮 投資組合進階分析與加碼"
        if st.button(btn_text, use_container_width=True):
            st.session_state.show_portfolio_analyzer = not st.session_state.show_portfolio_analyzer
            st.rerun()

    st.markdown("## 💼 全球投資持股庫")

    c_curr1, c_curr2 = st.columns([3, 1.2])
    with c_curr2:
        currency_mode = st.radio("計價基準：", ["原始各國幣別", "全部折合新台幣 (TWD)"], horizontal=True)

    portfolio_data = []
    total_market_val_calc = 0.0
    total_cost_val_calc = 0.0
    today_total_change_calc = 0.0
    hist_series_dict = {}

    for item in st.session_state.my_portfolio:
        sym = item["symbol"]
        mkt = item.get("market", detect_market(sym))
        shares = item["shares"]
        cost = item["cost"]
        stop_loss = item.get("stop_loss", -10.0)
        take_profit = item.get("take_profit", 20.0)

        if mkt == "美股":
            fx_rate = rates["USD"]
            currency_symbol = "$"
        elif mkt == "日股":
            fx_rate = rates["JPY"]
            currency_symbol = "¥"
        else:
            fx_rate = 1.0
            currency_symbol = "NT$"

        try:
            df, info, _ = fetch_stock_full_data(sym)
            curr_price = df["Close"].iloc[-1] if not df.empty else cost
            prev_close = df["Close"].iloc[-2] if len(df) > 1 else curr_price
            div_yield = info.get("dividendYield", 0) or 0
            if not df.empty:
                hist_series_dict[sym] = df["Close"].tail(252) * shares * fx_rate
        except Exception:
            curr_price, prev_close = cost, cost
            div_yield = 0

        cost_sub = shares * cost
        mkt_sub = shares * curr_price
        diff = mkt_sub - cost_sub
        diff_pct = (diff / cost_sub) * 100 if cost_sub > 0 else 0
        day_diff = (curr_price - prev_close) * shares

        multiplier = fx_rate if currency_mode == "全部折合新台幣 (TWD)" else 1.0
        total_market_val_calc += (mkt_sub * multiplier)
        total_cost_val_calc += (cost_sub * multiplier)
        today_total_change_calc += (day_diff * multiplier)

        portfolio_data.append({
            "symbol": sym,
            "market": mkt,
            "shares": shares,
            "cost": cost,
            "price": curr_price,
            "cost_sub": cost_sub,
            "mkt_sub": mkt_sub,
            "diff": diff,
            "diff_pct": diff_pct,
            "day_diff": day_diff,
            "div_yield": div_yield,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "fx_rate": fx_rate,
            "curr_sym": currency_symbol,
            "mkt_sub_twd": mkt_sub * fx_rate
        })

    if portfolio_data:
        with st.expander("📊 查看資產配置甜甜圈圖（市場與個股權重）", expanded=True):
            col_pie1, col_pie2 = st.columns(2)
            custom_colors = ['#556B5D', '#8C9A8E', '#C3B091', '#8E735B', '#4A6572', '#D99B82']
            total_twd_display = sum(p["mkt_sub_twd"] for p in portfolio_data)

            with col_pie1:
                pie_mkt_df = pd.DataFrame(portfolio_data).groupby("market")["mkt_sub_twd"].sum().reset_index()
                fig_pie_mkt = go.Figure(data=[go.Pie(
                    labels=pie_mkt_df["market"],
                    values=pie_mkt_df["mkt_sub_twd"],
                    hole=.6,
                    textinfo="label+percent",
                    textposition='inside',
                    insidetextorientation='radial',
                    textfont=dict(color="#FFFFFF", size=11),
                    marker=dict(colors=custom_colors, line=dict(color='#F7F4EA', width=2))
                )])
                fig_pie_mkt.add_annotation(
                    text=f"<b>總資產</b><br><span style='font-size:11px;'>NT${total_twd_display:,.0f}</span>",
                    x=0.5, y=0.5, font_size=12, font_color="#2F3E34", showarrow=False
                )
                fig_pie_mkt.update_layout(
                    title=dict(text="<b>🌍 市場分佈 (折合台幣)</b>", font=dict(color="#2F3E34", size=13)),
                    paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=30, b=10), height=240, showlegend=False
                )
                st.plotly_chart(fig_pie_mkt, use_container_width=True, config={'displayModeBar': False})

            with col_pie2:
                pie_sym_df = pd.DataFrame(portfolio_data)
                fig_pie_sym = go.Figure(data=[go.Pie(
                    labels=pie_sym_df["symbol"],
                    values=pie_sym_df["mkt_sub_twd"],
                    hole=.6,
                    textinfo="label+percent",
                    textposition='inside',
                    insidetextorientation='radial',
                    textfont=dict(color="#FFFFFF", size=11),
                    marker=dict(colors=custom_colors, line=dict(color='#F7F4EA', width=2))
                )])
                fig_pie_sym.add_annotation(
                    text=f"<b>{len(portfolio_data)} 檔</b><br><span style='font-size:11px;'>持股標的</span>",
                    x=0.5, y=0.5, font_size=12, font_color="#2F3E34", showarrow=False
                )
                fig_pie_sym.update_layout(
                    title=dict(text="<b>📌 個股權重配置</b>", font=dict(color="#2F3E34", size=13)),
                    paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=30, b=10), height=240, showlegend=False
                )
                st.plotly_chart(fig_pie_sym, use_container_width=True, config={'displayModeBar': False})

    if st.session_state.show_portfolio_analyzer and portfolio_data:
        st.markdown('<div class="analyzer-card">', unsafe_allow_html=True)
        tab_calc1, tab_calc2, tab_equity = st.tabs(["📊 報酬率公式分析", "💰 現有資金最佳加碼做法", "📈 組合歷史淨值成長曲線"])

        with tab_calc1:
            formula_choice = st.selectbox(
                "選擇你想套用的投資評估公式：",
                [
                    "1. 簡易投資報酬率 (ROI) - 帳面總損益",
                    "2. 年化複合增長率 (CAGR) - 每年複利成長率",
                    "3. 成本現金殖利率 (Yield on Cost, YoC) - 原始本金被動現金流",
                    "4. 夏普比率 (Sharpe Ratio) - 承擔風險的超額回報"
                ]
            )

            if "ROI" in formula_choice:
                tot_diff = total_market_val_calc - total_cost_val_calc
                tot_roi = (tot_diff / total_cost_val_calc) * 100 if total_cost_val_calc > 0 else 0
                st.write("**公式：** $\\text{ROI} = \\frac{\\text{當前總市值} - \\text{總成本}}{\\text{總成本}} \\times 100\\%$")
                st.info(f"💡 目前總持股投入成本為 **${total_cost_val_calc:,.2f}**，總市值為 **${total_market_val_calc:,.2f}**，整體帳面投資報酬率 (ROI) 為 **{tot_roi:+.2f}%**。")

            elif "CAGR" in formula_choice:
                st.write("**公式：** $\\text{CAGR} = \\left( \\frac{\\text{當前市值}}{\\text{投入成本}} \\right)^{\\frac{1}{n}} - 1$")
                years_held = st.slider("請設定持有時間（年數）：", min_value=0.5, max_value=15.0, value=2.0, step=0.5)
                if total_cost_val_calc > 0:
                    cagr_val = ((total_market_val_calc / total_cost_val_calc) ** (1.0 / years_held) - 1.0) * 100
                    st.success(f"📈 經過 {years_held} 年的複利滾動，投資組合的**年化報酬率 (CAGR) 為 {cagr_val:+.2f}% / 年**。")

            elif "YoC" in formula_choice:
                st.write("**公式：** $\\text{YoC} = \\frac{\\text{預估每股年配息}}{\\text{原始每股買入成本}} \\times 100\\%$")
                yoc_list = []
                for p in portfolio_data:
                    est_annual_div = p["price"] * p["div_yield"]
                    yoc = (est_annual_div / p["cost"] * 100) if p["cost"] > 0 else 0
                    yoc_list.append({
                        "股票代號": p["symbol"],
                        "買入成本": f"{p['curr_sym']}{p['cost']:.2f}",
                        "目前股價": f"{p['curr_sym']}{p['price']:.2f}",
                        "當前殖利率": f"{p['div_yield']*100:.2f}%",
                        "成本殖利率 (YoC)": f"{yoc:.2f}%"
                    })
                st.dataframe(pd.DataFrame(yoc_list), use_container_width=True)

            elif "Sharpe" in formula_choice:
                st.write("**公式：** $\\text{Sharpe Ratio} = \\frac{R_p - R_f}{\\sigma_p}$")
                c1, c2 = st.columns(2)
                with c1:
                    rf_rate = st.number_input("設定無風險利率 %：", value=3.5, step=0.1)
                with c2:
                    st_dev = st.number_input("預估年化波動度 %：", value=18.0, step=0.5)

                tot_diff = total_market_val_calc - total_cost_val_calc
                tot_roi = (tot_diff / total_cost_val_calc) * 100 if total_cost_val_calc > 0 else 0
                sharpe = (tot_roi - rf_rate) / st_dev if st_dev > 0 else 0
                eval_text = "表現優異！" if sharpe > 1.0 else ("表現尚可。" if sharpe > 0 else "目前收益尚未跑贏無風險資產。")
                st.metric("整體夏普比率 (Sharpe Ratio)", f"{sharpe:.2f}")
                st.caption(f"評估結論：{eval_text}")

        with tab_calc2:
            st.markdown("#### 💡 現有閒置資金最佳加碼策略")
            c_invest, c_strategy = st.columns([1, 1])
            with c_invest:
                idle_cash = st.number_input("準備投入的新資金金額 (TWD)：", min_value=100.0, value=30000.0, step=1000.0)
            with c_strategy:
                strategy = st.selectbox(
                    "選擇加碼策略：",
                    ["⚖️ 再平衡逢低加碼法", "🚀 強勢順勢加碼法", "🌐 平均分散加碼法"]
                )

            weights = {}
            if "再平衡" in strategy:
                neg_scores = {p["symbol"]: max(0.1, 100.0 - p["diff_pct"]) for p in portfolio_data}
                sum_scores = sum(neg_scores.values())
                weights = {sym: score / sum_scores for sym, score in neg_scores.items()}
            elif "強勢" in strategy:
                pos_scores = {p["symbol"]: max(0.1, 50.0 + p["diff_pct"]) for p in portfolio_data}
                sum_scores = sum(pos_scores.values())
                weights = {sym: score / sum_scores for sym, score in pos_scores.items()}
            else:
                n = len(portfolio_data)
                weights = {p["symbol"]: 1.0 / n for p in portfolio_data}

            advice_list = []
            for p in portfolio_data:
                sym = p["symbol"]
                w = weights.get(sym, 0)
                alloc_cash_twd = idle_cash * w
                alloc_cash_orig = alloc_cash_twd / p["fx_rate"]
                suggest_shares = int(alloc_cash_orig // p["price"])
                actual_spent_twd = suggest_shares * p["price"] * p["fx_rate"]

                advice_list.append({
                    "股票代號": sym,
                    "市場": p["market"],
                    "目前現價": f"{p['curr_sym']}{p['price']:.2f}",
                    "配置比例": f"{w*100:.1f}%",
                    "分配資金(台幣)": f"${alloc_cash_twd:,.0f}",
                    "建議買進股數": f"{suggest_shares:,} 股",
                    "預計支出(台幣)": f"${actual_spent_twd:,.0f}"
                })
            st.dataframe(pd.DataFrame(advice_list), use_container_width=True)

        with tab_equity:
            st.markdown("#### 📈 投資組合一年期總市值成長走勢（折合台幣）")
            if hist_series_dict:
                comb_df = pd.DataFrame(hist_series_dict).dropna()
                if not comb_df.empty:
                    comb_df["Total_Portfolio_TWD"] = comb_df.sum(axis=1)
                    eq_fig = go.Figure()
                    eq_fig.add_trace(go.Scatter(
                        x=comb_df.index, y=comb_df["Total_Portfolio_TWD"],
                        mode='lines', name='組合總市值',
                        line=dict(color='#556B5D', width=2.5),
                        fill='tozeroy', fillcolor='rgba(85, 107, 93, 0.08)'
                    ))
                    eq_fig.update_layout(
                        paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                        margin=dict(l=10, r=10, t=15, b=10), height=300,
                        hovermode="x unified", dragmode="pan",
                        xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                        yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", title="NT$ 總淨值")
                    )
                    st.plotly_chart(eq_fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown('</div>', unsafe_allow_html=True)

    c_action1, c_action2 = st.columns([1, 1])
    with c_action1:
        with st.expander("➕ 新增股票到持股庫", expanded=False):
            c_sym, c_mkt_select, c_shares, c_cost = st.columns([2, 2, 2, 2])
            with c_sym:
                new_sym = st.text_input("股票代號 (例: 2330.TW / NVDA)", key="input_add_sym").strip().upper()
            with c_mkt_select:
                known_markets = list(st.session_state.market_rules.keys())
                auto_idx = known_markets.index(detect_market(new_sym)) if detect_market(new_sym) in known_markets else 0
                chosen_market = st.selectbox("市場國別", known_markets + ["➕ 自訂市場..."], index=auto_idx)
            with c_shares:
                new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
            with c_cost:
                new_cost = st.number_input("買入平均成本", min_value=0.01, value=100.0, step=1.0)

            c_sl, c_tp = st.columns(2)
            with c_sl:
                new_sl = st.number_input("停損百分比 (%)", value=-10.0, step=1.0)
            with c_tp:
                new_tp = st.number_input("停利百分比 (%)", value=20.0, step=1.0)

            final_market = chosen_market
            if chosen_market == "➕ 自訂市場...":
                final_market = st.text_input("輸入市場名稱", value="其他市場").strip()

            if st.button("確認加入持股庫", use_container_width=True):
                if new_sym:
                    new_entry = {
                        "symbol": new_sym, "market": final_market, "shares": new_shares,
                        "cost": new_cost, "stop_loss": new_sl, "take_profit": new_tp
                    }
                    st.session_state.my_portfolio.append(new_entry)
                    save_portfolio_data(st.session_state.my_portfolio)
                    st.success(f"已加入並存檔 {new_sym}！")
                    st.rerun()

    with c_action2:
        with st.expander("👀 觀察自選名單 (Watchlist)", expanded=False):
            w_in, w_btn = st.columns([3, 1])
            with w_in:
                add_w_sym = st.text_input("輸入觀察股票代號：", key="input_watch_sym").strip().upper()
            with w_btn:
                st.write("")
                if st.button("➕ 加入", use_container_width=True):
                    if add_w_sym and add_w_sym not in st.session_state.my_watchlist:
                        st.session_state.my_watchlist.append(add_w_sym)
                        save_watchlist_data(st.session_state.my_watchlist)
                        st.rerun()

            if st.session_state.my_watchlist:
                for w_sym in st.session_state.my_watchlist:
                    wc1, wc2, wc3 = st.columns([3, 1.5, 1])
                    with wc1:
                        st.write(f"📌 **{w_sym}** ({detect_market(w_sym)})")
                    with wc2:
                        if st.button("看盤", key=f"btn_w_{w_sym}", use_container_width=True):
                            st.session_state.active_ticker = w_sym
                            st.session_state.page = "dashboard"
                            st.query_params["page"] = "dashboard"
                            st.rerun()
                    with wc3:
                        if st.button("🗑️", key=f"del_w_{w_sym}"):
                            st.session_state.my_watchlist.remove(w_sym)
                            save_watchlist_data(st.session_state.my_watchlist)
                            st.rerun()

    st.write("")

    all_markets = sorted(list(set([item.get("market", "未分類") for item in st.session_state.my_portfolio])))
    tabs = st.tabs(["🌐 全部持股"] + [f"📍 {m}" for m in all_markets])

    for i, current_tab in enumerate(tabs):
        with current_tab:
            target_filter = None if i == 0 else all_markets[i - 1]
            filtered_items = [
                (idx, item) for idx, item in enumerate(portfolio_data)
                if target_filter is None or item["market"] == target_filter
            ]

            if not filtered_items:
                st.info("此分類目前無持股資料。")
            else:
                h1, h2, h3, h4, h5, h6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                h1.markdown("**代號 (市場)**")
                h2.markdown("**持有股數**")
                h3.markdown("**成本**")
                h4.markdown("**現價**")
                h5.markdown("**未實現損益**")
                h6.markdown("**操作**")
                st.divider()

                for orig_idx, p in filtered_items:
                    sym = p["symbol"]
                    mkt = p["market"]
                    shares = p["shares"]
                    cost = p["cost"]
                    curr_price = p["price"]
                    diff = p["diff"]
                    diff_pct = p["diff_pct"]
                    curr_s = p["curr_sym"]

                    profit_color = get_market_color(mkt, is_up=(diff >= 0))
                    alert_html = ""
                    if diff_pct <= p["stop_loss"]:
                        alert_html = f" <span class='alert-tag alert-loss'>⚠️ 停損 ({diff_pct:.1f}%)</span>"
                    elif diff_pct >= p["take_profit"]:
                        alert_html = f" <span class='alert-tag alert-profit'>🎯 達標 ({diff_pct:.1f}%)</span>"

                    r1, r2, r3, r4, r5, r6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                    r1.markdown(f"**{sym}**{alert_html}", unsafe_allow_html=True)
                    r2.write(f"{shares:,.0f}")
                    r3.write(f"{curr_s}{cost:,.2f}")
                    r4.write(f"{curr_s}{curr_price:,.2f}")
                    r5.markdown(f"<span style='color:{profit_color}; font-weight:bold;'>{curr_s}{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

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
                                save_portfolio_data(st.session_state.my_portfolio)
                                st.rerun()

                st.divider()

    tot_diff = total_market_val_calc - total_cost_val_calc
    tot_pct = (tot_diff / total_cost_val_calc) * 100 if total_cost_val_calc > 0 else 0
    prefix = "NT$ " if currency_mode == "全部折合新台幣 (TWD)" else ""

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("持股總現值", f"{prefix}{total_market_val_calc:,.2f}")
    m2.metric("投入總成本", f"{prefix}{total_cost_val_calc:,.2f}")
    m3.metric("累積未實現損益", f"{prefix}{tot_diff:+,.2f}", f"{tot_pct:+.2f}%")
    m4.metric("今日單日波動", f"{prefix}{today_total_change_calc:+,.2f}")

    if portfolio_data:
        with st.expander("📥 匯出持股資料報表 (CSV)", expanded=False):
            csv_df = pd.DataFrame(portfolio_data)[[
                "symbol", "market", "shares", "cost", "price", "diff", "diff_pct"
            ]]
            csv_df.columns = ["股票代號", "市場", "持有股數", "買入成本", "即時現價", "累積損益", "報酬率(%)"]
            csv_data = csv_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="確認下載 CSV 檔案",
                data=csv_data,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


# ==========================================
# 頁面 3：iPad 專業雙欄分屏看盤（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    dash_css = """
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #F7F4EA !important;
        color: #2F3E34 !important;
    }
    #MainMenu, header, footer, div[data-testid="stDecoration"] { visibility: hidden !important; }
    .block-container {
        padding: 1rem 1.8rem !important;
        max-width: 1400px !important;
    }
    h1, h2, h3, h4, label, p, span {
        color: #2F3E34 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #EFEADB !important;
        border: 1px solid #D8D2C0 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
    div[data-testid="stButton"] > button {
        background-color: #E6E0CE !important;
        color: #2F3E34 !important;
        border: 1.5px solid #738A7A !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
    }
    .plotly-touch-stage {
        touch-action: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }
    </style>
    """
    st.markdown(dash_css, unsafe_allow_html=True)

    render_global_ticker()

    c_n1, c_n2, _ = st.columns([1.5, 1.5, 6])
    with c_n1:
        if st.button("← 回持股庫"):
            st.session_state.page = "portfolio"
            st.query_params["page"] = "portfolio"
            st.rerun()
    with c_n2:
        if st.button("🏠 回封面"):
            st.session_state.page = "welcome"
            st.query_params["page"] = "welcome"
            st.rerun()

    col_left, col_right = st.columns([1.1, 2.5])

    with col_left:
        st.markdown("#### 🔍 快捷切換股票")
        in_sym = st.text_input("輸入股票代號：", value=st.session_state.active_ticker, key="search_left_sym")
        if st.button("確定搜尋", use_container_width=True):
            st.session_state.active_ticker = in_sym.strip().upper()
            st.rerun()

        st.markdown("---")
        st.markdown("**💼 我的持股部位**")
        for item in st.session_state.my_portfolio:
            s = item["symbol"]
            is_active = (s == st.session_state.active_ticker)
            label = f"👉 {s}" if is_active else f"• {s}"
            if st.button(label, key=f"sel_port_{s}", use_container_width=True):
                st.session_state.active_ticker = s
                st.rerun()

        st.markdown("**👀 觀察自選名單**")
        for s in st.session_state.my_watchlist:
            is_active = (s == st.session_state.active_ticker)
            label = f"👉 {s}" if is_active else f"• {s}"
            if st.button(label, key=f"sel_watch_{s}", use_container_width=True):
                st.session_state.active_ticker = s
                st.rerun()

    with col_right:
        current_ticker = st.session_state.active_ticker
        market_type = detect_market(current_ticker)

        try:
            full_df, info, news_items = fetch_stock_full_data(current_ticker)

            if not full_df.empty:
                latest_close = full_df["Close"].iloc[-1]
                prev_close = full_df["Close"].iloc[-2] if len(full_df) > 1 else latest_close
                diff = latest_close - prev_close
                diff_pct = (diff / prev_close) * 100
                is_up = (diff >= 0)
                theme_color = get_market_color(market_type, is_up)
                company_name = info.get("shortName", current_ticker)

                st.markdown(f"### {company_name} ({current_ticker}) · <span style='font-size:1rem; color:#738A7A;'>{market_type}</span>", unsafe_allow_html=True)

                r1, r2, r3, r4 = st.columns(4)
                r1.metric("收盤價", f"{latest_close:.2f}", f"{diff:+.2f} ({diff_pct:+.2f}%)")
                r2.metric("52 週最高/最低", f"{info.get('fiftyTwoWeekHigh', full_df['High'].tail(252).max()):.1f} / {info.get('fiftyTwoWeekLow', full_df['Low'].tail(252).min()):.1f}")
                pe_val = info.get('trailingPE', None)
                r3.metric("本益比 (PE)", f"{pe_val:.2f}" if pe_val else "N/A")
                div_yield = info.get('dividendYield', None)
                r4.metric("殖利率", f"{div_yield * 100:.2f}%" if div_yield else "0.00%")

                tab_chart, tab_benchmark, tab_dca, tab_news, tab_info = st.tabs([
                    "📈 專業走勢圖", "🌐 大盤對比 (Alpha)", "📅 定期定額", "📰 即時新聞", "🏢 財務基本面"
                ])

                with tab_chart:
                    # 1. 時間區間按鈕組
                    st.write("**快捷時間區間：**")
                    b1, b2, b3, b4, b5, b6, b_type = st.columns([1, 1, 1, 1, 1, 1.2, 2.5])
                    with b1:
                        if st.button("1 個月", key="btn_p_1m", use_container_width=True):
                            st.session_state.chart_range_preset = "1M"
                    with b2:
                        if st.button("3 個月", key="btn_p_3m", use_container_width=True):
                            st.session_state.chart_range_preset = "3M"
                    with b3:
                        if st.button("6 個月", key="btn_p_6m", use_container_width=True):
                            st.session_state.chart_range_preset = "6M"
                    with b4:
                        if st.button("1 年", key="btn_p_1y", use_container_width=True):
                            st.session_state.chart_range_preset = "1Y"
                    with b5:
                        if st.button("4 年", key="btn_p_4y", use_container_width=True):
                            st.session_state.chart_range_preset = "4Y"
                    with b6:
                        if st.button("上市以來", key="btn_p_all", use_container_width=True):
                            st.session_state.chart_range_preset = "ALL"
                    with b_type:
                        chart_render_type = st.radio("類型：", ["平滑折線", "蠟燭 K 線"], horizontal=True)

                    # 2. 多線條與指標選單
                    show_indicators = st.multiselect(
                        "疊加技術線條與輔助指標：",
                        [
                            "MA5 (週線)",
                            "MA20 (月線)",
                            "MA60 (季線)",
                            "布林通道 (Bollinger Bands)",
                            "個人買入成本線",
                            "52 週高低價參考線"
                        ],
                        default=["MA20 (月線)", "布林通道 (Bollinger Bands)", "個人買入成本線"]
                    )

                    plot_data = full_df.copy()

                    # 計算各類均線
                    if "MA5 (週線)" in show_indicators and len(plot_data) >= 5:
                        plot_data["MA5"] = plot_data["Close"].rolling(window=5).mean()
                    if "MA20 (月線)" in show_indicators and len(plot_data) >= 20:
                        plot_data["MA20"] = plot_data["Close"].rolling(window=20).mean()
                    if "MA60 (季線)" in show_indicators and len(plot_data) >= 60:
                        plot_data["MA60"] = plot_data["Close"].rolling(window=60).mean()

                    # 計算布林通道
                    if "布林通道 (Bollinger Bands)" in show_indicators and len(plot_data) >= 20:
                        bb_ma = plot_data["Close"].rolling(window=20).mean()
                        bb_std = plot_data["Close"].rolling(window=20).std()
                        plot_data["BB_Upper"] = bb_ma + (bb_std * 2)
                        plot_data["BB_Lower"] = bb_ma - (bb_std * 2)

                    latest_date = plot_data.index.max()
                    delta_map = {
                        "1M": timedelta(days=30),
                        "3M": timedelta(days=90),
                        "6M": timedelta(days=180),
                        "1Y": timedelta(days=365),
                        "4Y": timedelta(days=365 * 4),
                        "ALL": None
                    }
                    init_delta = delta_map.get(st.session_state.chart_range_preset, timedelta(days=90))
                    init_start = (latest_date - init_delta) if init_delta else plot_data.index.min()

                    # 自適應當前時間區間高低點
                    view_df = plot_data[plot_data.index >= init_start]
                    y_min = view_df["Low"].min() * 0.95 if "Low" in view_df else view_df["Close"].min() * 0.95
                    y_max = view_df["High"].max() * 1.05 if "High" in view_df else view_df["Close"].max() * 1.05

                    fig = go.Figure()

                    # 主圖：折線或 K 線
                    if chart_render_type == "平滑折線":
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["Close"], mode='lines', name='收盤價',
                            line=dict(color=theme_color, width=2.5),
                            fill='tozeroy', fillcolor=f"rgba(115, 138, 122, 0.08)",
                            yaxis='y1'
                        ))
                    else:
                        up_c = "#E53935" if market_type == "台股" else "#2E7D32"
                        dn_c = "#2E7D32" if market_type == "台股" else "#E53935"
                        fig.add_trace(go.Candlestick(
                            x=plot_data.index,
                            open=plot_data['Open'], high=plot_data['High'],
                            low=plot_data['Low'], close=plot_data['Close'],
                            increasing_line_color=up_c, decreasing_line_color=dn_c,
                            name='K 線', yaxis='y1'
                        ))

                    # 繪製 MA5
                    if "MA5" in plot_data:
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["MA5"],
                            mode='lines', name='MA5 (週線)',
                            line=dict(color='#2980B9', width=1.5), yaxis='y1'
                        ))

                    # 繪製 MA20
                    if "MA20" in plot_data:
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["MA20"],
                            mode='lines', name='MA20 (月線)',
                            line=dict(color='#E67E22', width=1.5), yaxis='y1'
                        ))

                    # 繪製 MA60
                    if "MA60" in plot_data:
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["MA60"],
                            mode='lines', name='MA60 (季線)',
                            line=dict(color='#8E44AD', width=1.5), yaxis='y1'
                        ))

                    # 繪製布林通道（上軌與下軌，中間加半透明通道陰影）
                    if "BB_Upper" in plot_data and "BB_Lower" in plot_data:
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["BB_Upper"],
                            mode='lines', name='布林上軌',
                            line=dict(color='rgba(127, 140, 141, 0.65)', width=1, dash='dash'),
                            yaxis='y1'
                        ))
                        fig.add_trace(go.Scatter(
                            x=plot_data.index, y=plot_data["BB_Lower"],
                            mode='lines', name='布林下軌',
                            line=dict(color='rgba(127, 140, 141, 0.65)', width=1, dash='dash'),
                            fill='tonexty', fillcolor='rgba(127, 140, 141, 0.08)',
                            yaxis='y1'
                        ))

                    # 成交量副軸
                    vol_colors = [(theme_color if r["Close"] >= r["Open"] else "#9E9E9E") for _, r in plot_data.iterrows()]
                    fig.add_trace(go.Bar(
                        x=plot_data.index, y=plot_data["Volume"],
                        name="成交量", marker_color=vol_colors, opacity=0.3, yaxis='y2'
                    ))

                    # 疊加個人買入成本水平線
                    if "個人買入成本線" in show_indicators:
                        user_holding = next((item for item in st.session_state.my_portfolio if item["symbol"] == current_ticker), None)
                        if user_holding:
                            cost_val = user_holding["cost"]
                            fig.add_hline(
                                y=cost_val, line_dash="dot", line_color="#D35400", line_width=1.8,
                                annotation_text=f"持股成本: {cost_val:.2f}", annotation_position="top left",
                                annotation_font=dict(color="#D35400", size=10)
                            )

                    # 疊加 52 週高低價參考水平線
                    if "52 週高低價參考線" in show_indicators:
                        h52 = info.get('fiftyTwoWeekHigh', full_df['High'].tail(252).max())
                        l52 = info.get('fiftyTwoWeekLow', full_df['Low'].tail(252).min())
                        fig.add_hline(y=h52, line_dash="dash", line_color="#C0392B", line_width=1, annotation_text="52W 高", annotation_position="top right")
                        fig.add_hline(y=l52, line_dash="dash", line_color="#27AE60", line_width=1, annotation_text="52W 低", annotation_position="bottom right")

                    fig.update_layout(
                        paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                        margin=dict(l=5, r=10, t=10, b=10), height=480,
                        hovermode="x unified",
                        dragmode="pan",
                        xaxis=dict(
                            showgrid=True, gridcolor="#E3DEC8", color="#2F3E34",
                            range=[init_start, latest_date],
                            rangeslider=dict(visible=True, thickness=0.08, bgcolor="#EFEADB"),
                            type="date"
                        ),
                        yaxis=dict(
                            title="價格",
                            showgrid=True, gridcolor="#E3DEC8", color="#2F3E34",
                            side="right",
                            range=[y_min, y_max],
                            autorange=False,
                            fixedrange=False
                        ),
                        yaxis2=dict(
                            title="",
                            overlaying='y',
                            side='left',
                            showgrid=False,
                            showticklabels=False,
                            range=[0, plot_data["Volume"].max() * 4.5]
                        )
                    )

                    st.markdown('<div class="plotly-touch-stage">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.caption("💡 提示：點選上方標籤可疊加或關閉指標線，點擊快捷區間鈕可伸展時間軸。")

                with tab_benchmark:
                    bm_symbol, bm_name = get_market_benchmark(market_type)
                    st.markdown(f"**對比大盤基準（{bm_name}）**")
                    bm_start = datetime.now() - timedelta(days=365)
                    bm_df = fetch_benchmark_data(bm_symbol, bm_start.strftime("%Y-%m-%d"))
                    stk_bm_df = full_df[full_df.index >= pd.to_datetime(bm_start).tz_localize(full_df.index.tz)]

                    if not bm_df.empty and not stk_bm_df.empty:
                        common_idx = stk_bm_df.index.intersection(bm_df.index)
                        if len(common_idx) > 5:
                            s_close = stk_bm_df.loc[common_idx, "Close"]
                            b_close = bm_df.loc[common_idx, "Close"]
                            s_return = ((s_close / s_close.iloc[0]) - 1.0) * 100
                            b_return = ((b_close / b_close.iloc[0]) - 1.0) * 100
                            alpha = s_return.iloc[-1] - b_return.iloc[-1]

                            bm_fig = go.Figure()
                            bm_fig.add_trace(go.Scatter(x=common_idx, y=s_return, mode='lines', name=f"{current_ticker}", line=dict(color='#2E7D32' if alpha >= 0 else '#E53935', width=2.5)))
                            bm_fig.add_trace(go.Scatter(x=common_idx, y=b_return, mode='lines', name=f"{bm_name}", line=dict(color='#7F8C8D', width=2, dash='dot')))
                            bm_fig.update_layout(
                                paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                                margin=dict(l=10, r=10, t=10, b=10), height=320,
                                hovermode="x unified", dragmode="pan",
                                xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                                yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", autorange=True, side="right", title="累積報酬 (%)")
                            )
                            c1, c2, c3 = st.columns(3)
                            c1.metric(f"個股年報酬", f"{s_return.iloc[-1]:+.1f}%")
                            c2.metric(f"大盤年報酬", f"{b_return.iloc[-1]:+.1f}%")
                            c3.metric("超額 Alpha", f"{alpha:+.1f}%")
                            st.plotly_chart(bm_fig, use_container_width=True, config={'displayModeBar': False})

                with tab_dca:
                    monthly_amount = st.number_input("每月定額 ($)：", value=5000.0, step=500.0)
                    dca_start = datetime.now() - timedelta(days=2 * 365)
                    dca_df = full_df[full_df.index >= pd.to_datetime(dca_start).tz_localize(full_df.index.tz)]

                    if not dca_df.empty:
                        monthly_df = dca_df.resample('MS').first()
                        total_invested, total_shares, dca_timeline = 0.0, 0.0, []
                        for date, row in monthly_df.iterrows():
                            p = row["Close"]
                            if p > 0:
                                total_shares += (monthly_amount / p)
                                total_invested += monthly_amount
                                dca_timeline.append({"date": date, "invested": total_invested, "val": total_shares * p})

                        if dca_timeline:
                            final_val = total_shares * latest_close
                            dca_roi = ((final_val - total_invested) / total_invested) * 100 if total_invested > 0 else 0
                            dc1, dc2, dc3 = st.columns(3)
                            dc1.metric("投入本金", f"${total_invested:,.0f}")
                            dc2.metric("期末市值", f"${final_val:,.0f}")
                            dc3.metric("定額投報", f"{final_val-total_invested:+,.0f}", f"{dca_roi:+.1f}%")

                with tab_news:
                    if news_items:
                        for news in news_items[:5]:
                            st.markdown(f"• **[{news.get('title', '無標題')}]({news.get('link', '#')})**")
                    else:
                        st.info("暫無新聞。")

                with tab_info:
                    st.write(info.get("longBusinessSummary", "暫無簡介資料。"))

            else:
                st.error("查無此股票行情資料。")

        except Exception as e:
            st.error(f"讀取失敗：{e}")
