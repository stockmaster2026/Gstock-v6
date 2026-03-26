
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. 初始化與板塊定義 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.70", page_icon="🛰️")

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

# 預載數據
all_t = list(set([t for s in SECTORS.values() for t in s]))
for t in all_t:
    if t not in st.session_state.full_registry:
        st.session_state.full_registry[t] = fetch_realtime_intel(t)

# --- 3. UI 佈局 ---
col_l, col_r = st.columns([1, 3.2])

with col_l:
    st.title("🛰️ 偵察系統")
    t_input = st.text_input("輸入代號進行偵察:", "AAOI").upper()
    
    if st.button("🚀 執行偵察診斷"):
        if t_input in st.session_state.full_registry and st.session_state.full_registry[t_input] is not None:
            d = st.session_state.full_registry[t_input]
            
            # --- 出現放大卡片 ---
            bg_l = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'], "#eee")
            tx_l = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
            st.markdown(f"""
                <div style="background-color:{bg_l}; padding:18px; border-radius:12px; color:{tx_l}; border:1px solid #ddd; margin-bottom:20px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:bold; font-size:22px;">{t_input}</span><span style="font-size:24px;">{d['sb']}</span>
                    </div>
                    <div style="font-size:38px; font-weight:bold; margin: 5px 0;">${d['p']}</div>
                    <div style="font-size:18px; border-bottom:1px solid rgba(128,128,128,0.3); margin-bottom:10px;">PS: {d['ps']}</div>
                    <div style="font-size:14px;">技術(X1):{d['x1']} | 構造(X2):{d['x2']} | 能量(X3):{d['x3']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # --- 出現詳細分析 ---
            st.write(f"### **{t_input} 戰情報告**")
            if d['color'] == "咖啡色":
                st.error(f"判定：{d['label']}")
                st.markdown("### **💀 快逃命啊**\n* **分析**：趨勢已全面崩壞，主力大規模撤離。\n* **指令**：**絕對空手**。不可搶反彈，此為「🐍 誘多陷阱」。")
            elif d['color'] == "白色":
                st.info(f"判定：{d['label']}")
                if d['sb'] == "🔥": st.success("### **✨ 完美伏擊點**\n* **分析**：主力已動手，均線高度壓縮。建議分批建倉，守住 20MA。")
                else: st.markdown("### **☁️ 蹲下蓄力**\n* **分析**：能量正在壓縮。建議耐心守線，不急於進場。")
            elif d['color'] == "淺綠色":
                st.success(f"判定：{d['label']}")
                st.markdown("### **🚩 趨勢啟動**\n* **分析**：標線站穩。建議標準加碼，守住 20MA。")
            else:
                st.success(f"判定：{d['label']}")
                st.markdown("### **🚀 起飛衝鋒**\n* **分析**：強者恆強。不預設高點，讓利潤奔跑！")
        else: st.warning("數據獲取中或查無此標的。")

with col_r:
    st.title("📊 11 大板塊實時監控")
    for sector, tickers in SECTORS.items():
        st.write(f"#### **【{sector}】**")
        grid = st.columns(4)
        for i, t in enumerate(tickers):
            # 防錯：確保 d 不是 None 且 key 存在
            d_r = st.session_state.full_registry.get(t)
            if d_r:
                with grid[i % 4]:
                    bg_r = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d_r['color'], "#eee")
                    tx_r = "white" if d_r['color'] in ["深綠色", "咖啡色"] else "black"
                    st.markdown(f"""
                        <div style="background-color:{bg_r}; padding:10px; border-radius:8px; color:{tx_r}; border:1px solid #ddd; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; line-height:1;">
                                <span style="font-weight:bold; font-size:15px;">{t}</span><span>{d_r['sb']}</span>
                            </div>
                            <div style="font-size:22px; font-weight:bold; margin: 4px 0;">${d_r['p']}</div>
                            <div style="font-size:13px; border-bottom:1px solid rgba(128,128,128,0.2); margin-bottom:4px; padding-bottom:2px;"><b>PS: {d_r['ps']}</b></div>
                            <div style="font-size:10.5px; line-height:1.1; display:flex; justify-content:space-between;">
                                <span>X1:{d_r['x1']}</span><span>X2:{d_r['x2']}</span><span>X3:{d_r['x3']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
