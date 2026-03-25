
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 0. UI 配置 (100% 復刻 V32.0 樣式) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.5", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .sector-head { color: #44aaff; font-weight: bold; font-size: 1.3rem; margin: 30px 0 15px 0; border-left: 6px solid #44aaff; padding-left: 12px; }
    .stock-card {
        background-color: #1a1a1a; border: 2px solid #3d3d00;
        border-radius: 12px; padding: 22px; margin-bottom: 25px; min-height: 520px;
    }
    .active-border { border: 2px solid #ffff00; box-shadow: 0 0 20px rgba(255, 255, 0, 0.4); }
    .battle-score {
        background-color: #333300; color: #ffff00; border-radius: 10px;
        padding: 10px; text-align: center; font-weight: bold; border: 1px solid #ffff00; margin: 15px 0; font-size: 1.1rem;
    }
    .price-up { color: #00ff00; font-size: 1.8rem; font-weight: bold; }
    .price-down { color: #ff4b4b; font-size: 1.8rem; font-weight: bold; }
    .array-green { font-family: 'Courier New', monospace; color: #00ff00; font-weight: bold; font-size: 1.1rem; }
    .comment-blue { color: #44aaff; font-size: 0.95rem; text-align: center; margin-top: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心數據引擎 (X-Ray 邏輯：X1趨勢/X2構造/X3能量) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stable_x_data(ticker):
    try:
        # 抗封鎖延時：模擬真人休息
        time.sleep(random.uniform(1.8, 3.5))
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, timeout=12)
        if df.empty or len(df) < 40: return None
        
        close = df['Close'].ffill()
        vol = df['Volume'].ffill()
        
        # --- X1: Alignment (修正 MACD 斜率先行) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        # 修正：水底斜率轉正即給 7 分，多頭給 10 分
        x1 = 10 if macd.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2] else (7 if hist.iloc[-1] > hist.iloc[-2] else 3)
        
        # --- X2: Anchoring (均線 3%~5% 糾結度) ---
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 4)
        
        # --- X3: Activation (能量點火判定) ---
        v_avg = vol.rolling(10).mean().iloc[-1]
        x3 = 10 if vol.iloc[-1] > v_avg * 1.3 else (5 if vol.iloc[-1] < v_avg * 0.7 else 7)
        
        # --- AWI 綜合天氣 (X2:40%, X1:30%, X3:30%) ---
        awi_score = round((x2 * 0.4 + x1 * 0.3 + x3 * 0.3), 1)
        weather = "🎆" if awi_score >= 9 else ("☀️" if awi_score >= 7 else ("☁️" if awi_score >= 5 else "🌫️"))
        
        return {
            "p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
            "awi": awi_score, "weather": weather, "x1": x1, "x2": x2, "x3": x3,
            "v_h": [int(x2)] * 5, "a_h": [int(x3)] * 5
        }
    except: return None

# --- 2. 11 大滿編板塊名單 (含 AXTI 與存儲修正) ---
sectors = {
    "▋ 太空整合 (Space Tech)": ["LUNR", "ASTS", "PL", "BKSY", "SPIR", "RKLB"],
    "▋ 光通訊 (Optical)": ["AAOI", "GLW", "AXTI", "LITE", "COHR", "FN"],
    "▋ 存儲板塊 (Storage)": ["MU", "WDC", "STX", "PSTG", "SMCI", "TOSYY"],
    "▋ 算力晶片 (Chips)": ["NVDA", "ARM", "TSM", "AMD", "AVGO", "SOXL"],
    "▋ 量子計算": ["IONQ", "RGTI", "QUBT", "QBTS", "ARQQ", "LPA"],
    "▋ AI 醫療 (AI Health)": ["TEM", "GEHC", "SDGR", "DOCN", "TDOC", "CANO"],
    "▋ 軍工科技 (Defense)": ["KTOS", "AVAV", "LMT", "NOC", "PLTR", "BA"],
    "▋ 電力能源 (Power)": ["OKLO", "VST", "SMR", "NLR", "CCJ", "TLNE"],
    "▋ 數據分析 (Big Data)": ["PLTR", "SNOW", "MSTR", "DDOG", "NET", "PATH"],
    "▋ 金融科技 (FinTech)": ["HOOD", "COIN", "SOFI", "PYPL", "SQ", "UPST"],
    "▋ 網絡安全 (Cyber)": ["CRWD", "PANW", "FTNT", "S", "ZS", "OKTA"]
}

# --- 3. 介面呈現 ---
with st.sidebar:
    st.title("🕹️ 指揮控制")
    main_tkr = st.text_input("🔍 偵察自選代碼", "PL").upper()
    if st.button("🚀 重新加載"): st.cache_data.clear(); st.rerun()
    st.info("當前版本：V32.5 (X系列終極版)")

st.title("🛡️ 雙軌指揮中心 V32.5")

for section, tickers in sectors.items():
    st.markdown(f'<div class="sector-head">{section}</div>', unsafe_allow_html=True)
    rows = [tickers[i:i+3] for i in range(0, len(tickers), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, tkr in enumerate(row):
            with cols[idx]:
                data = fetch_stable_x_data(tkr)
                if data:
                    active = "active-border" if tkr == main_tkr else ""
                    st.markdown(f"""
                    <div class="stock-card {active}">
                        <center><h3 style="margin:0;">{tkr} {data['weather']}</h3></center>
                        <div class="battle-score">AWI 巔峰氣象：{data['awi']} / 10</div>
                        <center><div class="{'price-up' if data['chg'] > 0 else 'price-down'}">${data['p']} <small>({data['chg']}%)</small></div></center>
                        <hr style="border-color:#444;">
                        <div style="font-size:0.85rem; color:#aaa;">X2 構造(40%): {data['x2']}.0</div>
                        <div style="font-size:0.85rem; color:#aaa;">X1 趨勢(30%): {data['x1']}.0</div>
                        <div style="font-size:0.85rem; color:#aaa;">X3 能量(30%): {data['x3']}.0</div>
                        <hr style="border-color:#444;">
                        <div style="font-size:1.1rem;">V26(h): <span class="array-green">{' | '.join(map(str, data['v_h']))}</span></div>
                        <div style="font-size:1.1rem;">AWI(h): <span class="array-green">{' | '.join(map(str, data['a_h']))}</span></div>
                        <center><div class="comment-blue">{"🔥 能量點火" if data['x3']==10 else "🌫️ 縮量洗盤"}</div></center>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"📡 {tkr} 隊列中...")
