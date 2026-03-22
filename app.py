import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 環境定錨 (完全保留 V26.0 經典 CSS) ---
st.set_page_config(page_title="V28.4 巔峰指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; -webkit-overflow-scrolling: touch !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0; border-left: 6px solid #00ffcc; padding-left: 15px; }
    .card-box { display: inline-block !important; vertical-align: top !important; min-width: 300px; max-width: 300px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; white-space: normal !important; flex: 0 0 auto !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心邏輯 (F1/F2/F3 & AWI) ---
def calculate_metrics(df):
    try:
        # 預計算所有需要的指標
        df['MA10'] = df['Close'].rolling(10).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean() if len(df) >= 200 else df['MA50']
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-6))))
        
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        df = df.dropna(subset=['MA50', 'RSI', 'MACD_h'])
        return df
    except:
        return None

def get_scores(df_slice, prev_row):
    # V26 舊邏輯
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    f2_cond = (curr['MA20'] > curr['MA50'])
    f2_std = 10 if f2_cond and (p > ma20 * 0.985) else 0
    is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
    is_washout = (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (is_attack or is_washout) and (rsi > 45) else 0
    f1_std = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    v26_total = int((f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2))
    
    # AWI 新邏輯
    ma_list = [curr['MA10'], curr['MA20'], curr['MA50']]
    cv = np.std(ma_list) / np.mean(ma_list)
    a2_s = 10 if cv < 0.03 else (7 if cv < 0.05 else 3)
    v20 = df_slice['Volume'].tail(20).mean()
    a3_s = 10 if curr['Volume'] < v20 * 0.5 else (7 if curr['Volume'] < v20 * 0.8 else 4)
    a1_s = 10 if curr['MACD_h'] > 0 else 3
    awi_score = (a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3)
    icon = "🎆" if awi_score >= 9.0 else ("☀️" if awi_score >= 7.0 else ("☁️" if awi_score >= 5.0 else "🌫️"))
    
    return v26_total, awi_score, icon, f1_std, f2_std, f3_std

# --- 3. 數據偵察 (強化穩定性) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, timeout=10)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[df['Volume'] > 0].copy()
        return calculate_metrics(df)
    except:
        return None

# --- 4. 渲染函數 ---
def render_card(t, df):
    if df is None: return ""
    v26_h, awi_h, awi_sum = [], [], 0
    for i in range(5, 0, -1):
        idx = len(df) - i
        v26_s, awi_s, aicon, f1, f2, f3 = get_scores(df.iloc[:idx+1], df.iloc[idx-1])
        v26_h.append(v26_s); awi_h.append(aicon); awi_sum += awi_s
    
    # 當前數據
    v26_s, awi_s, icon, f1, f2, f3 = get_scores(df, df.iloc[-2])
    p, ch = float(df['Close'].iloc[-1]), ((df['Close'].iloc[-1]-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100
    bg = "#1E4620" if v26_s >= 9 else ("#326432" if v26_s >= 6 else "#46461E")
    cmd = "🔥 冠軍進攻" if v26_s >= 9 else "💪 跡象轉強"
    
    return f"""
    <div class="card-box" style="background-color: {bg}; border: 1.5px solid #00ffcc;">
        <h3 style="margin:0;">{t} {icon}</h3>
        <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{p:.2f} <span style="font-size:14px; color:#0f0;">({ch:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; font-size:11px; line-height:1.5;">
            <div>🥇 結構(F2)(50%): <b>{int(f2)}/10</b></div>
            <div>🔥 籌碼(F3)(30%): <b>{int(f3)}/10</b></div>
            <div>✅ 技術(F1)(20%): <b>{int(f1)}/10</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:5px; border-radius:6px; font-family:monospace; font-size:13px; margin:10px 0;">
            V26(h): {"|".join(map(str, v26_h))} <br> AWI(5): {" ".join(awi_h)}
        </div>
        <p style="font-size:20px; font-weight:bold; color:#FFD700; margin:0;">{int(awi_sum*1117)} AWI Pts</p>
        <p style="font-size:11px; font-weight:bold; color:#fff;">{cmd}</p>
    </div>"""

# --- 5. 主程式架構 ---
# Sidebar 優先渲染，解決消失問題
st.sidebar.title("🕹️ 控制中心")
manual_input = st.sidebar.text_input("🔍 偵察自選代碼 (如 NVDA)", "").upper()
if st.sidebar.button("🧹 刷新數據"):
    st.cache_data.clear()
    st.rerun()

st.title("🛡️ 雙軌指揮中心 V28.4")

# 問題 3 修復：完整板塊 (滿漢全席)
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

# 處理自選
if manual_input:
    st.markdown(f'<div class="sector-title">🎯 手動偵察: {manual_input}</div>', unsafe_allow_html=True)
    df_manual = fetch_data(manual_input)
    if df_manual is not None:
        st.markdown(f'<div class="h-wrapper">{render_card(manual_input, df_manual)}</div>', unsafe_allow_html=True)
    else:
        st.error("代碼錯誤或抓取超時")

# 處理各板塊 (優化：使用拼接字串減少渲染次數)
for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    cards_html = ""
    for t in tickers:
        df_ticker = fetch_data(t)
        if df_ticker is not None:
            cards_html += render_card(t, df_ticker)
    
    if cards_html:
        st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)
    else:
        st.write("📡 板塊數據加載中或暫無信號...")

st.caption(f"數據更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V28.4 究極穩定版")

