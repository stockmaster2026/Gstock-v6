import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統初始化與戰術設定 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.61", page_icon="🛰️")

# 自定義 CSS 確保整體介面專業感
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 預設追蹤名單 (可擴充至 100 檔)
if 'target_list' not in st.session_state:
    st.session_state.target_list = [
        "TSLA", "IONQ", "RKLB", "ASTS", "PLTR", "ONDS", "LUNR", "AAOI", 
        "GLW", "AMD", "NVDA", "SOFI", "RDDT", "OKLO", "KTOS", "PL",
        "SMCI", "ARM", "PLUG", "MARA", "HIMS", "SOUN", "PATH", "SNOW"
    ]

if 'full_registry' not in st.session_state:
    st.session_state.full_registry = {}

# --- 2. 數據抓取與緩存 (10 分鐘黃金頻率) ---
@st.cache_data(ttl=600)
def fetch_market_data(tickers):
    # 執行實時抓取 (目前對位 yfinance 後台)
    data = yf.download(tickers, period="60d", interval="1d", group_by='ticker')
    return data

def update_market_intelligence():
    """核心計算引擎：計算 PS 分數與 SB 點火狀態"""
    raw_data = fetch_market_data(st.session_state.target_list)
    for ticker in st.session_state.target_list:
        try:
            df = raw_data[ticker] if len(st.session_state.target_list) > 1 else raw_data
            if df.empty: continue
            
            current_price = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
            
            # --- PS 分數三維邏輯 (V32.9.38) ---
            # X1: 趨勢對齊 (30%)
            x1 = 10 if current_price > ma20 else 5
            # X2: 構造錨定 (40%) - 均線糾結 < 3%
            spread = abs(ma20 - ma50) / ma20
            x2 = 10 if spread < 0.03 else 5
            # X3: 能量活化 (30%) - 爆量判定
            x3 = 10 if df['Volume'].iloc[-1] > df['Volume'].tail(5).mean() else 4
            
            ps = round((x1 * 0.3) + (x2 * 0.4) + (x3 * 0.3), 1)
            
            # SB 點火判定
            sb = "🔥" if (x2 >= 7 and current_price > ma20) else "❄️"
            
            # 底色判定映射
            if ps >= 9.0: color, label = "深綠色", "🚀 起飛衝鋒"
            elif 7.0 <= ps < 9.0: color, label = "淺綠色", "🚩 趨勢啟動"
            elif 5.0 <= ps < 7.0: color, label = "白色", "✨ 完美伏擊" if sb=="🔥" else "☁️ 蹲下蓄力"
            else: color, label = "咖啡色", "💀 快逃命啊"
            
            # 存入後台資料庫
            st.session_state.full_registry[ticker] = {
                "price": round(current_price, 2), "ps": ps, "sb": sb, 
                "color": color, "label": label,
                "x1": x1, "x2": x2, "x3": x3
            }
        except Exception:
            continue

# 執行戰情刷新
update_market_intelligence()

# --- 3. 佈局規劃 ---
col_left, col_right = st.columns([1, 3.2])

# --- 左側：詳細診斷區 (強制讀卡) ---
with col_left:
    st.subheader("🛰️ 戰術偵察")
    target = st.text_input("輸入代號 (不論是否在面板上):", "IONQ").upper()
    
    if st.button("🔎 執行深度診斷"):
        if target in st.session_state.full_registry:
            d = st.session_state.full_registry[target]
            st.write(f"### **{target} 診斷報告**")
            st.metric("當前實時價", f"${d['price']}", delta=f"PS 指標: {d['ps']}")
            
            # 【白話文邏輯強連動】
            if d['color'] == "咖啡色":
                st.error(f"{d['label']}")
                st.markdown("> **戰情判定**：結構瓦解，主力撤離。**絕對空手，不准摸底！**")
            elif d['color'] == "白色":
                st.info(f"{d['label']}")
                if d['sb'] == "🔥":
                    st.success("**✨ 偵測買點**：主力已動手，完美伏擊位，守住 20MA。")
                else:
                    st.markdown("> **戰情判定**：下雪中(❄️)，能量正在壓縮。**不急進場，耐心守線。**")
            elif d['color'] == "淺綠色":
                st.success(f"{d['label']}")
                st.markdown("> **戰情判定**：標線站穩，趨勢確立。**標準加碼點。**")
            elif d['color'] == "深綠色":
                st.success(f"🚀 {d['label']}")
                st.markdown("> **戰情判定**：三維共振，強者恆強。**只抱不追，讓利潤奔跑！**")
            
            st.divider()
            st.caption("防守座標：收盤價跌破生命線 (20MA) 視為警報。")
        else:
            st.warning(f"⚠️ {target} 未在監控清單中。")

# --- 右側：戰情監控面板 (密集視覺修正版) ---
with col_right:
    st.subheader("📊 11 大板塊實時監控")
    
    # 建立 4 列網格
    cols = st.columns(4)
    visible_items = list(st.session_state.full_registry.items())[:32]
    
    for i, (ticker, data) in enumerate(visible_items):
        with cols[i % 4]:
            # 顏色對位
            bg = {"深綠色": "#006400", "淺綠色": "#90EE90", "白色": "#FFFFFF", "咖啡色": "#6F4E37"}.get(data['color'], "#FFFFFF")
            txt = "white" if data['color'] in ["深綠色", "咖啡色"] else "black"
            
            # 【視覺修正 V32.9.61】密集佈局 CSS
            st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:8px; color:{txt}; border:1px solid #ddd; margin-bottom:10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                    <div style="display:flex; justify-content:space-between; align-items:center; line-height:1;">
                        <span style="font-size:16px; font-weight:bold;">{ticker}</span>
                        <span style="font-size:18px;">{data['sb']}</span>
                    </div>
                    <div style="font-size:24px; font-weight:bold; margin: 4px 0;">${data['price']}</div>
                    <div style="font-size:14px; font-weight:bold; border-bottom:1px solid rgba(128,128,128,0.3); padding-bottom:2px; margin-bottom:4px;">PS: {data['ps']}</div>
                    <div style="font-size:12px; line-height:1.1;">
                        <p style="margin:0 0 2px 0;">技術(X1): {data['x1']}</p>
                        <p style="margin:0 0 2px 0;">構造(X2): {data['x2']}</p>
                        <p style="margin:0;">能量(X3): {data['x3']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

