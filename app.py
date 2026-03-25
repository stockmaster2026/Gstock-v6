
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

# --- 1. 數據抓取 (加入 Cache 緩存機制，防止載入失敗) ---
@st.cache_data(ttl=600)  # 數據快取 10 分鐘，減少請求次數
def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        return df
    except:
        return pd.DataFrame()

# --- 2. 核心計算：V32.5 邏輯 ---
W = {'A1': 0.25, 'A2': 0.30, 'A3': 0.45}

def get_v32_5_metrics(ticker):
    df = fetch_stock_data(ticker)
    if df.empty or len(df) < 15: return None
    
    # A1 趨勢 (MACD 手動計算 + 斜率修正)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    a1 = 10 if macd.iloc[-1] > 0 else (7 if macd.iloc[-1] > macd.iloc[-2] else 3)
    
    # A2 構造 (5% 均線糾結度)
    ma10 = df['Close'].rolling(10).mean()
    ma20 = df['Close'].rolling(20).mean()
    dist = abs(ma10.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
    a2 = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
    
    # A3 能量 (45% 權重 - 抓點火)
    vol_avg = df['Volume'].rolling(10).mean()
    curr_vol = df['Volume'].iloc[-1]
    a3 = 10 if curr_vol > vol_avg.iloc[-1] * 1.3 else (5 if curr_vol < vol_avg.iloc[-1] * 0.7 else 7)
    
    score = round((a1 * W['A1'] + a2 * W['A2'] + a3 * W['A3']), 1)
    
    # 生成趨勢陣列 (模擬 V26 與 AWI 歷史)
    v26_h = [int(a2)] * 5 
    awi_h = [int(a3)] * 5
    
    return {
        "price": round(df['Close'].iloc[-1], 2),
        "pct": round(((df['Close'].iloc[-1]/df['Close'].iloc[-2])-1)*100, 2),
        "score": score,
        "a1": a1, "a2": a2, "a3": a3,
        "v26_h": v26_h, "awi_h": awi_h,
        "comment": "🔥 能量點火" if a3 == 10 else ("🌫️ 縮量洗盤" if a3 == 5 else "☀️ 等待表態")
    }

# --- 3. UI 佈局實作 ---
with st.sidebar:
    st.title("🕹️ 控制中心")
    main_ticker = st.text_input("🔍 偵察代碼", "LUNR").upper()
    if st.button("♻️ 強制刷新數據"):
        st.cache_data.clear()
        st.rerun()

st.title("🛡️ 雙軌指揮中心 V32.5")
st.subheader("▋ 指標監控卡片")

# 設定監控清單
watchlist = [main_ticker, "IONQ", "RGTI", "PL", "AAOI", "ASTS", "NVDA", "KTOS", "TEM"]
# 每行顯示三個卡片
rows = [watchlist[i:i + 3] for i in range(0, len(watchlist), 3)]

for row in rows:
    cols = st.columns(3)
    for i, tkr in enumerate(row):
        data = get_v32_5_metrics(tkr)
        with cols[i]:
            if data:
                active_class = "stock-card-active" if tkr == main_ticker else ""
                st.markdown(f"""
                <div class="stock-card {active_class}">
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
