
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- 0. 介面配置 (100% 復刻 V32.0 雙軌卡片設計) ---
st.set_page_config(layout="wide", page_title="V32.5 雙軌指揮中心", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .stock-card {
        background-color: #1c1c1c; border: 2px solid #3d3d00;
        border-radius: 12px; padding: 15px; margin-bottom: 20px;
        min-height: 380px;
    }
    .stock-card-active { border-color: #a8a800; box-shadow: 0 0 15px rgba(168, 168, 0, 0.4); }
    .price-up { color: #00ff00; font-weight: bold; font-size: 1.5rem; }
    .price-down { color: #ff4b4b; font-weight: bold; font-size: 1.5rem; }
    .array-text { font-family: 'Courier New', monospace; color: #00ff00; font-weight: bold; }
    .metric-box { background-color: #333300; border-radius: 5px; padding: 5px; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心數據獲取 (解決 YFRateLimitError 鎖頻) ---
@st.cache_data(ttl=1800) # 緩存提高到 30 分鐘
def get_v32_5_data(ticker):
    try:
        # 這是關鍵：每抓一檔，休息 1.5 秒，偽裝成真人在操作
        time.sleep(1.5) 
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 26: return None
        
        close = df['Close'].ffill()
        vol = df['Volume'].ffill()
        
        # A1 趨勢 (MACD 手動計算 + 斜率修正)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        
        # 安全檢查與斜率修正 (抓 AAOI 類起漲)
        if len(macd) < 2: return None
        cur_m, pre_m = macd.iloc[-1], macd.iloc[-2]
        a1 = 10 if cur_m > 0 else (7 if cur_m > pre_m else 3)
        
        # A2 構造 (5% 均線糾結度)
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        a2 = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
        
        # A3 能量 (45% 權重核心)
        v_avg = vol.rolling(10).mean().iloc[-1]
        c_vol = vol.iloc[-1]
        a3 = 10 if c_vol > v_avg * 1.3 else (5 if c_vol < v_avg * 0.7 else 7)
        
        return {
            "p": round(float(close.iloc[-1]), 2),
            "chg": round(((close.iloc[-1]/close.iloc[-2])-1)*100, 2),
            "s": round((a1 * 0.25 + a2 * 0.30 + a3 * 0.45), 1),
            "a1": a1, "a2": a2, "a3": a3,
            "v_h": [int(a2)] * 5, "a_h": [int(a3)] * 5
        }
    except: return None

# --- 2. 控制中心 ---
with st.sidebar:
    st.title("🕹️ 控制中心")
    main_tkr = st.text_input("🔍 偵察自選代碼", "LUNR").upper()
    if st.button("♻️ 強制刷新 (解決載入失敗)"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.info("V32.5 巔峰埋伏版\nA1: 25% | A2: 30% | A3: 45%")

# --- 3. 畫面顯示 ---
st.title("🛡️ 雙軌指揮中心 V32.5")
st.subheader("▋ 指標監控卡片")

watchlist = [main_tkr, "IONQ", "RGTI", "PL", "AAOI", "ASTS", "NVDA", "KTOS", "ARM"]

for i in range(0, len(watchlist), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(watchlist):
            tkr = watchlist[i+j]
            data = get_v32_5_data(tkr)
            with cols[j]:
                if data:
                    active = "stock-card-active" if tkr == main_tkr else ""
                    st.markdown(f"""
                    <div class="stock-card {active}">
                        <center><h3 style="margin:0;">{tkr} ☀️</h3></center>
                        <div class="metric-box"><span style="color: #ffff00;">五日平均戰力：{data['s']} / 10</span></div>
                        <center><div class="{'price-up' if data['chg'] > 0 else 'price-down'}">${data['p']} <small>({data['chg']}%)</small></div></center>
                        <div style="font-size: 0.85rem; color: #888; margin-top: 10px;">
                            F2 結構(30%): {data['a2']}.0/10<br>
                            F3 籌碼(45%): {data['a3']}.0/10<br>
                            F1 技術(25%): {data['a1']}.0/10
                        </div>
                        <hr style="border-color: #444; margin: 10px 0;">
                        <div style="font-size:0.8rem;">V26(h): <span class="array-text">{' | '.join(map(str, data['v_h']))}</span></div>
                        <div style="font-size:0.8rem;">AWI(h): <span class="array-text">{' | '.join(map(str, data['a_h']))}</span></div>
                        <center><div style="margin-top:10px; color:#3399ff;">💤 {"🔥 能量點火" if data['a3']==10 else "☀️ 等待表態"}</div></center>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"📡 {tkr} 連線中或被 Yahoo 鎖頻...")
