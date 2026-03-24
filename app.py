
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- 1. 頁面配置與卡片視覺樣式 (完全復刻昨天最強 UI) ---
st.set_page_config(page_title="Apex Ambush V32.5", page_icon="🛰️", layout="wide")

st.markdown("""
    <style>
    .sector-card { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .stock-row { background-color: #f8fafc; border-radius: 10px; padding: 18px; margin-bottom: 12px; border-left: 6px solid #cbd5e1; }
    .awi-badge { padding: 3px 10px; border-radius: 5px; font-size: 0.9rem; background-color: rgba(255,255,255,0.8); border: 1px solid #e2e8f0; font-weight: bold; }
    .score-text { font-size: 1.8rem; color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心計算引擎 (融合 A1/A2/A3 與 F1/F2/F3 邏輯) ---
def analyze_stock(ticker, spy_df):
    try:
        df = yf.download(ticker, period="6mo", auto_adjust=True, progress=False, threads=False)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 指標原生計算
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_DIF'] = ema12 - ema26
        df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
        
        hist_scores = []
        for i in range(-4, 1):
            sub = df.iloc[:len(df)+i] if i < 0 else df
            curr, prev = sub.iloc[-1], sub.iloc[-2]
            
            # A1: 趨勢對齊 (20%) - F1/F2: MACD雙線零軸上
            a1_score = 10 if (curr['MACD_DIF'] > 0 and curr['MACD_DEA'] > 0) else (6 if curr['MACD_DIF'] > prev['MACD_DIF'] else 0)
            a1_w = round(a1_score * 0.2, 1)
            
            # A2: 構造錨定 (40%) - F2: VCP均線糾結度 < 3%
            mas = [float(curr['MA10']), float(curr['MA20']), float(curr['MA50'])]
            comp = (np.std(mas) / np.mean(mas)) * 100
            # A2 滿分條件：站穩 MA20 (F1) 且極度糾結 (VCP)
            a2_score = 10 if (curr['Close'] > curr['MA20'] and comp < 1.5) else (8 if comp < 3.0 else 4)
            a2_w = round(a2_score * 0.4, 1)
            
            # A3: 能量活化 (40%) - F3: RS強度與成交量判定
            vol_ratio = curr['Volume'] / sub['Volume'].tail(10).mean()
            v_s = 5 if vol_ratio > 1.3 or vol_ratio < 0.5 else 0
            rs = (curr['Close']/sub.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close'])
            r_s = 5 if rs > 0.02 else (3 if rs > 0 else 0)
            a3_w = round((v_s + r_s) * 0.4, 1)
            
            hist_scores.append(round(a1_w + a2_w + a3_w, 1))
            
        return {
            "tk": ticker, "sc": hist_scores[-1], "bg": "#dcfce7" if hist_scores[-1] >= 9 else "#f1f5f9", 
            "a1": a1_score, "a1w": a1_w, "a2": a2_score, "a2w": a2_w, "a3": (v_s + r_s), "a3w": a3_w, 
            "hist": hist_scores, "cp": round(comp, 2), "pr": round(float(df.iloc[-1]['Close']), 2)
        }
    except: return None

# --- 3. 左側 Sidebar 查詢功能 (真空預設) ---
st.sidebar.header("🔍 即時個股查詢")
user_query = st.sidebar.text_input("輸入代號 (例如: OKLO)", value="")

spy_raw = yf.download("SPY", period="6mo", auto_adjust=True, progress=False, threads=False)
if isinstance(spy_raw.columns, pd.MultiIndex): spy_raw.columns = spy_raw.columns.get_level_values(0)

if user_query:
    st.sidebar.markdown("---")
    q_res = analyze_stock(user_query, spy_raw)
    if q_res:
        st.sidebar.markdown(f"""
        <div class="stock-row" style="background-color: {q_res['bg']}; border-left: 6px solid #4f46e5;">
            <b>🔍 {q_res['tk']} — ${q_res['pr']}</b>
            <div class="score-text">{q_res['sc']} <small>分</small></div>
            <hr style="margin: 8px 0;">
            <small>A1:{q_res['a1']} | A2:{q_res['a2']} | A3:{q_res['a3']}</small><br>
            <small>加權:{q_res['a1w']} | {q_res['a2w']} | {q_res['a3w']}</small><br>
            <small>5日 AWI: {q_res['hist']}</small>
        </div>
        """, unsafe_allow_html=True)

# --- 4. 右側 11 個戰略板塊 (一帶多結構完全還原) ---
st.title("🛰️ Apex Ambush V32.5 指揮部")

STRATEGIC_SECTORS = {
    "AI 量子戰略板塊": ["AAOI", "IONQ", "RGTI", "QUBT"],
    "巔峰埋伏領航": ["PL", "SOUN", "BBAI", "AISP"],
    "航太衛星板塊": ["LUNR", "RKLB", "SIDU", "ASTS"],
    "電動車與能源": ["TSLA", "RIVN", "LCID"],
    "算力核心板塊": ["NVDA", "AMD", "AVGO", "SMCI"],
    "晶圓代工板塊": ["TSEM", "TSM", "INTC"],
    "高速傳輸板塊": ["CRDO", "MRVL", "ALAB"],
    "雲端軟體龍頭": ["MSFT", "ORCL", "SNOW"],
    "數位廣告搜尋": ["GOOGL", "AMZN", "BIDU"],
    "社交元宇宙": ["META", "SNAP", "PINS"],
    "消費電子": ["AAPL", "SONY", "HPQ"]
}

for sector_name, stocks in STRATEGIC_SECTORS.items():
    st.markdown(f'<div class="sector-card"><h3>📦 {sector_name}</h3>', unsafe_allow_html=True)
    cols = st.columns(2)
    for idx, ticker in enumerate(stocks):
        with cols[idx % 2]:
            time.sleep(0.5) 
            res = analyze_stock(ticker, spy_raw)
            if res:
                st.markdown(f"""
                <div class="stock-row" style="background-color: {res['bg']};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b>{res['tk']} — ${res['pr']}</b>
                        <span class="score-text">{res['sc']}</span>
                    </div>
                    <hr style="margin: 10px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                        <div><small>A1(20%)</small><br><b>{res['a1']}</b>({res['a1w']})</div>
                        <div><small>A2(40%)</small><br><b>{res['a2']}</b>({res['a2w']})</div>
                        <div><small>A3(40%)</small><br><b>{res['a3']}</b>({res['a3w']})</div>
                    </div>
                    <div style="margin-top:10px;">
                        <span class="awi-badge">5日 AWI: {res['hist']}</span>
                        <span class="awi-badge">壓縮: {res['cp']}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
