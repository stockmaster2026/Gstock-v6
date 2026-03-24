
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. 頁面配置與卡片視覺樣式 (完全復刻昨天最強版) ---
st.set_page_config(page_title="Apex Ambush V32.5", page_icon="🛰️", layout="wide")

st.markdown("""
    <style>
    .sector-card { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 15px; padding: 22px; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .stock-row { background-color: #f8fafc; border-radius: 10px; padding: 18px; margin-bottom: 12px; border-left: 6px solid #cbd5e1; }
    .awi-badge { padding: 3px 10px; border-radius: 5px; font-size: 0.9rem; background-color: rgba(255,255,255,0.8); border: 1px solid #e2e8f0; font-weight: bold; }
    .score-text { font-size: 1.8rem; color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心計算引擎 (V26.5 深度邏輯) ---
def analyze_stock(ticker, spy_df):
    try:
        df = yf.download(ticker, period="6mo", auto_adjust=True, progress=False, threads=False)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        for m in [10, 20, 50]: df[f'MA{m}'] = df['Close'].rolling(window=m).mean()
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        
        hist_scores = []
        for i in range(-4, 1):
            sub = df.iloc[:len(df)+i] if i < 0 else df
            curr, prev = sub.iloc[-1], sub.iloc[-2]
            a1 = 10 if curr['MACD'] > 0 else (6 if curr['MACD'] > prev['MACD'] else 0)
            mas = [float(curr['MA10']), float(curr['MA20']), float(curr['MA50'])]
            comp = (np.std(mas) / np.mean(mas)) * 100
            a2 = 10 if comp < 1.5 else (8 if comp < 3.0 else 4)
            vol_r = curr['Volume'] / sub['Volume'].tail(10).mean()
            v_s = 5 if vol_r > 1.3 or vol_r < 0.5 else 0
            rs = (curr['Close']/sub.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close'])
            r_s = 5 if rs > 0.02 else (3 if rs > 0 else 0)
            hist_scores.append(round((a1*0.2) + (a2*0.4) + ((v_s + r_s)*0.4), 1))
            
        res = {"tk": ticker, "sc": hist_scores[-1], "bg": "#dcfce7" if hist_scores[-1] >= 9 else "#f1f5f9", 
               "a1": a1, "a1w": round(a1*0.2, 1), "a2": a2, "a2w": round(a2*0.4, 1), 
               "a3": (v_s + r_s), "a3w": round((v_s + r_s)*0.4, 1), "hist": hist_scores, 
               "cp": round(comp, 2), "pr": round(float(df.iloc[-1]['Close']), 2)}
        return res
    except: return None

# --- 3. 左側 Sidebar 查詢功能 ---
st.sidebar.header("🔍 即時個股查詢")
user_query = st.sidebar.text_input("輸入代號 (例如: OKLO)", value="")

spy_raw = yf.download("SPY", period="6mo", auto_adjust=True, progress=False, threads=False)
spy_df = get_indicators(spy_raw) if 'get_indicators' in locals() else spy_raw # 容錯處理

if user_query:
    st.sidebar.markdown("---")
    q_res = analyze_stock(user_query, spy_df)
    if q_res:
        st.sidebar.markdown(f'<div class="stock-row" style="background-color: {q_res["bg"]}; border-left: 6px solid #4f46e5;"><b>{q_res["tk"]} — ${q_res["pr"]}</b><div class="score-text">{q_res["sc"]} <small>分</small></div><hr><small>A1:{q_res["a1"]} | A2:{q_res["a2"]} | A3:{q_res["a3"]}</small><br><small>加權: {q_res["a1w"]}|{q_res["a2w"]}|{q_res["a3w"]}</small><br><small>AWI: {q_res["hist"]}</small></div>', unsafe_allow_html=True)

# --- 4. 右側 11 個大型板塊 (還原結構：一板塊多股票) ---
st.title("🛰️ Apex Ambush V32.5 指揮部")

# 定義 11 個板塊及其關聯股票 (模擬昨天版本)
SECTORS = {
    "AI 量子板塊": ["AAOI", "IONQ", "RGTI", "QUBT"],
    "巔峰埋伏標的": ["PL", "SOUN", "BBAI", "AISP"],
    "太空科技": ["LUNR", "RKLB", "SIDU", "ASTS"],
    "電動車龍頭": ["TSLA", "RIVN", "LCID"],
    "AI 算力核心": ["NVDA", "AMD", "AVGO", "SMCI"],
    "半導體製造": ["TSEM", "INTC", "TSM"],
    "高速傳輸": ["CRDO", "MRVL", "PANS"],
    "軟體龍頭": ["MSFT", "ORCL", "SNOW"],
    "搜尋與廣告": ["GOOGL", "AMZN", "BIDU"],
    "社交與元宇宙": ["META", "SNAP", "PINS"],
    "消費電子": ["AAPL", "SONY", "HPQ"]
}

# 渲染 11 個大型板塊
for sector_name, stocks in SECTORS.items():
    st.markdown(f'<div class="sector-card"><h3>📦 {sector_name}</h3>', unsafe_allow_html=True)
    cols = st.columns(2) # 每個大板塊內部用兩欄顯示股票
    for idx, ticker in enumerate(stocks):
        with cols[idx % 2]:
            res = analyze_stock(ticker, spy_df)
            if res:
                st.markdown(f'<div class="stock-row" style="background-color: {res["bg"]};"><div style="display: flex; justify-content: space-between;"><b>{res["tk"]} — ${res["pr"]}</b><span class="score-text">{res["sc"]}</span></div><hr><small>A1:{res["a1"]} | A2:{res['a2']} | A3:{res['a3']}</small><br><small>加權: {res["a1w"]} | {res["a2w"]} | {res["a3w"]}</small><br><small>5日 AWI: {res["hist"]}</small></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
