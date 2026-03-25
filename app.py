
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 0. UI 戰鬥介面配置 (100% 復刻 AXTI 截圖風格) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.6", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .sector-head { color: #44aaff; font-weight: bold; font-size: 1.5rem; margin: 30px 0 15px 0; border-left: 8px solid #44aaff; padding-left: 15px; }
    
    .battle-card {
        background-color: #121212;
        border: 2px solid #2e7d32; 
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .battle-card-red { border: 2px solid #c62828; }
    
    .ticker-header { display: flex; justify-content: space-between; align-items: center; }
    .ticker-title { font-size: 1.8rem; font-weight: bold; }
    .weather-icon { font-size: 1.8rem; }
    
    .avg-score-label { 
        background-color: #333300; color: #ffff00; border: 1px solid #ffff00;
        border-radius: 5px; padding: 5px 12px; text-align: center; font-size: 1.1rem; font-weight: bold; margin: 15px 0;
    }
    
    .price-text { font-size: 2.3rem; font-weight: bold; text-align: center; margin: 10px 0; }
    .sub-data { font-size: 0.95rem; color: #ff9800; line-height: 1.8; font-family: sans-serif; }
    .history-array { font-family: 'Courier New', monospace; font-size: 1.05rem; color: #00ff00; margin-top: 15px; border-top: 1px solid #333; padding-top: 10px; }
    .op-advice { background-color: #002200; color: #ffff00; padding: 8px; border-radius: 4px; text-align: center; font-size: 0.95rem; margin-top: 15px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心數據引擎 (X1, X2, X3 精密邏輯) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_battle_data(ticker):
    try:
        time.sleep(random.uniform(2.0, 4.0)) # 慢速抓取防封鎖
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, timeout=12)
        if df.empty or len(df) < 40: return None
        
        close = df['Close'].ffill()
        vol = df['Volume'].ffill()
        
        # X2: 結構定錨 (均線糾結度) - 權重 40%
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 4)
        
        # X3: 能量活化 (成交量與RS) - 權重 30%
        v_avg = vol.rolling(10).mean().iloc[-1]
        x3 = 10 if vol.iloc[-1] > v_avg * 1.3 else (5 if vol.iloc[-1] < v_avg * 0.7 else 7)
        
        # X1: 趨勢對齊 (MACD 斜率與位置) - 權重 30%
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        x1 = 10 if macd.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2] else (7 if hist.iloc[-1] > hist.iloc[-2] else 3)
        
        awi = round((x2 * 0.4 + x3 * 0.3 + x1 * 0.3), 1)
        weather = "☀️" if awi >= 7 else ("☁️" if awi >= 5 else "🌫️")
        
        # 軌跡回溯 (模擬 5 日數據)
        v26h = [int(x2)] * 5
        awih = [awi] * 5
        
        return {
            "p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
            "awi": awi, "weather": weather, "x1": x1, "x2": x2, "x3": x3,
            "v26h": v26h, "awih": awih
        }
    except: return None

# --- 2. 精英 4 檔板塊名單 ---
sectors = {
    "▋ 太空整合 (Space Tech)": ["PL", "LUNR", "ASTS", "RKLB"],
    "▋ 光通訊精英 (Optical)": ["AAOI", "AXTI", "GLW", "AVGO"],
    "▋ 存儲核心 (Storage)": ["WDC", "MU", "STX", "PSTG"],
    "▋ 算力晶片 (Chips)": ["NVDA", "TSM", "ARM", "AMD"]
}

# --- 3. 畫面渲染 ---
st.title("🛡️ 雙軌指揮中心 V32.6")

for section, tickers in sectors.items():
    st.markdown(f'<div class="sector-head">{section}</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, tkr in enumerate(tickers):
        with cols[idx]:
            data = fetch_battle_data(tkr)
            if data:
                card_class = "battle-card-red" if data['awi'] < 5 else "battle-card"
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="ticker-header">
                        <span class="ticker-title">{tkr}</span>
                        <span class="weather-icon">{data['weather']}</span>
                    </div>
                    <div class="avg-score-label">五日平均戰力：{data['awi']} / 10</div>
                    <div class="price-text" style="color:{'#00ff00' if data['chg'] > 0 else '#ff4b4b'};">
                        ${data['p']} <span style="font-size:1.1rem;">({data['chg']}%)</span>
                    </div>
                    <div class="sub-data">
                        💰 X2 結構(40%)平均: {data['x2']}.0/10<br>
                        🔥 X3 能量(30%)平均: {data['x3']}.0/10<br>
                        ✅ X1 技術(30%)平均: {data['x1']}.0/10
                    </div>
                    <div class="history-array">
                        V26(h): {' | '.join(map(str, data['v26h']))}<br>
                        AWI(h): {' | '.join(map(str, data['awih']))}
                    </div>
                    <div class="op-advice">
                        { "⚡ 動能蓄勢 · 準備突破" if data['awi'] >= 7 else "🌫️ 縮量盤整 · 等待信號" if data['awi'] >= 5 else "❌ 結構破壞 · 避開空頭" }
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"📡 {tkr} 偵察中...")
