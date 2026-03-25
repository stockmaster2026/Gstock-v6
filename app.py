import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# --- 0. UI 配置 ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.5.3", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .sector-head { color: #44aaff; font-weight: bold; font-size: 1.3rem; margin: 30px 0 15px 0; border-left: 6px solid #44aaff; padding-left: 12px; }
    .stock-card {
        background-color: #1a1a1a; border: 2px solid #3d3d00;
        border-radius: 12px; padding: 22px; margin-bottom: 25px; min-height: 480px;
    }
    .active-border { border: 2px solid #ffff00; box-shadow: 0 0 20px rgba(255, 255, 0, 0.4); }
    .battle-score {
        background-color: #333300; color: #ffff00; border-radius: 10px;
        padding: 10px; text-align: center; font-weight: bold; border: 1px solid #ffff00; margin: 15px 0; font-size: 1.1rem;
    }
    .price-up { color: #00ff00; font-size: 1.8rem; font-weight: bold; }
    .price-down { color: #ff4b4b; font-size: 1.8rem; font-weight: bold; }
    .array-green { font-family: 'Courier New', monospace; color: #00ff00; font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 穩定數據引擎 (X-Ray 邏輯) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data_v32_5_3(ticker):
    try:
        # 防封鎖隨機延遲
        time.sleep(random.uniform(2.0, 3.5))
        data = yf.download(ticker, period="6mo", interval="1d", progress=False, timeout=10)
        if data.empty or len(data) < 30: return None
        
        close = data['Close'].ffill()
        vol = data['Volume'].ffill()
        
        # X1: Alignment (MACD 斜率先行修正)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        x1 = 10 if macd.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2] else (7 if hist.iloc[-1] > hist.iloc[-2] else 3)
        
        # X2: Anchoring (均線 3%~5% 糾結)
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 4)
        
        # X3: Activation (能量點火)
        v_avg = vol.rolling(10).mean().iloc[-1]
        x3 = 10 if vol.iloc[-1] > v_avg * 1.3 else (5 if vol.iloc[-1] < v_avg * 0.7 else 7)
        
        # AWI 綜合計算
        awi = round((x2 * 0.4 + x1 * 0.3 + x3 * 0.3), 1)
        weather = "🎆" if awi >= 9 else ("☀️" if awi >= 7 else ("☁️" if awi >= 5 else "🌫️"))
        
        return {"p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
                "awi": awi, "weather": weather, "x1": x1, "x2": x2, "x3": x3}
    except: return None

# --- 2. 11 大板塊 (每板塊精選 4 檔精英標的) ---
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
with st.sidebar:
    st.title("🕹️ 指揮部")
    main_tkr = st.text_input("🔍 偵察自選代碼", "PL").upper()
    if st.button("🚀 強制刷新"): st.cache_data.clear(); st.rerun()
    st.info("V32.5.3 精英 4 檔版")

st.title("🛡️ 雙軌指揮中心 V32.5.3")

for section, tickers in sectors.items():
    st.markdown(f'<div class="sector-head">{section}</div>', unsafe_allow_html=True)
    # 使用 4 列顯示，讓一排剛好放下 4 檔
    cols = st.columns(4)
    for idx, tkr in enumerate(tickers):
        with cols[idx]:
            data = fetch_data_v32_5_3(tkr)
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
                    <center><div style="color:#44aaff; font-weight:bold;">{"🔥 能量點火" if data['x3']==10 else "☀️ 縮量洗盤"}</div></center>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"📡 {tkr} 偵察中...")

