
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 樣式配置 ---
st.set_page_config(page_title="V32.0 巔峰指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 22px; font-weight: bold; margin: 25px 0 10px 0; border-left: 5px solid #00ffcc; padding-left: 12px; }
    .card-box { display: inline-block !important; min-width: 300px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; flex: 0 0 auto !important; margin-right: 10px; }
    .score-banner { font-size: 16px; font-weight: bold; color: #FFD700; background: rgba(0,0,0,0.5); border-radius: 6px; padding: 4px; margin-bottom: 8px; border: 1px solid #FFD700; }
    /* Sidebar 卡片優化 */
    [data-testid="stSidebar"] .card-box { min-width: 100%; margin-right: 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心計算模組 ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_data(ticker):
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
    f2 = 10 if (ma20 > ma50) and (p > ma20 * 0.985) else 0
    f3 = 10 if (rsi > 45) and (vol_ratio > 1.3 or (p < prev_row['Close'] and vol_ratio < 0.8)) else 0
    f1 = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) else 0
    v26_day = int((f2 * 0.5) + (f3 * 0.3) + (f1 * 0.2))
    cv = np.std([curr['MA10'], ma20, ma50]) / np.mean([curr['MA10'], ma20, ma50])
    a2_s = 10 if cv < 0.03 else (7 if cv < 0.05 else 3)
    a3_s = 10 if curr['Volume'] < df_slice['Volume'].tail(20).mean() * 0.55 else 5
    a1_s = 10 if curr['MACD_h'] > 0 else 3
    awi_single = int((a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3))
    return v26_day, awi_single, f1, f2, f3

# --- 3. 渲染卡片 (修正渲染錯誤並補回權重) ---
def render_card(t, df):
    if df is None: return ""
    v_h, a_h, ic_h = [], [], []
    f1_list, f2_list, f3_list, v26_list = [], [], [], []
    for i in range(5, 0, -1):
        idx = len(df) - i
        v, asingle, f1, f2, f3 = get_logic(df.iloc[:idx+1], df.iloc[idx-1])
        v_h.append(str(v)); a_h.append(str(asingle))
        f1_list.append(f1); f2_list.append(f2); f3_list.append(f3); v26_list.append(v)
        ic_h.append("🎆" if asingle >= 9 else ("☀️" if asingle >= 7 else "☁️" if asingle >= 5 else "🌫️"))
    
    avg_total = sum(v26_list) / 5
    avg_f1, avg_f2, avg_f3 = sum(f1_list)/5, sum(f2_list)/5, sum(f3_list)/5
    p, ch = float(df['Close'].iloc[-1]), ((df['Close'].iloc[-1]-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100
    
    if avg_total >= 9.0: bg, cmd = "#1E4620", "🔥 冠軍共振・最強進攻"
    elif avg_total >= 7.0: bg, cmd = "#2E5A2E", "⚡ 動能蓄勢・準備突破"
    elif avg_total >= 4.0: bg, cmd = "#64641E", "💤 縮量洗盤・等待表態"
    else: bg, cmd = "#461E1E", "❌ 趨勢破壞・避開空頭"

    # 使用 f-string 進行乾淨的 HTML 拼接
    return f"""
    <div class="card-box" style="background-color: {bg}; border: 1.5px solid #00ffcc; padding: 15px; border-radius: 12px; text-align: center; color: white;">
        <h3 style="margin:0; font-size:18px;">{t} {ic_h[-1]}</h3>
        <div class="score-banner">五日平均戰力: {avg_total:.1f} / 10</div>
        <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{p:.2f} <span style="font-size:14px; color:#0f0;">({ch:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:8px; font-size:10px; line-height:1.6;">
            <div>🥇 F2 結構(50%)平均: <b>{avg_f2:.1f}/10</b></div>
            <div>🔥 F3 籌碼(30%)平均: <b>{avg_f3:.1f}/10</b></div>
            <div>✅ F1 技術(20%)平均: <b>{avg_f1:.1f}/10</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:10px; border-radius:8px; font-family:monospace; font-size:13px; margin:15px 0; text-align:left;">
            <div>V26(h): {" | ".join(v_h)}</div>
            <div style="border-top:1px solid #333; margin-top:5px; padding-top:5px;">
                AWI(h): {" | ".join(a_h)}
            </div>
            <div style="font-size:15px; margin-top:5px;">{" ".join(ic_h)}</div>
        </div>
        <p style="font-size:13px; font-weight:bold; color:#fff;">{cmd}</p>
    </div>"""

# --- 4. 側邊欄 ---
st.sidebar.title("🕹️ 控制中心")
search_ticker = st.sidebar.text_input("🔍 偵察自選代碼 (Enter 套用)", "").upper()
if search_ticker:
    with st.sidebar:
        df_m = fetch_data(search_ticker)
        if df_m is not None:
            st.markdown(render_card(search_ticker, df_m), unsafe_allow_html=True)
        else:
            st.error("查無資料。")

if st.sidebar.button("🧹 刷新數據"):
    st.cache_data.clear()
    st.rerun()

# --- 5. 主程式板塊 (11 個完整板塊) ---
st.title("🛡️ 雙軌指揮中心 V32.0")
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
    cards_html = "".join([f'<div class="card-box">{render_card(t, fetch_data(t))}</div>' for t in tickers])
    st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)

st.caption(f"最後同步於: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V32.0 終極穩定版")
