
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 環境配置與 CSS 強化 ---
st.set_page_config(page_title="V31.4 巔峰指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 22px; font-weight: bold; margin: 25px 0 10px 0; border-left: 5px solid #00ffcc; padding-left: 12px; }
    .card-box { display: inline-block !important; min-width: 295px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; flex: 0 0 auto !important; margin-right: 10px; }
    .current-score { font-size: 16px; font-weight: bold; color: #FFD700; background: rgba(0,0,0,0.5); border-radius: 6px; padding: 4px; margin-bottom: 8px; border: 1px solid #FFD700; }
    /* 側邊欄卡片微調 */
    [data-testid="stSidebar"] .card-box { min-width: 100%; margin-right: 0; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算模組 (2y 數據深度確保 MA200) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_full_data(ticker):
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False, timeout=12)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[df['Volume'] > 0].copy()
        df['MA10'] = df['Close'].rolling(10).mean(); df['MA20'] = df['Close'].rolling(20).mean(); df['MA50'] = df['Close'].rolling(50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-6))))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean(); ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        return df.dropna(subset=['MA50', 'RSI', 'MACD_h'])
    except: return None

def get_logic(df_slice, prev_row):
    curr = df_slice.iloc[-1]
    p, rsi, ma20, ma50 = float(curr['Close']), float(curr['RSI']), float(curr['MA20']), float(curr['MA50'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    # F-System (單項基準 10 分)
    f2 = 10 if (ma20 > ma50) and (p > ma20 * 0.985) else 0
    f3 = 10 if (rsi > 45) and (vol_ratio > 1.3 or (p < prev_row['Close'] and vol_ratio < 0.8)) else 0
    f1 = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) else 0
    v26_s = int((f2 * 0.5) + (f3 * 0.3) + (f1 * 0.2))
    # AWI-System (單項基準 10 分)
    cv = np.std([curr['MA10'], ma20, ma50]) / np.mean([curr['MA10'], ma20, ma50])
    a2_s = 10 if cv < 0.03 else (7 if cv < 0.05 else 3)
    a3_s = 10 if curr['Volume'] < df_slice['Volume'].tail(20).mean() * 0.55 else 5
    a1_s = 10 if curr['MACD_h'] > 0 else 3
    awi_single = int((a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3))
    return v26_s, awi_single, f1, f2, f3

# --- 3. 渲染卡片 (移除 Pts, 實現直線隔離) ---
def render_card(t, df):
    if df is None: return ""
    v_h, a_h, ic_h = [], [], []
    for i in range(5, 0, -1):
        idx = len(df) - i
        v, asingle, f1, f2, f3 = get_logic(df.iloc[:idx+1], df.iloc[idx-1])
        v_h.append(str(v)); a_h.append(str(asingle))
        ic_h.append("🎆" if asingle >= 9 else ("☀️" if asingle >= 7 else "☁️" if asingle >= 5 else "🌫️"))
    
    v_now, a_now, f1_now, f2_now, f3_now = get_logic(df, df.iloc[-2])
    p, ch = float(df['Close'].iloc[-1]), ((df['Close'].iloc[-1]-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100
    bg = "#1E4620" if v_now >= 9 else ("#64641E" if v_now >= 5 else "#461E1E")

    return f"""
    <div style="background-color: {bg}; border: 1.5px solid #00ffcc; padding: 12px; border-radius: 12px; text-align: center; color: white; width: 100%;">
        <h3 style="margin:0; font-size:16px;">{t} {ic_h[-1]}</h3>
        <div class="current-score" style="font-size:14px;">今日總分: {v_now} / 10</div>
        <p style="font-size:20px; font-weight:bold; margin:5px 0;">&dollar;{p:.2f} <span style="font-size:13px; color:#0f0;">({ch:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; font-size:11px; line-height:1.5;">
            <div>🥇 冠軍結構(F2)(50%): <b>{int(f2_now)}/10</b></div>
            <div>🔥 主力籌碼(F3)(30%): <b>{int(f3_now)}/10</b></div>
            <div>✅ 技術指標(F1)(20%): <b>{int(f1_now)}/10</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:6px; border-radius:6px; font-family:monospace; font-size:12px; margin:10px 0; text-align:left;">
            <div>V26(h): {" | ".join(v_h)}</div>
            <div style="border-top:1px solid #333; margin-top:4px; padding-top:4px;">
                AWI(h): {" | ".join(a_h)} </div>
            <div style="font-size:14px; margin-top:4px;">{" ".join(ic_h)}</div>
        </div>
        <p style="font-size:11px; font-weight:bold; color:#fff;">{"🔥 冠軍進攻" if v_now >= 9 else "💤 結構整理"}</p>
    </div>"""

# --- 4. 側邊欄控制中心 (問題修復：偵察結果直接在 Sidebar 下方) ---
st.sidebar.title("🕹️ 控制中心")
search_ticker = st.sidebar.text_input("🔍 偵察自選代碼", "").upper()

if search_ticker:
    with st.sidebar:
        df_m = fetch_full_data(search_ticker)
        if df_m is not None:
            st.markdown(render_card(search_ticker, df_m), unsafe_allow_html=True)
        else:
            st.error("查無此代碼資料。")

if st.sidebar.button("🧹 刷新全局數據"):
    st.cache_data.clear()
    st.rerun()

# --- 5. 主程式板塊 (完整 11 個板塊) ---
st.title("🛡️ 雙軌指揮中心 V31.4")

SECTORS = {
    "🌌 量子計算": ["IONQ", "RGTI", "QBTS", "QUBT", "D-WAVE"],
    "🌈 光通訊": ["AXTI", "AAOI", "LITE", "FN", "COHR", "AVGO", "MRVL"],
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "TSM", "ARM", "MU"], 
    "💻 AI 軟體": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "☁️ 網絡安全": ["CRWD", "PANW", "NET", "ZS", "FTNT"], 
    "🧬 生物醫療": ["HIMS", "SANA", "SNDX", "RXRX", "TEM"],
    "🛰️ 國防安全": ["RCAT", "AVAV", "KTOS", "CRCL", "BBAI"],
    "🤖 機器人": ["ASML", "AMAT", "LRCX", "ISRG", "TER"],
    "🚗 交通傳產": ["TSLA", "RIVN", "AMZN", "AAPL", "GOOGL"]
}

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    cards_html = "".join([f'<div class="card-box">{render_card(t, fetch_full_data(t))}</div>' for t in tickers])
    st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)

st.caption(f"數據自動更新於: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V31.4 終極版")
