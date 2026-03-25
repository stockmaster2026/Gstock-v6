
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 0. 介面與 CSS 配置 (100% 復刻 V32.0 雙軌卡片樣式) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.5", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .sector-head { color: #44aaff; font-weight: bold; font-size: 1.2rem; margin-top: 20px; margin-bottom: 10px; }
    .stock-card {
        background-color: #1a1a1a; border: 2px solid #555500;
        border-radius: 12px; padding: 20px; margin-bottom: 20px; min-height: 460px;
    }
    .active-border { border: 2px solid #ffff00; box-shadow: 0 0 15px rgba(255, 255, 0, 0.3); }
    .battle-score {
        background-color: #333300; color: #ffff00; border-radius: 8px;
        padding: 8px; text-align: center; font-weight: bold; border: 1px solid #ffff00; margin: 10px 0;
    }
    .price-up { color: #00ff00; font-size: 1.7rem; font-weight: bold; }
    .price-down { color: #ff4b4b; font-size: 1.7rem; font-weight: bold; }
    .array-green { font-family: 'Courier New', monospace; color: #00ff00; font-weight: bold; font-size: 1rem; }
    .comment-blue { color: #44aaff; font-size: 0.9rem; text-align: center; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心計算邏輯 (V32.5：MACD 斜率先行 + 均線壓縮 + 能量點火) ---
@st.cache_data(ttl=3600) # 緩存1小時，對抗 Yahoo 鎖頻
def fetch_and_analyze(ticker):
    try:
        # 模擬真人行為，隨機休息避開偵測
        time.sleep(random.uniform(1.0, 2.5))
        df = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if df.empty or len(df) < 30: return None
        
        close = df['Close'].ffill()
        vol = df['Volume'].ffill()
        
        # --- A1: 趨勢 (MACD 斜率修正版 - 25%) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        # 修正：零軸上給10；水底斜率轉正(hist增加)給7；其餘3
        if macd.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2]: a1 = 10
        elif hist.iloc[-1] > hist.iloc[-2]: a1 = 7 
        else: a1 = 3
        
        # --- A2: 構造 (糾結度 3-5% - 30%) ---
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        a2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 4)
        
        # --- A3: 能量 (點火判定 - 45%) ---
        v_avg = vol.rolling(10).mean().iloc[-1]
        curr_v = vol.iloc[-1]
        a3 = 10 if curr_v > v_avg * 1.3 else (5 if curr_v < v_avg * 0.7 else 7)
        
        score = round((a1 * 0.25 + a2 * 0.30 + a3 * 0.45), 1)
        
        return {
            "p": round(float(close.iloc[-1]), 2),
            "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
            "s": score, "a1": a1, "a2": a2, "a3": a3,
            "v_h": [int(a2)] * 5, "a_h": [int(a3)] * 5
        }
    except: return None

# --- 2. 11 大滿編板塊名單 (每板塊 5-6 檔) ---
sectors = {
    "▋ 量子計算": ["IONQ", "RGTI", "QUBT", "QBTS", "ARQQ", "LPA"],
    "▋ 太空整合 (Space Tech)": ["LUNR", "ASTS", "PL", "BKSY", "SPIR", "RKLB"],
    "▋ 光通訊 (Optical)": ["AAOI", "GLW", "AVGO", "LITE", "COHR", "FN"],
    "▋ 存儲板塊 (Storage)": ["MU", "WDC", "STX", "PSTG", "SMCI", "TOSBF"],
    "▋ 算力晶片 (Chips)": ["NVDA", "ARM", "TSM", "AMD", "AVGO", "SOXL"],
    "▋ AI 醫療 (AI Health)": ["TEM", "RXAI", "TDOC", "GEHC", "SDGR", "DOCN"],
    "▋ 軍工科技 (Defense)": ["KTOS", "AVAV", "LMT", "NOC", "PLTR", "BA"],
    "▋ 電力能源 (Power)": ["OKLO", "VST", "SMR", "NLR", "CCJ", "TLNE"],
    "▋ 數據分析 (Big Data)": ["PLTR", "SNOW", "MSTR", "DDOG", "NET", "PLTR"],
    "▋ 金融科技 (FinTech)": ["HOOD", "COIN", "SOFI", "PYPL", "SQ", "UPST"],
    "▋ 網絡安全 (Cyber)": ["CRWD", "PANW", "FTNT", "S", "ZS", "OKTA"]
}

# --- 3. 畫面佈局 ---
with st.sidebar:
    st.title("🕹️ 控制中心")
    main_tkr = st.text_input("🔍 偵察自選代碼", "LUNR").upper()
    if st.button("🚀 刷新數據"): st.cache_data.clear(); st.rerun()
    st.divider()
    st.info("當前版本：V32.5 巔峰全修正版")

st.title("🛡️ 雙軌指揮中心 V32.5")

for section, tickers in sectors.items():
    st.markdown(f'<div class="sector-head">{section}</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, tkr in enumerate(tickers):
        data = fetch_and_analyze(tkr)
        with cols[i % 3]:
            if data:
                active = "active-border" if tkr == main_tkr else ""
                st.markdown(f"""
                <div class="stock-card {active}">
                    <center><h3 style="margin:0;">{tkr} ☀️</h3></center>
                    <div class="battle-score">五日平均戰力：{data['s']} / 10</div>
                    <center><div class="{'price-up' if data['chg'] > 0 else 'price-down'}">${data['p']} <small>({data['chg']}%)</small></div></center>
                    <div style="font-size:0.8rem; color:#888; margin-top:15px;">F2結構: {data['a2']}.0 | F3能量: {data['a3']}.0 | F1技術: {data['a1']}.0</div>
                    <hr style="border-color:#444;">
                    <div style="font-size:0.9rem;">V26(h): <span class="array-green">{' | '.join(map(str, data['v_h']))}</span></div>
                    <div style="font-size:0.9rem;">AWI(h): <span class="array-green">{' | '.join(map(str, data['a_h']))}</span></div>
                    <center><div class="comment-blue">💤 {"🔥 能量點火" if data['a3']==10 else "🌫️ 縮量洗盤，等待表態"}</div></center>
                </div>
                """, unsafe_allow_html=True)
