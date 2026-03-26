
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. 系統初始化與板塊定義 (戰術歸位) ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.65", page_icon="🛰️")

# 強制鎖定 11 大板塊 (神聖不可侵犯)
if 'sectors' not in st.session_state:
    st.session_state.sectors = {
        "AI 核心": ["TSLA", "NVDA", "AMD", "SMCI"],
        "半導體": ["AAOI", "GLW", "INTC", "TSMC"],
        "航太太空": ["RKLB", "LUNR", "ONDS", "KTOS"],
        "網路安全": ["OKLO", "PATH", "SNOW", "OKTA"],
        "加密貨幣": ["MARA", "RIOT", "COIN", "MSTR"],
        "能源轉型": ["PLUG", "FCEL", "BLDP", "CHPT"],
        "生技醫療": ["HIMS", "TDOC", "GILD", "VRTX"],
        "軍工防禦": ["PLTR", "SOUN", "PATH", "AI"], # PLTR 兼具軍工大數據
        "大數據": ["PLTR", "DDOG", "MDB", "ESTC"],
        "自動駕駛": ["TSLA", "MBLY", "Aurora", "MVIS"],
        "民生消費": ["SOFI", "RDDT", "PL", "U"]
    }

# 將所有個股打平成 100 檔後台庫存 (預備軍)
if 'target_list' not in st.session_state:
    all_tickers = [ticker for sublist in st.session_state.sectors.values() for ticker in sublist]
    # 確保不重複，並可自行擴充
    st.session_state.target_list = list(set(all_tickers + ["SOUN", "HIMS", "PATH", "SNOW"]))

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# --- 2. 數據抓取引擎 (使用 requests，對齊補給清單) ---
@st.cache_data(ttl=600) # 10 分鐘黃金頻率
def fetch_stock_intel(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=30d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        result = data['chart']['result'][0]
        price = result['meta']['regularMarketPrice']
        closes = pd.Series(result['indicators']['quote'][0]['close']).dropna()
        if len(close_series) < 20: return None
        volumes = result['indicators']['quote'][0]['volume']
        
        # 指標計算
        m20 = closes.rolling(20).mean().iloc[-1]
        m50 = closes.rolling(min(len(closes), 50)).mean().iloc[-1]
        
        # --- PS 分數三維邏輯 (V32.9.38) ---
        x1 = 10 if price > m20 else 5
        x2 = 10 if abs(m20 - m50) / m20 < 0.03 else 5
        x3 = 10 if volumes[-1] > np.mean(volumes[-5:]) else 4
        ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
        sb = "🔥" if (x2 >= 7 and price > ma20) else "❄️"
        
        # 底色判定
        if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
        elif ps >= 7.0: c, l = "淺綠色", "🚩 趨勢啟動"
        elif ps >= 5.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
        else: c, l = "咖啡色", "💀 快逃命啊"
        
        return {"p": round(price, 2), "ps": ps, "sb": sb, "color": c, "label": l, "x1": x1, "x2": x2, "x3": x3}
    except Exception: return None

def update_intelligence():
    # 這裡實施 100 檔後台庫存的全量更新
    for t in st.session_state.target_list:
        intel = fetch_stock_intel(t)
        if intel: st.session_state.full_registry[t] = intel

update_intelligence()

# --- 3. 介面佈局 (視覺 & 功能重建) ---
col_left, col_right = st.columns([1, 3])

# --- 左側：雙偵察框 (功能完全拆分) ---
with col_left:
    st.subheader("🛰️ 戰術偵察中心")
    
    # 功能一：個股詳細診斷 (產出白話文分析)
    st.divider()
    st.write("### **1. 個股詳細診斷**")
    query_diag = st.text_input("輸入代號進行詳細診斷 (如: RKLB):", "IONQ").upper()
    
    if st.button("🔎 執行深度診斷"):
        # 強制讀卡分析，絕不腦補
        if query_diag in st.session_state.full_registry:
            d = st.session_state.full_registry[query_diag]
            st.write(f"#### **{query_diag} 實戰診斷**")
            st.metric("實時價", f"${d['p']}", delta=f"PS: {d['ps']}")
            # 白話文邏輯強連動
            if d['color'] == "咖啡色": st.error(f"{d['label']}")
            elif d['color'] == "白色": st.info(f"{d['label']}")
            else: st.success(f"{d['label']}")
        else: st.warning("請先確保代號在監控清單中。")

    # 功能二：搜尋板塊個股 (產出卡片視覺)
    st.divider()
    st.write("### **2. 搜尋個股卡片**")
    query_card = st.text_input("輸入代號在板塊中標記:", "").upper()
    if st.button("🎯 執行搜尋標記"):
        if query_card:
            if query_card in st.session_state.full_registry:
                st.success(f"已在【{get_ticker_sector(query_card)}】板塊中標記 {query_card}。")
                # 此處可用 session state 記錄要強化的卡片，這裡簡化處理
            else:
                st.error("此代號未在後台數據庫中。")

# --- 右側：11 大板塊 (視覺密集排列修正版) ---
def get_ticker_sector(ticker):
    for sector, tickers in st.session_state.sectors.items():
        if ticker in tickers: return sector
    return None

with col_right:
    st.subheader("📊 11 大板塊戰情監控面板")
    
    for sector, tickers in st.session_state.sectors.items():
        st.write(f"### **【{sector}】**")
        # 為每個板塊建立 4 列網格
        cols = st.columns(4)
        
        # 篩選出該板塊有數據的股票
        sector_items = {t: st.session_state.full_registry[t] for t in tickers if t in st.session_state.full_registry}
        
        for i, (ticker, data) in enumerate(sector_items.items()):
            with cols[i % 4]:
                # 顏色對位
                bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(data['color'])
                tx = "white" if data['color'] in ["深綠色", "咖啡色"] else "black"
                
                # 【視覺修正】密集佈局，解決 X3 掉出框外問題
                st.markdown(f"""
                    <div style="background-color:{bg}; padding:10px; border-radius:8px; color:{tx}; border:1px solid #ddd; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; line-height:1;">
                            <span style="font-size:16px; font-weight:bold;">{ticker}</span>
                            <span style="font-size:18px;">{data['sb']}</span>
                        </div>
                        <div style="font-size:24px; font-weight:bold; margin: 4px 0;">${data['p']}</div>
                        <div style="font-size:14px; font-weight:bold; border-bottom:1px solid rgba(128,128,128,0.3); padding-bottom:2px; margin-bottom:4px;">PS: {data['ps']}</div>
                        <div style="font-size:11px; line-height:1.2; display: flex; justify-content: space-between;">
                            <span>X1:{data['x1']}</span><span>X2:{data['x2']}</span><span>X3:{data['x3']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
