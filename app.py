
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 環境佈局 ---
st.set_page_config(page_title="V30.0 巔峰指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 22px; font-weight: bold; margin: 25px 0 10px 0; border-left: 6px solid #00ffcc; padding-left: 12px; }
    .card-box { display: inline-block !important; min-width: 310px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; flex: 0 0 auto !important; margin-right: 10px; }
    .score-banner { font-size: 16px; font-weight: bold; color: #FFD700; background: rgba(0,0,0,0.5); border-radius: 6px; padding: 5px; margin-bottom: 8px; border: 1px solid #FFD700; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心演算 (數據深度 2y) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_full_data(ticker):
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False, timeout=8)
        if df.empty or len(df) < 100: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[df['Volume'] > 0].copy()
        df['MA10'] = df['Close'].rolling(10).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-6))))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        return df.dropna(subset=['MA50', 'RSI', 'MACD_h'])
    except: return None

def get_logic(df_slice, prev_row):
    curr = df_slice.iloc[-1]
    p, rsi, ma20, ma50 = float(curr['Close']), float(curr['RSI']), float(curr['MA20']), float(curr['MA50'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    # 三個獨立 Filter
    f2 = 10 if (ma20 > ma50) and (p > ma20 * 0.985) else 0
    f3 = 10 if (rsi > 45) and (vol_ratio > 1.3 or (p < prev_row['Close'] and vol_ratio < 0.8)) else 0
    f1 = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) else 0
    v26_s = int((f2 * 0.5) + (f3 * 0.3) + (f1 * 0.2))
    # AWI 單日分
    cv = np.std([curr['MA10'], ma20, ma50]) / np.mean([curr['MA10'], ma20, ma50])
    a2_s = 10 if cv < 0.03 else (7 if cv < 0.05 else 3)
    a3_s = 10 if curr['Volume'] < df_slice['Volume'].tail(20).mean() * 0.55 else 5
    a1_s = 10 if curr['MACD_h'] > 0 else 3
    awi_single = (a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3)
    return v26_s, awi_single, f1, f2, f3

# --- 3. 渲染卡片 (補回 F1, F3 累計分) ---
def render_v30_card(t, df):
    if df is None: return ""
    v_h, a_h, ic_h = [], [], []
    f1_sum, f2_sum, f3_sum, awi_total = 0, 0, 0, 0
    for i in range(5, 0, -1):
        idx = len(df) - i
        v, asingle, f1, f2, f3 = get_logic(df.iloc[:idx+1], df.iloc[idx-1])
        v_h.append(str(v)); a_h.append(str(int(asingle)))
        f1_sum += f1; f2_sum += f2; f3_sum += f3; awi_total += asingle
        ic_h.append("🎆" if asingle >= 9 else ("☀️" if asingle >= 7 else "☁️" if asingle >= 5 else "🌫️"))
    
    v_now, a_now, f1_now, f2_now, f3_now = get_logic(df, df.iloc[-2])
    p, ch = float(df['Close'].iloc[-1]), ((df['Close'].iloc[-1]-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100
    bg = "#1E4620" if v_now >= 9 else ("#64641E" if v_now >= 5 else "#461E1E")

    return f"""
    <div class="card-box" style="background-color: {bg}; border: 2px solid #00ffcc;">
        <h3 style="margin:0;">{t} {ic_h[-1]}</h3>
        <div class="score-banner">
            🥈 F2(結): {f2_sum}/50 | 🔥 F3(籌): {f3_sum}/50<br>
            ✅ F1(技): {f1_sum}/50 | 🏆 總分: {f1_sum+f2_sum+f3_sum}/150
        </div>
        <p style="font-size:20px; font-weight:bold; margin:5px 0;">&dollar;{p:.2f} <span style="font-size:14px; color:#0f0;">({ch:+.2f}%)</span></p>
        <div style="background-color:black; color:#0f0; padding:8px; border-radius:6px; font-family:monospace; font-size:13px; margin:10px 0; text-align:left;">
            <div>V26(h): {" | ".join(v_h)}</div>
            <div style="border-top:1px solid #333; margin-top:4px; padding-top:4px;">
                AWI(h): {" | ".join(a_h)} </div>
            <div style="font-size:14px; margin-top:4px;">{" ".join(ic_h)}</div>
        </div>
        <p style="font-size:18px; font-weight:bold; color:#FFD700; margin:0;">{int(awi_total * 1117)} AWI Pts</p>
    </div>"""

# --- 4. 主介面 (邏輯優先順序) ---
st.sidebar.title("🕹️ 控制中心")
search_ticker = st.sidebar.text_input("🔍 偵察自選代碼", "").upper()
if st.sidebar.button("🧹 刷新數據"):
    st.cache_data.clear()
    st.rerun()

st.title("🛡️ 雙軌指揮中心 V30.0")

# 解決問題 1：手動輸入優先顯示
if search_ticker:
    st.markdown(f'<div class="sector-title">🎯 手動偵察優先: {search_ticker}</div>', unsafe_allow_html=True)
    with st.spinner(f"正在深度掃描 {search_ticker}..."):
        df_manual = fetch_full_data(search_ticker)
        if df_manual is not None:
            st.markdown(f'<div class="h-wrapper">{render_v30_card(search_ticker, df_manual)}</div>', unsafe_allow_html=True)
        else:
            st.error("代碼查無資料或 yfinance 拒絕連線。")

# 解決問題 2 & 3：滿漢全席板塊與 F1/F3 累計得分
SECTORS = {
    "🌌 量子計算": ["IONQ", "RGTI", "QBTS", "QUBT", "D-WAVE"],
    "🌈 光通訊": ["AXTI", "AAOI", "LITE", "FN", "COHR", "AVGO", "MRVL"],
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "TSM", "ARM", "MU"], 
    "💻 AI 軟體": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "🤖 機器人": ["ASML", "AMAT", "LRCX", "ISRG", "TER"]
}

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    cards_html = "".join([render_v30_card(t, fetch_full_data(t)) for t in tickers])
    st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)
