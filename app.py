import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 0. UI 配置 (復刻 10:47 AM 極簡風格) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.10")

st.markdown("""
    <style>
    .sector-title { font-size: 1.6rem; font-weight: bold; color: #44aaff; margin: 30px 0 15px 0; border-left: 10px solid #44aaff; padding-left: 15px; }
    .metric-card { border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px; text-align: center; }
    .pink-zone { background-color: rgba(255, 182, 193, 0.08) !important; border: 1px solid rgba(255, 0, 0, 0.15) !important; }
    .ticker-name { font-size: 1.5rem; font-weight: bold; opacity: 0.9; }
    .price-large { font-size: 2.8rem; font-weight: bold; margin: 10px 0; }
    .awi-badge { background-color: rgba(255, 255, 0, 0.1); color: #ffd700; border: 1px solid #ffd700; border-radius: 5px; padding: 3px 12px; font-size: 1rem; font-weight: bold; }
    .data-row { font-family: 'Courier New', monospace; font-size: 0.9rem; margin-top: 15px; color: #888; }
    .advice-box { padding: 8px; border-radius: 5px; margin-top: 12px; font-size: 0.95rem; font-weight: bold; }
    .advice-safe { background-color: rgba(0, 50, 0, 0.2); color: #00ff00; }
    .advice-warn { background-color: rgba(50, 0, 0, 0.2); color: #ff8888; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 原生強效數據引擎 (不依賴 tvDatafeed) ---
@st.cache_data(ttl=600)
def fetch_analysis(ticker):
    try:
        # 使用原生 requests 抓取公開數據源 (模擬 TradingView 邏輯)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers)
        data = resp.json()['chart']['result'][0]
        
        close = pd.Series(data['indicators']['quote'][0]['close']).ffill()
        vol = pd.Series(data['indicators']['quote'][0]['volume']).ffill()
        open_p = pd.Series(data['indicators']['quote'][0]['open']).ffill()

        # X2 構造 (⚓ 定錨)
        ma10, ma20 = close.rolling(10).mean().iloc[-1], close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        is_anchored = dist < 0.03
        x2 = 10 if is_anchored else (7 if dist < 0.05 else 3)
        
        # X1 趨勢 (零軸判定)
        ema12, ema26 = close.ewm(span=12).mean(), close.ewm(span=26).mean()
        macd = ema12 - ema26
        is_on_zero = macd.iloc[-1] > 0
        x1 = 10 if is_on_zero else (6 if macd.iloc[-1] > macd.iloc[-2] else 0)
        
        # X3 能量 (🔥 點火)
        v_avg = vol.rolling(10).mean().iloc[-1]
        is_fired = vol.iloc[-1] > v_avg * 1.3 and close.iloc[-1] > open_p.iloc[-1]
        x3 = 10 if is_fired else 5
        
        awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
        weather = "☀️" if awi >= 7 else "☁️"
        icon_str = ("⚓" if is_anchored else "") + ("🔥" if is_fired else "")
        
        advice = "🚀 順風點火" if (is_on_zero and is_fired) else ("🌫️ 潛伏偵測" if not is_on_zero and (is_anchored or is_fired) else "☁️ 盤整中")
        adv_class = "advice-safe" if is_on_zero else "advice-warn"

        return {"p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
                "awi": awi, "x1": x1, "x2": x2, "x3": x3, "weather": weather, 
                "advice": advice, "adv_class": adv_class, "is_pink": not is_on_zero, "icons": icon_str}
    except: return None

# --- 2. 側邊欄 ---
st.sidebar.header("📡 戰略輸入")
input_data = st.sidebar.text_input("新增自選代碼", "LUNR, IONQ, PLTR")
customs = [t.strip().upper() for t in input_data.split(",") if t.strip()]

# --- 3. 板塊與渲染 ---
sectors = {"太空技術": ["LUNR", "PL", "ASTS", "RKLB"], "光通訊": ["AAOI", "AXTI", "GLW"], "自選": customs}
st.title("🛡️ 雙軌指揮中心 V32.9.10")

for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(6)
    for i, tkr in enumerate(tkrs):
        with cols[i % 6]:
            d = fetch_analysis(tkr)
            if d:
                color = "#ff4b4b" if d['chg'] >= 0 else "#00ff00"
                card_class = "metric-card pink-zone" if d['is_pink'] else "metric-card"
                st.markdown(f"""<div class="{card_class}">
                    <div class="ticker-name">{tkr} {d['weather']} {d['icons']}</div>
                    <div class="awi-badge">AWI: {d['awi']}</div>
                    <div class="price-large" style="color:{color};">${d['p']}</div>
                    <div class="data-row">X2:{d['x2']} | X1:{d['x1']} | X3:{d['x3']}</div>
                    <div class="advice-box {d['adv_class']}">{d['advice']}</div>
                </div>""", unsafe_allow_html=True)

