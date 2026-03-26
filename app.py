import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. 系統初始化與【11 大板塊】定義 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.68", page_icon="🛰️")

SECTORS = {
    "AI 核心": ["TSLA", "NVDA", "AMD", "SMCI"],
    "半導體": ["AAOI", "GLW", "AVGO", "TSMC"],
    "航太太空": ["RKLB", "LUNR", "ONDS", "KTOS"],
    "網路安全": ["OKLO", "PATH", "SNOW", "PLTR"],
    "加密貨幣": ["MARA", "RIOT", "COIN", "MSTR"],
    "能源轉型": ["PLUG", "FCEL", "BLDP", "CHPT"],
    "生技醫療": ["HIMS", "TDOC", "GILD", "VRTX"],
    "軍工防衛": ["PLTR", "SOUN", "PATH", "KTOS"],
    "大數據": ["PLTR", "DDOG", "MDB", "SNOW"],
    "自動駕駛": ["TSLA", "MBLY", "Aurora", "MVIS"],
    "民生消費": ["SOFI", "RDDT", "PL", "U"]
}

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# --- 2. 數據抓取引擎 (對齊 requirements.txt) ---
@st.cache_data(ttl=600)
def fetch_realtime_intel(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=30d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        result = res['chart']['result'][0]
        price = result['meta']['regularMarketPrice']
        closes = pd.Series(result['indicators']['quote'][0]['close']).dropna()
        vols = pd.Series(result['indicators']['quote'][0]['volume']).dropna()
        
        m20 = closes.rolling(20).mean().iloc[-1]
        m50 = closes.rolling(min(len(closes), 50)).mean().iloc[-1]
        
        # --- 定錨 V32.9.38 核心算法 ---
        x1 = 10 if price > m20 else 5
        x2 = 10 if abs(m20 - m50) / m20 < 0.03 else 5
        x3 = 10 if vols.iloc[-1] > vols.tail(5).mean() else 4
        ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
        sb = "🔥" if (x2 >= 7 and price > m20) else "❄️"
        
        # 底色判定
        if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
        elif 7.0 <= ps < 9.0: c, l = "淺綠色", "🚩 趨勢啟動"
        elif 5.0 <= ps < 7.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
        else: c, l = "咖啡色", "💀 快逃命啊"
        
        return {"p": round(price, 2), "ps": ps, "sb": sb, "color": c, "label": l, "x1": x1, "x2": x2, "x3": x3}
    except: return None

# 初始化所有板塊個股數據
all_t = list(set([t for s in SECTORS.values() for t in s]))
for t in all_t:
    if t not in st.session_state.full_registry:
        st.session_state.full_registry[t] = fetch_realtime_intel(t)

# --- 3. 介面與【白話文診斷邏輯 V32.9.53】 ---
col_l, col_r = st.columns([1, 3.2])

with col_l:
    st.title("🛰️ 戰術偵察中心")
    
    # 【功能一：詳細診斷】
    st.write("### **1. 個股詳細診斷**")
    diag_q = st.text_input("輸入代號進行詳細診斷 (如: PL):", "PL", key="d").upper()
    
    if st.button("🔎 執行深度診斷"):
        # 強制對位 Registry 數據，防止數據脫鉤
        if diag_q in st.session_state.full_registry:
            d = st.session_state.full_registry[diag_q]
            st.write(f"#### **{diag_q} 戰情報告**")
            st.metric("當前實時價", f"${d['p']}", delta=f"PS 指標: {d['ps']}")
            
            # --- 物理性鎖定白話文判斷邏輯 ---
            if d['color'] == "咖啡色":
                st.error(f"判定底色：{d['label']}")
                st.markdown("### **💀 快逃命啊**\n* **分析**：趨勢已全面崩壞，主力大規模撤離。\n* **指令**：**絕對空手**。不可搶反彈，此為「🐍 誘多陷阱」。")
            elif d['color'] == "白色":
                st.info(f"判定底色：{d['label']}")
                if d['sb'] == "🔥":
                    st.success("### **✨ 完美伏擊點**\n* **分析**：主力已動手，均線高度壓縮完畢。\n* **指令**：**分批建倉**。守住生命線 (20MA)，等待噴發。")
                else:
                    st.markdown("### **☁️ 蹲下蓄力**\n* **分析**：能量正在壓縮，目前處於下雪(❄️)狀態。\n* **指令**：**只抱不追**。耐心守線，動能尚未對齊。")
            elif d['color'] == "淺綠色":
                st.success(f"判定底色：{d['label']}")
                st.markdown("### **🚩 趨勢啟動**\n* **分析**：標線站穩，標準趨勢對齊。\n* **指令**：**標準加碼點**。守住 20MA，享受波段。")
            elif d['color'] == "深綠色":
                st.success(f"判定底色：{d['label']}")
                st.markdown("### **🚀 起飛衝鋒**\n* **分析**：三維共振最強狀態，強者恆強。\n* **指令**：**強烈持有**。不預設高點，直到出現落袋訊號。")
            
            st.caption(f"診斷時間: {datetime.now().strftime('%H:%M:%S')}")
        else: st.warning("請確保代號已加入監控清單。")

    st.divider()
    # 【功能二：定位卡片】
    st.write("### **2. 搜尋個股卡片**")
    card_q = st.text_input("輸入代號定位卡片:", "", key="c").upper()
    if st.button("🎯 執行搜尋定位"):
        if card_q in st.session_state.full_registry: st.info(f"已於右側板塊鎖定 {card_q}")
        else: st.error("查無此標的庫存。")

with col_r:
    st.title("📊 11 大板塊監控面板")
    for sector, tickers in SECTORS.items():
        st.write(f"#### **【{sector}】**")
        grid = st.columns(4)
        for i, t in enumerate(tickers):
            if t in st.session_state.full_registry:
                d = st.session_state.full_registry[t]
                with grid[i % 4]:
                    bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
                    tx = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
                    # 密集修正 CSS，解決 X3 溢出問題
                    st.markdown(f"""
                        <div style="background-color:{bg}; padding:10px; border-radius:8px; color:{tx}; border:1px solid #ddd; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; line-height:1;">
                                <span style="font-weight:bold; font-size:15px;">{t}</span><span>{d['sb']}</span>
                            </div>
                            <div style="font-size:24px; font-weight:bold; margin: 4px 0;">${d['p']}</div>
                            <div style="font-size:13px; border-bottom:1px solid rgba(128,128,128,0.2); margin-bottom:4px; padding-bottom:2px;"><b>PS: {d['ps']}</b></div>
                            <div style="font-size:11px; line-height:1.2; display: flex; justify-content: space-between;">
                                <span>X1:{d['x1']}</span><span>X2:{d['x2']}</span><span>X3:{d['x3']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

