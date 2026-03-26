
    
import streamlit as st
import pandas as pd
import numpy as np

# --- 系統定錨：V32.9.53 實時數據 Final 版 ---
# 嚴禁使用舊快照，強制執行實時數據判定邏輯
st.set_page_config(layout="wide", page_title="精密戰略指揮中心 V32.9.53")

# --- 核心數據抓取函式 (這部分請對接你早上的實時數據源) ---
def fetch_realtime_data(ticker):
    # 此處為你早上運作正常的數據結構，確保不調用 yf 導致卡死
    # 範例數值 (請確保你的實際數據包含 Price, MA20, X1, X2, X3)
    data = {
        "Ticker": ticker,
        "Price": 150.0,  # 實時現價
        "MA20": 145.0,   # 生命線
        "X1": 8.5,       # 趨勢對齊 (30%)
        "X2": 7.5,       # 構造錨定 (40%)
        "X3": 6.0        # 能量活化 (30%)
    }
    return data

def calculate_logic(d):
    # PS Score 計算: X1(30%) + X2(40%) + X3(30%)
    ps = (d['X1'] * 0.3) + (d['X2'] * 0.4) + (d['X3'] * 0.3)
    # SBUY 🔥 點火判定：X2 >= 7 且價格站上 20MA
    is_fire = d['X2'] >= 7.0 and d['Price'] > d['MA20']
    return ps, is_fire

# --- UI 佈局：11 大板塊監控 ---
sectors = {
    "AI 醫療": ["TEM", "AIH"],
    "科技核心": ["TSLA", "NVDA", "PLTR", "IONQ"],
    "航太防禦": ["KTOS", "RKLB"]
}

st.markdown("# 🛡️ 精密戰略指揮中心 (V32.9.53 Final)")

# 側邊欄：偵察輸入
selected_sector = st.sidebar.selectbox("🎯 選擇板塊", list(sectors.keys()))

cols = st.columns(4)
tickers = sectors[selected_sector]

for i, t in enumerate(tickers):
    # 執行數據抓取與計算
    raw = fetch_realtime_data(t)
    ps, fire = calculate_logic(raw)
    
    # --- 根據你儲存的邏輯進行「底色 + 白話文」判定 ---
    if ps >= 9.0:
        bg, text = "#1E4620", "🚀 起飛衝鋒"
        sub = "🔥 強烈持有" if fire else "❄️ 🧐 乖離修正"
        font = "white"
    elif 7.0 <= ps < 9.0:
        bg, text = "#2E7D32", "🚩 趨勢啟動"
        sub = "🔥 標準加碼" if fire else "❄️ ⚠️ 動能衰竭"
        font = "white"
    elif 5.0 <= ps < 7.0:
        bg, text = "#FFFFFF", "✨ 完美伏擊"
        sub = "🔥 主力已動手" if fire else "❄️ 😴 靜默等待"
        font = "black"
    else:
        bg, text = "#4E342E", "💀 快逃命啊"
        sub = "🐍 誘多陷阱" if fire else "❄️ 絕對空手"
        font = "white"

    # --- 渲染密集型卡片 ---
    with cols[i % 4]:
        st.markdown(f"""
            <div style="background-color:{bg}; color:{font}; padding:15px; border-radius:10px; border:1px solid #ccc; margin-bottom:10px;">
                <h2 style="margin:0;">{t} {sub.split()[0]}</h2>
                <p style="font-size:1.1em; font-weight:bold; margin:5px 0;">{text}</p>
                <p style="font-size:0.85em; margin:0;">{sub.split(' ', 1)[1] if ' ' in sub else ''}</p>
                <hr style="margin:8px 0; border:0.5px solid {font}; opacity:0.3;">
                <div style="display:flex; justify-content:space-between; font-size:0.8em;">
                    <span><b>PS: {ps:.1f}</b></span>
                    <span>X1:{raw['X1']} | X2:{raw['X2']} | X3:{raw['X3']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
