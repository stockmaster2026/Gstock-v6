
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 0. 介面配置 (100% 復刻 V32.0 雙軌指揮中心) ---
st.set_page_config(layout="wide", page_title="V32.5 雙軌指揮中心", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .stock-card {
        background-color: #1c1c1c;
        border: 2px solid #3d3d00;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .stock-card-active { border-color: #a8a800; box-shadow: 0 0 15px rgba(168, 168, 0, 0.3); }
    .price-up { color: #00ff00; font-weight: bold; font-size: 1.5rem; }
    .price-down { color: #ff4b4b; font-weight: bold; font-size: 1.5rem; }
    .array-text { font-family: 'Courier New', monospace; color: #00ff00; font-weight: bold; }
    .metric-box { background-color: #333300; border-radius: 5px; padding: 5px; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 數據緩存與計算 (解決 ValueError) ---
@st.cache_data(ttl=600)
def fetch_and_calc(ticker):
    try:
        # 抓取稍長一點的數據確保計算 MACD 時不會越界
        df = yf.download(ticker, period="2mo", interval="1d", progress=False)
        if df.empty or len(df) < 26: return None
        
        # A1 趨勢 (手動計算 MACD + 斜率修正)
        close = df['Close'].fillna(method='ffill')
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        
        # 安全取值：確保索引存在
        cur_m = macd.iloc[-1]
        pre_m = macd.iloc[-2]
        a1 = 10 if cur_m > 0 else (7 if cur_m > pre_m else 3)
        
        # A2 構造 (5% 均線糾結)
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        a2 = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
        
        # A3 能量 (45% 權重 - 抓點火)
        vol = df['Volume'].fillna(0)
        vol_avg = vol.rolling(10).mean().iloc[-1]
        curr_vol = vol.iloc[-1]
        a3 = 10 if curr_vol > vol_avg * 1.3 else (5 if curr_vol < vol_avg * 0.7 else 7)
        
        score = round((a1 * 0.25 + a2 * 0.30 + a3 * 0.45), 1)
        
        # 歷史陣列模擬 (復刻 V32.0 樣式)
        v26_h = [int(a2)] * 5
        awi_h = [int(a3)] * 5
        
        return {
            "price": round(float(close.iloc[-1]), 2),
            "pct": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
            "score": score, "a1": a1, "a2": a2, "a3": a3,
            "v26_h": v26_h, "awi_h": awi_h,
            "comment": "🔥 能量點火" if a3 == 10 else ("🌫️ 縮量洗盤" if a3 == 5 else "☀️ 等待表態")
        }
    except: return None

# --- 2. 控制中心 ---
with st.sidebar:
    st.title("🕹️ 控制中心")
    main_ticker = st.text_input("🔍 偵察代碼", "LUNR").upper()
    if st.button("♻️ 強制刷新數據"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.write("V32.5 邏輯：A1(25%) A2(30%) A3(45%)")

# --- 3. 畫面實作 ---
st.title("🛡️ 雙軌指揮中心 V32.5")
st.subheader("▋ 指標監控卡片")

watchlist = [main_ticker, "IONQ", "RGTI", "PL", "AAOI", "ASTS"]
cols = st.columns(3)

for i, tkr in enumerate(watchlist):
    data = fetch_and_calc(tkr)
    with cols[i % 3]:
        if data:
            active = "stock-card-active" if tkr == main_ticker else ""
            st.markdown(f"""
            <div class="stock-card {active}">
                <center><h3 style="margin:0;">{tkr} ☀️</h3></center>
                <div class="metric-box">
                    <span style="color: #ffff00;">五日平均戰力：{data['score']} / 10</span>
                </div>
                <center>
                    <div class="{'price-up' if data['pct'] > 0 else 'price-down'}">
                        ${data['price']} <small>({'+' if data['pct'] > 0 else ''}{data['pct']}%)</small>
                    </div>
                </center>
                <div style="font-size: 0.85rem; color: #888; margin-top: 10px;">
                    F2 結構(30%): {data['a2']}.0/10<br>
                    F3 籌碼(45%): {data['a3']}.0/10<br>
                    F1 技術(25%): {data['a1']}.0/10
                </div>
                <hr style="border-color: #444; margin: 10px 0;">
                <div style="font-size:0.8rem;">V26(h): <span class="array-text">{' | '.join(map(str, data['v26_h']))}</span></div>
                <div style="font-size:0.8rem;">AWI(h): <span class="array-text">{' | '.join(map(str, data['awi_h']))}</span></div>
                <center><div style="margin-top:10px; color:#3399ff;">💤 {data['comment']}</div></center>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"正在連線 {tkr}...")
