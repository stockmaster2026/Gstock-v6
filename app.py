import streamlit as st
import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval

# --- 0. UI 戰略介面 (隨系統自動切換深淺色) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.9")

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

# --- 1. TradingView 數據引擎 ---
@st.cache_resource
def init_tv(): return TvDatafeed()
tv = init_tv()

def fetch_analysis(ticker):
    try:
        df = tv.get_hist(symbol=ticker, exchange='NASDAQ', interval=Interval.in_daily, n_bars=50)
        if df is None: df = tv.get_hist(symbol=ticker, exchange='NYSE', interval=Interval.in_daily, n_bars=50)
        
        close, vol, open_p = df['close'], df['volume'], df['open']
        ma10, ma20 = close.rolling(10).mean().iloc[-1], close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        is_anchored = dist < 0.03
        x2 = 10 if is_anchored else (7 if dist < 0.05 else 3)
        
        ema12, ema26 = close.ewm(span=12).mean(), close.ewm(span=26).mean()
        macd = ema12 - ema26
        is_on_zero = macd.iloc[-1] > 0
        x1 = 10 if is_on_zero else (6 if macd.iloc[-1] > macd.iloc[-2] else 0)
        
        v_avg = vol.rolling(10).mean().iloc[-1]
        is_fired = vol.iloc[-1] > v_avg * 1.3 and close.iloc[-1] > open_p.iloc[-1]
        x3 = 10 if is_fired else 5
        
        awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
        weather = "🎆" if awi >= 9 else ("☀️" if awi >= 7 else ("☁️" if awi >= 5 else "🌫️"))
        icon_str = ("⚓" if is_anchored else "") + ("🔥" if is_fired else "")
        
        if is_on_zero:
            advice = "🚀 順風攻擊：多頭結構對齊" if is_fired else "⚓ 結構穩健：等待發動"
            adv_class = "advice-safe"
        else:
            advice = "🌫️ 潛伏偵測：低位買入痕跡" if (is_anchored or is_fired) else "🚨 弱勢區域：建議觀望"
            adv_class = "advice-warn"

        return {"p": round(float(close.iloc[-1]), 2), "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
                "awi": awi, "x1": x1, "x2": x2, "x3": x3, "weather": weather, 
                "advice": advice, "adv_class": adv_class, "is_pink": not is_on_zero, "icons": icon_str}
    except: return None

# --- 2. 側邊欄 ---
st.sidebar.header("📡 戰略輸入")
input_data = st.sidebar.text_input("輸入自選代碼 (如: LUNR, PI)", "LUNR, IONQ, AAOI")
customs = [t.strip().upper() for t in input_data.split(",") if t.strip()]

# --- 3. 板塊 ---
sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB", "KTOS"],
    "▋ 光通訊核心": ["AAOI", "AXTI", "GLW", "AVGO", "LITE"],
    "▋ 自選觀察": customs
}

# --- 4. 渲染 ---
st.title("🛡️ 雙軌指揮中心 V32.9.9")
for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(tkrs), 6))
    for i, tkr in enumerate(tkrs):
        with cols[i % 6]:
            d = fetch_analysis(tkr)
            if d:
                color = "#ff4b4b" if d['chg'] >= 0 else "#00ff00"
                card_class = "metric-card pink-zone" if d['is_pink'] else "metric-card"
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="ticker-name">{tkr} {d['weather']} {d['icons']}</div>
                    <div class="awi-badge">AWI: {d['awi']}</div>
                    <div class="price-large" style="color:{color};">${d['p']}</div>
                    <div class="data-row">X2:{d['x2']} | X1:{d['x1']} | X3:{d['x3']}</div>
                    <div class="advice-box {d['adv_class']}">{d['advice']}</div>
                </div>
                """, unsafe_allow_html=True)

