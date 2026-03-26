
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. 初始化與 11 大板塊定義 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.66", page_icon="🛰️")

# 定義 11 大板塊對應名單
SECTORS = {
    "AI 核心": ["TSLA", "NVDA", "AMD", "SMCI"],
    "半導體": ["AAOI", "GLW", "INTC", "TSMC"],
    "航太太空": ["RKLB", "LUNR", "ONDS", "KTOS"],
    "網路安全": ["OKLO", "PATH", "SNOW", "PLTR"],
    "加密貨幣": ["MARA", "RIOT", "COIN", "MSTR"],
    "能源轉型": ["PLUG", "FCEL", "BLDP", "CHPT"],
    "生技醫療": ["HIMS", "TDOC", "GILD", "VRTX"],
    "軍工防禦": ["PLTR", "SOUN", "PATH", "KTOS"],
    "大數據": ["PLTR", "DDOG", "MDB", "SNOW"],
    "自動駕駛": ["TSLA", "MBLY", "Aurora", "MVIS"],
    "民生消費": ["SOFI", "RDDT", "PL", "U"]
}

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# --- 2. 數據引擎 (使用 requests，完全避開 yfinance) ---
@st.cache_data(ttl=600)
def fetch_data_requests(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=30d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        meta = res['chart']['result'][0]['meta']
        indicators = res['chart']['result'][0]['indicators']['quote'][0]
        
        price = meta['regularMarketPrice']
        closes = pd.Series(indicators['close']).dropna()
        vols = indicators['volume']
        
        m20 = closes.rolling(20).mean().iloc[-1]
        m50 = closes.rolling(min(len(closes), 50)).mean().iloc[-1]
        
        # PS 核心邏輯
        x1 = 10 if price > m20 else 5
        x2 = 10 if abs(m20 - m50) / m20 < 0.03 else 5
        x3 = 10 if vols[-1] > np.mean(vols[-5:]) else 4
        ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
        sb = "🔥" if (x2 >= 7 and price > m20) else "❄️"
        
        if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
        elif ps >= 7.0: c, l = "淺綠色", "🚩 趨勢啟動"
        elif ps >= 5.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
        else: c, l = "咖啡色", "💀 快逃命啊"
        
        return {"p": round(price, 2), "ps": ps, "sb": sb, "color": c, "label": l, "x1": x1, "x2": x2, "x3": x3}
    except: return None

# 初始化加載所有名單
all_tickers = list(set([t for sub in SECTORS.values() for t in sub]))
for t in all_tickers:
    if t not in st.session_state.full_registry:
        intel = fetch_data_requests(t)
        if intel: st.session_state.full_registry[t] = intel

# --- 3. 佈局實作 ---
col_left, col_right = st.columns([1, 3.2])

with col_left:
    st.title("🛰️ 戰術偵察中心")
    
    # 【功能一：詳細診斷】
    st.markdown("### **1. 個股詳細診斷**")
    diag_input = st.text_input("輸入代號進行診斷:", "IONQ", key="diag").upper()
    if st.button("🔎 執行深度診斷"):
        if diag_input in st.session_state.full_registry:
            d = st.session_state.full_registry[diag_input]
            st.metric(f"{diag_input} 報價", f"${d['p']}", delta=f"PS: {d['ps']}")
            st.success(f"判定：{d['label']}") # 這裡會產出您的白話文分析
        else: st.warning("數據尚未同步。")

    st.divider()
    
    # 【功能二：搜尋卡片】
    st.markdown("### **2. 搜尋個股卡片**")
    card_input = st.text_input("輸入代號搜尋卡片:", "", key="card").upper()
    if st.button("🎯 執行搜尋定位"):
        if card_input in st.session_state.full_registry:
            st.info(f"已在右側面板為您定位 {card_input}")
        else: st.error("代號不在資料庫中。")

with col_right:
    st.title("📊 11 大板塊戰情監控面板")
    for sector, tickers in SECTORS.items():
        st.write(f"#### **【{sector}】**")
        grid = st.columns(4)
        for i, t in enumerate(tickers):
            if t in st.session_state.full_registry:
                d = st.session_state.full_registry[t]
                with grid[i % 4]:
                    bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
                    tx = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
                    # 密集視覺排版
                    st.markdown(f"""
                        <div style="background-color:{bg}; padding:10px; border-radius:8px; color:{tx}; border:1px solid #ddd; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; line-height:1;">
                                <span style="font-weight:bold; font-size:14px;">{t}</span><span>{d['sb']}</span>
                            </div>
                            <div style="font-size:22px; font-weight:bold; margin:2px 0;">${d['p']}</div>
                            <div style="font-size:12px; border-bottom:1px solid rgba(128,128,128,0.2); margin-bottom:3px; padding-bottom:2px;">PS: {d['ps']}</div>
                            <div style="font-size:10.5px; line-height:1.1; display:flex; justify-content:space-between;">
                                <span>X1:{d['x1']}</span><span>X2:{d['x2']}</span><span>X3:{d['x3']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
