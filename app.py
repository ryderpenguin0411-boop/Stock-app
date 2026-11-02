import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
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

DATA_FILE = "portfolio.json"
WATCHLIST_FILE = "watchlist.json"

# 2. 本地資料持久化存取函式
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

# 狀態管理
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

def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

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
                <div style="background:#EFEADB; padding:6px 12px; border-radius:8px; border:1px solid #D8D2C0; text-align:center;">
                    <span style="font-size:0.8rem; color:#556B5D; font-weight:bold;">{it['name']}</span><br>
                    <span style="font-size:0.95rem; font-weight:bold; color:#2F3E34;">{it['price']:,.2f}</span>
                    <span style="font-size:0.8rem; color:{color}; font-weight:bold;">({it['pct']:+.2f}%)</span>
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
        animation: pageFadeIn 0.45s ease-out forwards;
    }}
    @keyframes pageFadeIn {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
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
    /* 全域滑順進場過渡動畫 */
    .block-container {
        padding: 1.5rem 2.5rem !important;
        max-width: 1250px !important;
        animation: pageSlideFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        will-change: transform, opacity;
    }
    @keyframes pageSlideFade {
        0% {
            opacity: 0;
            transform: translateY(8px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
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
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
    }
    div[data-testid="stButton"] > button:active {
        transform: scale(0.98);
    }
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    .analyzer-card {
        background-color: #EFEADB;
        border: 1.5px solid #738A7A;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .alert-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-top: 4px;
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
        btn_text = "❌ 關閉分析與試算" if st.session_state.show_portfolio_analyzer else "🧮 投資組合進階分析與加碼"
        if st.button(btn_text, use_container_width=True):
            st.session_state.show_portfolio_analyzer = not st.session_state.show_portfolio_analyzer
            st.rerun()

    st.markdown("## 💼 全球投資持股庫")
    st.caption("支援全球即時大盤、自選名單、組合歷史淨值曲線、多幣別折算與停損利監控。")

    c_curr1, c_curr2 = st.columns([3, 1])
    with c_curr2:
        currency_mode = st.radio("計價貨幣基準", ["原始各國幣別", "全部折合新台幣 (TWD)"], horizontal=True)

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

    # 優化版甜甜圈圖
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
                    hole=.55,
                    textinfo="label+percent",
                    textfont=dict(color="#FFFFFF", size=12),
                    marker=dict(colors=custom_colors, line=dict(color='#F7F4EA', width=2))
                )])
                fig_pie_mkt.add_annotation(
                    text=f"<b>總資產</b><br><span style='font-size:11px;'>NT${total_twd_display:,.0f}</span>",
                    x=0.5, y=0.5, font_size=13, font_color="#2F3E34", showarrow=False
                )
                fig_pie_mkt.update_layout(
                    title=dict(text="<b>🌍 市場資產分佈 (折合台幣)</b>", font=dict(color="#2F3E34", size=14)),
                    paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=40, b=40), height=320,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#2F3E34", size=11))
                )
                st.plotly_chart(fig_pie_mkt, use_container_width=True, config={'displayModeBar': False})

            with col_pie2:
                pie_sym_df = pd.DataFrame(portfolio_data)
                fig_pie_sym = go.Figure(data=[go.Pie(
                    labels=pie_sym_df["symbol"],
                    values=pie_sym_df["mkt_sub_twd"],
                    hole=.55,
                    textinfo="label+percent",
                    textfont=dict(color="#FFFFFF", size=12),
                    marker=dict(colors=custom_colors, line=dict(color='#F7F4EA', width=2))
                )])
                fig_pie_sym.add_annotation(
                    text=f"<b>{len(portfolio_data)} 檔</b><br><span style='font-size:11px;'>持股標的</span>",
                    x=0.5, y=0.5, font_size=13, font_color="#2F3E34", showarrow=False
                )
                fig_pie_sym.update_layout(
                    title=dict(text="<b>📌 各持股比重配置</b>", font=dict(color="#2F3E34", size=14)),
                    paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=40, b=40), height=320,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#2F3E34", size=11))
                )
                st.plotly_chart(fig_pie_sym, use_container_width=True, config={'displayModeBar': False})

    # 進階分析、加碼試算與歷史淨值走勢
    if st.session_state.show_portfolio_analyzer and portfolio_data:
        st.markdown('<div class="analyzer-card">', unsafe_allow_html=True)
        st.markdown("### 🧮 投資組合進階量化、資產成長曲線與加碼")
        
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
                    rf_rate = st.number_input("設定無風險利率 %（如美國公債利率）：", value=3.5, step=0.1)
                with c2:
                    st_dev = st.number_input("預估年化波動度 (標準差) %：", value=18.0, step=0.5)

                tot_diff = total_market_val_calc - total_cost_val_calc
                tot_roi = (tot_diff / total_cost_val_calc) * 100 if total_cost_val_calc > 0 else 0
                sharpe = (tot_roi - rf_rate) / st_dev if st_dev > 0 else 0
                eval_text = "表現優異，承擔每單位風險能換取良好超額收益！" if sharpe > 1.0 else ("表現尚可，符合基準。" if sharpe > 0 else "目前收益尚未跑贏無風險資產。")
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
                    [
                        "⚖️ 再平衡逢低加碼法（優先補貼跌幅較大或佔比偏低者）",
                        "🚀 強勢順勢加碼法（優先加碼目前正報酬最高者）",
                        "🌐 平均分散加碼法（平均將資金切成等分）"
                    ]
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
                    "建議配置比例": f"{w*100:.1f}%",
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
                        margin=dict(l=10, r=10, t=15, b=10), height=320,
                        hovermode="x unified", dragmode="pan",
                        xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                        yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", title="NT$ 總淨值")
                    )
                    st.plotly_chart(eq_fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("資料天數不足以合成歷史曲線。")

        st.markdown('</div>', unsafe_allow_html=True)

    # 觀察名單與新增持股
    c_action1, c_action2 = st.columns([1, 1])
    with c_action1:
        with st.expander("➕ 新增股票到持股庫", expanded=False):
            c_sym, c_mkt_select, c_shares, c_cost = st.columns([2, 2, 2, 2])
            with c_sym:
                new_sym = st.text_input("股票代號 (例: 2330.TW / NVDA / 7203.T)", key="input_add_sym").strip().upper()
            with c_mkt_select:
                known_markets = list(st.session_state.market_rules.keys())
                auto_idx = known_markets.index(detect_market(new_sym)) if detect_market(new_sym) in known_markets else 0
                chosen_market = st.selectbox("市場國別", known_markets + ["➕ 自訂其他國家/市場..."], index=auto_idx)
            with c_shares:
                new_shares = st.number_input("持有股數", min_value=1.0, value=100.0, step=1.0)
            with c_cost:
                new_cost = st.number_input("買入平均成本", min_value=0.01, value=100.0, step=1.0)

            c_sl, c_tp = st.columns(2)
            with c_sl:
                new_sl = st.number_input("停損警示百分比 (%)", value=-10.0, step=1.0)
            with c_tp:
                new_tp = st.number_input("停利/目標價百分比 (%)", value=20.0, step=1.0)

            final_market = chosen_market
            if chosen_market == "➕ 自訂其他國家/市場...":
                c_c1, c_c2 = st.columns(2)
                with c_c1:
                    final_market = st.text_input("輸入市場名稱", value="其他市場").strip()
                with c_c2:
                    st.session_state.market_rules[final_market] = st.radio("漲跌顏色", ["漲紅跌綠", "漲綠跌紅"], horizontal=True)

            if st.button("確認加入持股庫", use_container_width=True):
                if new_sym:
                    new_entry = {
                        "symbol": new_sym, "market": final_market, "shares": new_shares,
                        "cost": new_cost, "stop_loss": new_sl, "take_profit": new_tp
                    }
                    st.session_state.my_portfolio.append(new_entry)
                    save_portfolio_data(st.session_state.my_portfolio)
                    st.success(f"已成功加入 [{final_market}] {new_sym}！")
                    st.rerun()

    with c_action2:
        with st.expander("👀 觀察自選名單 (Watchlist)", expanded=False):
            w_in, w_btn = st.columns([3, 1])
            with w_in:
                add_w_sym = st.text_input("輸入想觀察的股票代號：", key="input_watch_sym").strip().upper()
            with w_btn:
                st.write("")
                if st.button("➕ 加入自選", use_container_width=True):
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

    # 持股分類清單檢視
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
                st.info("此分類目前尚無任何持股資料。")
            else:
                h1, h2, h3, h4, h5, h6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                h1.markdown("**代號 (市場)**")
                h2.markdown("**持有股數**")
                h3.markdown("**買入成本**")
                h4.markdown("**即時現價**")
                h5.markdown("**未實現累積損益**")
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
                        alert_html = f"<div class='alert-tag alert-loss'>⚠️ 觸發停損 ({diff_pct:.1f}%)</div>"
                    elif diff_pct >= p["take_profit"]:
                        alert_html = f"<div class='alert-tag alert-profit'>🎯 達成目標 ({diff_pct:.1f}%)</div>"

                    r1, r2, r3, r4, r5, r6 = st.columns([2, 1.2, 1.3, 1.3, 2, 2.2])
                    r1.markdown(f"**{sym}** ({mkt}){alert_html}", unsafe_allow_html=True)
                    r2.write(f"{shares:,.0f}")
                    r3.write(f"{curr_s}{cost:,.2f}")
                    r4.write(f"{curr_s}{curr_price:,.2f}")
                    r5.markdown(f"<span style='color:{profit_color}; font-weight:bold;'>{curr_s}{diff:+,.2f} ({diff_pct:+.2f}%)</span>", unsafe_allow_html=True)

                    with r6:
                        b_col1, b_col2 = st.columns([2, 1])
                        with b_col1:
                            if st.button("📊 走勢分析", key=f"btn_an_{i}_{orig_idx}", use_container_width=True):
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
    m4.metric("今日單日總波動", f"{prefix}{today_total_change_calc:+,.2f}")

    if portfolio_data:
        csv_df = pd.DataFrame(portfolio_data)[[
            "symbol", "market", "shares", "cost", "price", "diff", "diff_pct", "stop_loss", "take_profit"
        ]]
        csv_df.columns = ["股票代號", "市場", "持有股數", "買入成本", "即時現價", "累積損益", "報酬率(%)", "停損點(%)", "停利點(%)"]
        csv_data = csv_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 匯出個人持股與損益報表 (CSV)",
            data=csv_data,
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


# ==========================================
# 頁面 3：個股行情與全方位數據（Dashboard Screen）
# ==========================================
elif st.session_state.page == "dashboard":
    dash_css = """
    <style>
    #MainMenu, header, footer, div[data-testid="stDecoration"] { visibility: hidden !important; }
    .stApp {
        background-color: #F7F4EA !important;
        color: #2F3E34 !important;
    }
    /* 全域滑順進場過渡動畫 */
    .block-container {
        padding: 1.5rem 2.5rem !important;
        max-width: 1250px !important;
        animation: pageSlideFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        will-change: transform, opacity;
    }
    @keyframes pageSlideFade {
        0% {
            opacity: 0;
            transform: translateY(8px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
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
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #738A7A !important;
        color: #F7F4EA !important;
    }
    div[data-testid="stButton"] > button:active {
        transform: scale(0.98);
    }
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }

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

    /* 輕量平滑圖表容器（移除吃效能的 blur 濾鏡） */
    .chart-stage-container {
        width: 100%;
        background-color: #F7F4EA;
        border-radius: 12px;
        animation: subtlePop 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        will-change: transform, opacity;
    }
    @keyframes subtlePop {
        0% {
            opacity: 0;
            transform: scale(0.98);
        }
        100% {
            opacity: 1;
            transform: scale(1.0);
        }
    }
    .news-card {
        background-color: #EFEADB;
        border: 1px solid #D8D2C0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        transition: transform 0.15s ease;
    }
    .news-card:hover {
        transform: translateX(4px);
    }
    </style>
    """
    st.markdown(dash_css, unsafe_allow_html=True)

    render_global_ticker()

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
        full_df, info, news_items = fetch_stock_full_data(current_ticker)
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

            tab_chart, tab_benchmark, tab_dca, tab_news, tab_data, tab_info = st.tabs([
                "📈 動態走勢與技術線", "🌐 大盤基準對比 (Alpha)", "📅 定期定額試算 (DCA)", "📰 重大即時新聞", "📋 歷史明細", "🏢 公司財務與基本面"
            ])

            with tab_chart:
                c_mode, c_type, c_tools = st.columns([2, 1.5, 2.5])
                with c_mode:
                    preset_view = st.selectbox(
                        "聚焦區間：",
                        ["最近 1 個月", "最近 3 個月", "最近 6 個月", "最近 1 年", "最近 4 年", "上市以來全部"],
                        index=1
                    )
                with c_type:
                    chart_render_type = st.radio("圖表類型", ["平滑折線", "專業蠟燭 K 線"], horizontal=True)
                with c_tools:
                    show_indicators = st.multiselect(
                        "疊加技術指標",
                        ["20 日均線 (MA20)", "60 日季線 (MA60)", "RSI 強弱指標", "顯示成交量副圖"],
                        default=["20 日均線 (MA20)", "顯示成交量副圖"]
                    )

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
                has_vol = "顯示成交量副圖" in show_indicators

                if has_rsi and has_vol:
                    rows, row_heights = 3, [0.60, 0.20, 0.20]
                    vol_row, rsi_row = 2, 3
                elif has_vol:
                    rows, row_heights = 2, [0.75, 0.25]
                    vol_row, rsi_row = 2, None
                elif has_rsi:
                    rows, row_heights = 2, [0.75, 0.25]
                    vol_row, rsi_row = None, 2
                else:
                    rows, row_heights = 1, [1.0]
                    vol_row, rsi_row = None, None

                fig = make_subplots(
                    rows=rows, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.06,
                    row_heights=row_heights
                )

                if chart_render_type == "平滑折線":
                    fig.add_trace(go.Scatter(
                        x=plot_data.index, y=plot_data["Close"], mode='lines', name='收盤價',
                        line=dict(color=theme_color, width=2.5),
                        fill='tozeroy',
                        fillcolor=f"rgba({int(theme_color[1:3], 16)}, {int(theme_color[3:5], 16)}, {int(theme_color[5:7], 16)}, 0.08)"
                    ), row=1, col=1)
                else:
                    up_c = "#E53935" if market_type == "台股" else "#2E7D32"
                    dn_c = "#2E7D32" if market_type == "台股" else "#E53935"
                    fig.add_trace(go.Candlestick(
                        x=plot_data.index,
                        open=plot_data['Open'], high=plot_data['High'],
                        low=plot_data['Low'], close=plot_data['Close'],
                        increasing_line_color=up_c, decreasing_line_color=dn_c, name='K 線'
                    ), row=1, col=1)

                if "MA20" in plot_data:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["MA20"], mode='lines', name='MA20 (月線)', line=dict(color='#E67E22', width=1.5)), row=1, col=1)
                if "MA60" in plot_data:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["MA60"], mode='lines', name='MA60 (季線)', line=dict(color='#8E44AD', width=1.5)), row=1, col=1)

                if has_vol:
                    vol_colors = [(theme_color if r["Close"] >= r["Open"] else "#9E9E9E") for _, r in plot_data.iterrows()]
                    fig.add_trace(go.Bar(x=plot_data.index, y=plot_data["Volume"], name="成交量", marker_color=vol_colors, opacity=0.7), row=vol_row, col=1)

                if has_rsi:
                    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["RSI"], mode='lines', name='RSI(14)', line=dict(color='#2980B9', width=1.8)), row=rsi_row, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="#C0392B", row=rsi_row, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="#27AE60", row=rsi_row, col=1)

                fig.update_layout(
                    paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                    margin=dict(l=10, r=10, t=15, b=10),
                    height=550 if rows > 1 else 490,
                    hovermode="x unified", dragmode="pan",
                    xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", range=[init_start, latest_date], rangeslider=dict(visible=False), type="date"),
                    yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", autorange=True, fixedrange=False)
                )

                st.markdown('<div class="chart-stage-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False, 'showTips': False})
                st.markdown('</div>', unsafe_allow_html=True)
                st.caption("💡 提示：在 iPad 上可用 **雙指捏合縮放** 任意平移與展開歷史走勢。")

            with tab_benchmark:
                bm_symbol, bm_name = get_market_benchmark(market_type)
                st.markdown(f"#### 🌐 {company_name} 對比市場大盤基準（{bm_name}）")
                bm_period = st.selectbox("對比時間長度：", ["最近 3 個月", "最近 6 個月", "最近 1 年", "最近 3 年"], index=2)
                bm_days_map = {"最近 3 個月": 90, "最近 6 個月": 180, "最近 1 年": 365, "最近 3 年": 365*3}
                bm_start = datetime.now() - timedelta(days=bm_days_map[bm_period])

                with st.spinner(f"正在對齊並計算與 {bm_name} 的雙軸累積回報..."):
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
                            bm_fig.add_trace(go.Scatter(x=common_idx, y=s_return, mode='lines', name=f"{current_ticker} 報酬率 (%)", line=dict(color='#2E7D32' if alpha >= 0 else '#E53935', width=2.5)))
                            bm_fig.add_trace(go.Scatter(x=common_idx, y=b_return, mode='lines', name=f"{bm_name} 報酬率 (%)", line=dict(color='#7F8C8D', width=2, dash='dot')))
                            bm_fig.update_layout(
                                paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                                margin=dict(l=10, r=10, t=15, b=10), height=450,
                                hovermode="x unified", dragmode="pan",
                                xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                                yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34", title="累積報酬率 (%)")
                            )
                            b_c1, b_c2, b_c3 = st.columns(3)
                            b_c1.metric(f"{current_ticker} 累積報酬", f"{s_return.iloc[-1]:+.2f}%")
                            b_c2.metric(f"{bm_name} 累積報酬", f"{b_return.iloc[-1]:+.2f}%")
                            b_c3.metric("超額報酬 (Alpha)", f"{alpha:+.2f}%")
                            st.plotly_chart(bm_fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

            with tab_dca:
                st.markdown(f"#### 📅 定期定額 (DCA) 投資成果回測")
                c_dca1, c_dca2 = st.columns(2)
                with c_dca1:
                    monthly_amount = st.number_input("每月固定投入金額 ($)：", min_value=100.0, value=5000.0, step=500.0)
                with c_dca2:
                    dca_years = st.selectbox("回測年期：", [1, 2, 3, 5], index=1)

                dca_start = datetime.now() - timedelta(days=dca_years * 365)
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
                        dca_profit = final_val - total_invested
                        dca_roi = (dca_profit / total_invested) * 100 if total_invested > 0 else 0

                        dc1, dc2, dc3 = st.columns(3)
                        dc1.metric("總投入本金", f"${total_invested:,.0f}")
                        dc2.metric("累積期末市值", f"${final_val:,.0f}")
                        dc3.metric("DCA 累積報酬", f"{dca_profit:+,.0f}", f"{dca_roi:+.2f}%")

                        timeline_df = pd.DataFrame(dca_timeline)
                        fig_dca = go.Figure()
                        fig_dca.add_trace(go.Scatter(x=timeline_df["date"], y=timeline_df["val"], mode='lines', name='資產現值', line=dict(color='#2E7D32', width=2.5)))
                        fig_dca.add_trace(go.Scatter(x=timeline_df["date"], y=timeline_df["invested"], mode='lines', name='累積本金', line=dict(color='#7F8C8D', width=2, dash='dot')))
                        fig_dca.update_layout(
                            paper_bgcolor="#F7F4EA", plot_bgcolor="#F7F4EA",
                            margin=dict(l=10, r=10, t=15, b=10), height=350, hovermode="x unified",
                            xaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34"),
                            yaxis=dict(showgrid=True, gridcolor="#E3DEC8", color="#2F3E34")
                        )
                        st.plotly_chart(fig_dca, use_container_width=True)

            with tab_news:
                st.markdown(f"#### 📰 {company_name} 最近重大即時新聞")
                if news_items:
                    for news in news_items[:6]:
                        title = news.get("title", "無標題")
                        publisher = news.get("publisher", "未知媒體")
                        link = news.get("link", "#")
                        pub_time = news.get("providerPublishTime", None)
                        time_str = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M") if pub_time else ""

                        st.markdown(f"""
                        <div class="news-card">
                            <a href="{link}" target="_blank" style="text-decoration:none; color:#2F3E34; font-weight:bold; font-size:1.05rem;">{title}</a>
                            <div style="font-size:0.8rem; color:#738A7A; margin-top:4px;">來源：{publisher} | 發布時間：{time_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("目前無即時新聞資料。")

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
