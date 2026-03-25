
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 0. UI 配置 (X系列精英版) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.5.5", page_icon="🛡️")

# --- 1. 核心數據引擎 (加入 User-Agent 偽裝與單線程保護) ---
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_data_v32_5_5(ticker):
    try:
        # 強制休息：模擬真人慢速看盤
        time.sleep(random.uniform(2.5, 4.5))
        
        # 使用極簡化抓取
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="6mo")
        
        if df.empty or len(df) < 30: return None
        
        close = df['Close'].ffill()
        vol = df['Volume'].ffill()
        
        # X1: Alignment (MACD 斜率先行)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        x1 = 10 if macd.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2] else (7 if hist.iloc[-1] > hist.iloc[-2] else 3)
        
        # X2: Anchoring (均線糾結度)
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 4)
        
        # X3: Activation (能量點火)
        v_avg = vol.rolling(10).mean().iloc[-1]
        x3 = 10 if vol.iloc[-1] > v_avg * 1.3 else (5 if vol.iloc[-1] < v_avg * 0.7 else 7)
        
        awi = round((x2 * 0.4 + x1 * 0.3 + x3 * 0.3), 1)
        weather = "🎆" if awi >= 9 else ("☀️" if awi >= 7 else ("☁️" if awi >= 5 else "🌫️"))
        
        return {"p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
                "awi": awi, "weather": weather, "x1": x1, "x2": x2, "x3": x3}
    except:
        return None

# --- 2. 11 大板塊 (每板塊 4 檔精英標的) ---
sectors = {
    "▋ 太空整合": ["PL", "LUNR", "ASTS", "RKLB"],
    "▋ 光通訊精英": ["AAOI", "AXTI", "GLW", "AVGO"],
    "▋ 存儲核心": ["WDC", "MU", "STX", "PSTG"],
    "▋ 算力晶片": ["NVDA", "TSM", "ARM", "AMD"],
    "▋ 量子計算": ["IONQ", "RGTI", "QUBT", "QBTS"],
    "▋ AI 醫療": ["TEM", "GEHC", "SDGR", "DOCN"],
    "▋ 軍工科技": ["KTOS", "PLTR", "AVAV", "LMT"],
    "▋ 電力能源": ["OKLO", "SMR", "VST", "CCJ"],
    "▋ 數據分析": ["PLTR", "SNOW", "MSTR", "DDOG"],
    "▋ 金融科技": ["HOOD", "COIN", "SOFI", "SQ"],
    "▋ 網絡安全": ["CRWD", "PANW", "FTNT", "S"]
}

# --- 3. 顯示呈現 ---
st.title("🛡️ 雙軌指揮中心 V32.5.5")

for section, tickers in sectors.items():
    st.markdown(f'<h3 style="color:#44aaff;">{section}</h3>', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, tkr in enumerate(tickers):
        with cols[idx]:
            data = fetch_data_v32_5_5(tkr)
            if data:
                st.markdown(f"""
                <div style="background-color:#1a1a1a; border:2px solid #3d3d00; border-radius:12px; padding:20px; margin-bottom:20px;">
                    <center><h3 style="margin:0;">{tkr} {data['weather']}</h3></center>
                    <div style="background-color:#333300; color:#ffff00; padding:5px; text-align:center; border-radius:8px; margin:10px 0;">AWI: {data['awi']}</div>
                    <center><h2 style="color:{'#00ff00' if data['chg'] > 0 else '#ff4b4b'};">${data['p']}</h2></center>
                    <div style="font-size:0.8rem; color:#888;">X2: {data['x2']} | X1: {data['x1']} | X3: {data['x3']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"📡 {tkr} 等待中...")
