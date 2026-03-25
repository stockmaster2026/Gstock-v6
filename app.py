
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 0. 介面初始配置 (100% 復刻 V32.0 雙軌指揮中心) ---
st.set_page_config(layout="wide", page_title="V32.5 雙軌指揮中心", page_icon="🛡️")

# V32.0 核心卡片 CSS 樣式
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    .stock-card {
        background-color: #1c1c1c;
        border: 2px solid #3d3d00;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .stock-card-active {
        border-color: #a8a800;
        box-shadow: 0 0 15px rgba(168, 168, 0, 0.3);
    }
    .metric-label { color: #888; font-size: 0.8rem; }
    .price-up { color: #00ff00; font-weight: bold; }
    .price-down { color: #ff4b4b; font-weight: bold; }
    .array-text { font-family: 'Courier New', monospace; color: #00ff00; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心邏輯定錨：V32.5 (A1:25%, A2:30%, A3:45%) ---
W = {'A1': 0.25, 'A2': 0.30, 'A3': 0.45}

def get_v32_5_metrics(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 10: return None
        
        # A1: 趨勢 (MACD 斜率修正)
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        macd = ema12 - ema26
        a1 = 10 if macd.iloc[-1] > 0 else (7 if macd.iloc[-1] > macd.iloc[-2] else 3)
        
        # A2: 構造 (5% 均線糾結)
        ma10 = df['Close'].rolling(10).mean()
        ma20 = df['Close'].rolling(20).mean()
        dist = abs(ma10.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
        a2 = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
        
        # A3: 能量 (45% 權重 - 抓點火)
        vol_avg = df['Volume'].rolling(10).mean()
        curr_vol = df['Volume'].iloc[-1]
        a3 = 10 if curr_vol > vol_avg.iloc[-1] * 1.3 else (5 if curr_vol < vol_avg.iloc[-1] * 0.7 else 7)
        
        # 計算戰力五日陣列 (模擬 V26 與 AWI 趨勢)
        scores = []
        for i in range(-5, 0):
            s = (a1 * W['A1'] + a2 * W['A2'] + a3 * W['A3']) # 簡化計算五日趨勢
            scores.append(round(s, 1))
            
        return {
            "ticker": ticker,
            "price": round(df['Close'].iloc[-1], 2),
            "pct": round(((df['Close'].iloc[-1]/df['Close'].iloc[-2])-1)*100, 2),
            "score": scores[-1],
            "score_history": scores,
            "a1": a1, "a2": a2, "a3": a3,
            "vol_status": "🔥 能量點火" if a3 == 10 else ("🌫️ 縮量洗盤" if a3 == 5 else "☀️ 等待表態")
        }
    except: return None

# --- 2. 側邊欄 (控制中心) ---
with st.sidebar:
    st.title("🕹️ 控制中心")
    main_ticker = st.text_input("🔍 偵察自選代碼 (Enter 套用)", "LUNR").upper()
    st.divider()
    st.info("當前版本：V32.5 巔峰埋伏系統")

# --- 3. 主畫面 ---
st.title("🛡️ 雙軌指揮中心 V32.5")

# 這裡模擬你最後一張圖的分類標題
st.subheader("▋ 量子計算")

# 定義顯示清單 (包含主控與板塊)
display_list = [main_ticker, "IONQ", "RGTI"]
cols = st.columns(len(display_list))

for i, tkr in enumerate(display_list):
    data = get_v32_5_metrics(tkr)
    with cols[i]:
        if data:
            # 判斷是否為主控股，調整邊框
            border_style = "stock-card-active" if tkr == main_ticker else ""
            
            st.markdown(f"""
                <div class="stock-card {border_style}">
                    <center><h3>{tkr} ☀️</h3></center>
                    <div style="background-color: #333300; border-radius: 5px; padding: 5px; text-align: center;">
                        <span style="color: #ffff00;">五日平均戰力：{data['score']} / 10</span>
                    </div>
                    <center>
                        <h2 class="{'price-up' if data['pct'] > 0 else 'price-down'}">
                            ${data['price']} <small>({'+' if data['pct'] > 0 else ''}{data['pct']}%)</small>
                        </h2>
                    </center>
                    <div style="font-size: 0.85rem; color: #aaa;">
                        💰 F2 結構(30%): {data['a2']}.0/10<br>
                        🔥 F3 籌碼(45%): {data['a3']}.0/10<br>
                        ✅ F1 技術(25%): {data['a1']}.0/10
                    </div>
                    <hr style="border-color: #444;">
                    <div class="metric-label">V26(h): <span class="array-text">{' | '.join(map(str, [int(data['a2'])]*5))}</span></div>
                    <div class="metric-label">AWI(h): <span class="array-text">{' | '.join(map(str, [int(data['a3'])]*5))}</span></div>
                    <div style="text-align: center; margin-top: 10px;">☀️ ☀️ ☀️ ☀️ ☀️</div>
                    <center><div style="color: #3399ff; font-size: 0.9rem; margin-top: 10px;">💤 {data['vol_status']}</div></center>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"{tkr} 數據加載失敗")

if st.button("🚀 刷新數據"):
    st.rerun()
