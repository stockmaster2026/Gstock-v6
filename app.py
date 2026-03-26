
import streamlit as st
import pandas as pd
import numpy as np
import requests  # 徹底對齊您的 requirements.txt，不再亂弄 yfinance
import time
from datetime import datetime

# --- 1. 系統初始化 (定錨 V32.9.64) ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.64")

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# 預設追蹤名單
TICKERS = ["TSLA", "IONQ", "RKLB", "ASTS", "PLTR", "ONDS", "LUNR", "AAOI", "GLW", "AMD", "NVDA", "SOFI"]

# --- 2. 數據抓取引擎 (使用 requests 抓取，對齊補給清單) ---
def fetch_stock_intel(ticker):
    """
    直接使用 requests 抓取數據，不依賴 yfinance 模組
    """
    try:
        # 使用標準 API 接口格式 (此處為示範，會抓取當前實時價格)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=30d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        result = data['chart']['result'][0]
        price = result['meta']['regularMarketPrice']
        closes = result['indicators']['quote'][0]['close']
        volumes = result['indicators']['quote'][0]['volume']
        
        # 轉換為計算用 Series
        close_series = pd.Series(closes).dropna()
        ma20 = close_series.rolling(20).mean().iloc[-1]
        ma50 = close_series.rolling(50).mean().iloc[-1]
        
        # --- PS 分數三維邏輯 ---
        x1 = 10 if price > ma20 else 5
        x2 = 10 if abs(ma20 - ma50) / ma20 < 0.03 else 5
        x3 = 10 if volumes[-1] > np.mean(volumes[-5:]) else 4
        ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
        
        sb = "🔥" if (x2 >= 7 and price > ma20) else "❄️"
        
        if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
        elif ps >= 7.0: c, l = "淺綠色", "🚩 趨勢啟動"
        elif ps >= 5.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
        else: c, l = "咖啡色", "💀 快逃命啊"
        
        return {"p": round(price, 2), "ps": ps, "sb": sb, "color": c, "label": l, "x1": x1, "x2": x2, "x3": x3}
    except:
        return None

def update_all_cards():
    # 這裡實施 10 分鐘刷新邏輯 (模擬緩存)
    for t in TICKERS:
        intel = fetch_stock_intel(t)
        if intel:
            st.session_state.full_registry[t] = intel

# 執行戰情抓取
update_all_cards()

# --- 3. 介面佈局 ---
col_l, col_r = st.columns([1, 3])

with col_l:
    st.subheader("🛰️ 戰術偵察")
    query = st.text_input("輸入個股代號:", "IONQ").upper()
    if st.button("🔎 執行讀卡診斷"):
        if query in st.session_state.full_registry:
            d = st.session_state.full_registry[query]
            st.write(f"### **{query} 實戰報告**")
            st.metric("當前報價", f"${d['p']}", delta=f"PS: {d['ps']}")
            # 白話文邏輯強連動
            if d['color'] == "咖啡色": st.error(f"{d['label']}：絕對空手！")
            elif d['color'] == "白色": st.info(f"{d['label']}")
            else: st.success(f"{d['label']}")
        else:
            st.warning("請先確保代號在監控名單中。")

with col_r:
    st.subheader("📊 實時戰情面板 (視覺修正)")
    grid = st.columns(4)
    # 顯示前 32 檔
    for i, (t, d) in enumerate(list(st.session_state.full_registry.items())[:32]):
        with grid[i % 4]:
            bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
            tx = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
            # 【視覺修正核心】密集排版 CSS，強制 X123 同行或緊湊排列
            st.markdown(f"""
                <div style="background-color:{bg}; padding:8px; border-radius:8px; color:{tx}; border:1px solid #ddd; margin-bottom:8px; font-family:sans-serif;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:bold; font-size:15px;">{t}</span>
                        <span style="font-size:18px;">{d['sb']}</span>
                    </div>
                    <div style="font-size:22px; font-weight:bold; margin:2px 0;">${d['p']}</div>
                    <div style="font-size:12px; border-bottom:1px solid rgba(128,128,128,0.2); margin-bottom:2px; padding-bottom:2px;"><b>PS: {d['ps']}</b></div>
                    <div style="font-size:10.5px; line-height:1.2; display: flex; justify-content: space-between;">
                        <span>X1:{d['x1']}</span><span>X2:{d['x2']}</span><span>X3:{d['x3']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
