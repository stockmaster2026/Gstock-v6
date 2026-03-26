import streamlit as st
import yfinance as yf  # 確保與您的 requirements.txt 內容一致
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統初始化 (沿用成功版本的設定) ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.61", page_icon="🛰️")

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# 預設追蹤名單
TICKERS = ["TSLA", "IONQ", "RKLB", "ASTS", "PLTR", "ONDS", "LUNR", "AAOI", "GLW", "AMD", "NVDA", "SOFI", "RDDT", "OKLO", "KTOS", "PL"]

# --- 2. 數據抓取 (維持 10 分鐘黃金頻率，確保不報錯) ---
@st.cache_data(ttl=600)
def fetch_data(ticker_list):
    # 使用與您環境最相容的抓取方式
    return yf.download(ticker_list, period="60d", interval="1d", group_by='ticker')

def update_intelligence():
    raw = fetch_data(TICKERS)
    for t in TICKERS:
        try:
            df = raw[t] if len(TICKERS) > 1 else raw
            if df.empty: continue
            
            cp = df['Close'].iloc[-1]
            m20 = df['Close'].rolling(window=20).mean().iloc[-1]
            m50 = df['Close'].rolling(window=50).mean().iloc[-1]
            
            # PS 分數 (V32.9.38 定錨邏輯)
            x1 = 10 if cp > m20 else 5
            x2 = 10 if abs(m20 - m50) / m20 < 0.03 else 5
            x3 = 10 if df['Volume'].iloc[-1] > df['Volume'].tail(5).mean() else 4
            ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
            
            sb = "🔥" if (x2 >= 7 and cp > m20) else "❄️"
            
            if ps >= 9.0: c, l = "深綠色", "🚀 起飛衝鋒"
            elif 7.0 <= ps < 9.0: c, l = "淺綠色", "🚩 趨勢啟動"
            elif 5.0 <= ps < 7.0: c, l = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
            else: c, l = "咖啡色", "💀 快逃命啊"
            
            st.session_state.full_registry[t] = {
                "p": round(cp, 2), "ps": ps, "sb": sb, "color": c, "label": l,
                "x1": x1, "x2": x2, "x3": x3
            }
        except: continue

update_intelligence()

# --- 3. 介面佈局 ---
col_l, col_r = st.columns([1, 3])

with col_l:
    st.subheader("🛰️ 戰術偵察")
    query = st.text_input("輸入代號:", "IONQ").upper()
    if st.button("🔎 執行深度診斷"):
        # 【強制讀卡】確保數據來源唯一性
        if query in st.session_state.full_registry:
            d = st.session_state.full_registry[query]
            st.write(f"### **{query} 診斷報告**")
            st.metric("實時價", f"${d['p']}", delta=f"PS: {d['ps']}")
            
            # 白話文邏輯鎖死
            if d['color'] == "咖啡色":
                st.error(f"{d['label']}")
                st.write("💀 **絕對空手**：結構已崩，不准摸底。")
            elif d['color'] == "白色":
                st.info(f"{d['label']}")
                st.write("✨ **完美伏擊**" if d['sb']=="🔥" else "☁️ **蹲下蓄力**：下雪中，守住 20MA。")
            elif d['color'] == "淺綠色":
                st.success(f"{d['label']}：標準加碼點。")
            elif d['color'] == "深綠色":
                st.success(f"🚀 {d['label']}：讓利潤奔跑！")
        else: st.warning("請先確保代號在監控清單中。")

with col_r:
    st.subheader("📊 實時戰情面板")
    cols = st.columns(4)
    for i, (t, d) in enumerate(list(st.session_state.full_registry.items())[:32]):
        with cols[i % 4]:
            bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(d['color'])
            tx = "white" if d['color'] in ["深綠色", "咖啡色"] else "black"
            
            # 【視覺修正 V32.9.61】密集佈局，確保 X3 不掉出框外
            st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:8px; color:{tx}; border:1px solid #ddd; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; line-height:1;">
                        <span style="font-weight:bold;">{t}</span><span>{d['sb']}</span>
                    </div>
                    <div style="font-size:22px; font-weight:bold; margin:3px 0;">${d['p']}</div>
                    <div style="font-size:13px; border-bottom:1px solid rgba(128,128,128,0.3); margin-bottom:3px;">PS: {d['ps']}</div>
                    <div style="font-size:12px; line-height:1.1;">
                        <p style="margin:0;">技術(X1): {d['x1']}</p>
                        <p style="margin:0;">構造(X2): {d['x2']}</p>
                        <p style="margin:0;">能量(X3): {d['x3']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

