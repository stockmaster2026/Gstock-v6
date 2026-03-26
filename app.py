
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. 系統初始化與板塊定義 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.69", page_icon="🛰️")

SECTORS = {
    "AI 核心": ["TSLA", "NVDA", "AMD", "SMCI"],
    "半導體": ["AAOI", "GLW", "AVGO", "TSMC"],
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

# --- 2. 核心數據引擎 (對齊 requirements.txt) ---
@st.cache_data(ttl=600)
def fetch_realtime_intel(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=30d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        result = res['chart']['result'][0]
        price = result['meta']['regularMarketPrice']
        quotes = result['indicators']['quote'][0]
        closes = pd.Series(quotes['close']).dropna()
        vols = pd.Series(quotes['volume']).dropna()
        
        m20 = closes.rolling(20).mean().iloc[-1]
        m50 = closes.rolling(min(len(closes), 50)).mean().iloc[-1]
        
        x1 = 10 if price > m20 else 5
        x2 = 10 if abs(m20 - m50) / m20 < 0.03 else 5
        x3 = 10 if vols.iloc[-1] > vols.tail(5).mean() else 4
        ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
        sb = "🔥" if (x2 >= 7 and price > m20) else "❄️"
        
        if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
        elif 7.0 <= ps < 9.0: c, l = "淺綠色", "🚩 趨勢啟動"
        elif 5.0 <= ps < 7.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
        else: c, l = "咖啡色", "💀 快逃命啊"
        
        return {"p": round(price, 2), "ps": ps, "sb": sb, "color": c, "label": l, "x1": x1, "x2": x2, "x3": x3}
    except: return None

# 初始化加載數據
all_t = list(set([t for s in SECTORS.values() for t in s]))
for t in all_t:
    if t not in st.session_state.full_registry:
        st.session_state.full_registry[t] = fetch_realtime_intel(t)

# --- 3. UI 佈局 (左偵察、右監控) ---
col_l, col_r = st.columns([1, 3.2])

with col_l:
    st.title("🛰️ 戰術偵察")
    ticker_input = st.text_input("輸入代號進行全維度偵察:", "LUNR").upper()
    
    if st.button("🚀 執行偵察診斷"):
        if ticker_input in st.session_state.full_registry:
            d = st.session_state.full_registry[ticker_input]
            
            # --- 結果一：呈現完整彩色卡片 ---
            bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
            tx = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
            
            st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:12px; color:{tx}; border:1px solid #ddd; margin-bottom:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:bold; font-size:20px;">{ticker_input}</span>
                        <span style="font-size:24px;">{d['sb']}</span>
                    </div>
                    <div style="font-size:36px; font-weight:bold; margin: 5px 0;">${d['p']}</div>
                    <div style="font-size:18px; border-bottom:1px solid rgba(128,128,128,0.3); margin-bottom:10px; padding-bottom:5px;"><b>PS: {d['ps']}</b></div>
                    <div style="font-size:14px; line-height:1.5; display: flex; justify-content: space-between;">
                        <span>技術(X1): {d['x1']}</span><span>構造(X2): {d['x2']}</span><span>能量(X3): {d['x3']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # --- 結果二：呈現詳細白話文分析 ---
            st.write(f"### **{ticker_input} 戰情報告**")
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
            
            st.caption(f"數據對位時間: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("請確保該代號在板塊監控清單中。")

with col_r:
    st.title("📊 11 大板塊實時監控")
    for sector, tickers in SECTORS.items():
        st.write(f"#### **【{sector}】**")
        grid = st.columns(4)
        for i, t in enumerate(tickers):
            if t in st.session_state.full_registry:
                d = st.session_state.full_registry[t]
                with grid[i % 4]:
                    bg_r = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
                    tx_r = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
                    st.markdown(f"""
                        <div style="background-color:{bg_r}; padding:10px; border-radius:8px; color:{tx_r}; border:1px solid #ddd; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; line-height:1;">
                                <span style="font-weight:bold; font-size:15px;">{t}</span><span>{d['sb']}</span>
                            </div>
                            <div style="font-size:22px; font-weight:bold; margin: 4px 0;">${d['p']}</div>
                            <div style="font-size:13px; border-bottom:1px solid rgba(128,128,128,0.2); margin-bottom:4px; padding-bottom:2px;"><b>PS: {d['ps']}</b></div>
                            <div style="font-size:11px; line-height:1.2; display: flex; justify-content: space-between;">
                                <span>X1:{d['x1']}</span><span>X2:{d['x2']}</span><span>X3:{d['x3']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
