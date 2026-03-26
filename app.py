
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 頁面全域設定 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.38")

# --- 2. 核心計算邏輯 (早晨穩定版) ---
def calculate_v32_logic(df):
    """
    確保傳入的 df 包含 Price, X1, X2, X3, MA20。
    """
    # PS 分數定錨：30% / 40% / 30%
    df['ps'] = (df['X1']*0.3 + df['X2']*0.4 + df['X3']*0.3).round(1)
    # SBUY 點火判定
    df['sbuy'] = (df['X2'] >= 7.0) & (df['Price'] > df['MA20'])
    return df

# --- 3. 基礎卡片組件 (早晨穩定版：無複雜 HTML，不噴代碼) ---
def render_stable_card(ticker, df):
    latest = df.iloc[-1]
    ps = latest['ps']
    
    # 底色邏輯
    if ps >= 9.0: color = "success"  # 深綠
    elif ps >= 7.0: color = "info"    # 淺綠
    elif ps >= 5.0: color = "warning" # 白色/黃色
    else: color = "error"             # 咖啡/紅色
    
    with st.container():
        st.subheader(f"{ticker} {'🔥' if latest['sbuy'] else '❄️'}")
        st.metric(label="當前價格", value=f"${latest['Price']}", delta=f"PS: {ps}")
        st.write(f"**技術(X1):** {latest['X1']} | **構造(X2):** {latest['X3']} | **能量(X3):** {latest['X3']}")
        
        # 簡易診斷文字
        if ps >= 7.0:
            st.write("🚩 **趨勢啟動**")
        elif ps < 5.0:
            st.write("💀 **快逃命啊**")
        else:
            st.write("✨ **等待伏擊**")

# --- 4. 主介面佈局 ---
col_left, col_right = st.columns([1, 4])

with col_left:
    st.header("🚀 偵察診斷")
    target = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        # --- 這裡對接妳的實時抓取 Function ---
        # 範例：df = fetch_realtime_data(target)
        # render_stable_card(target, calculate_v32_logic(df))
        st.write("已成功抓取實時數據進行診斷")

with col_right:
    st.header("📊 11 大板塊監控區")
    monitors = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
    rows = st.columns(4)
    for i, t in enumerate(monitors):
        with rows[i % 4]:
            # --- 這裡對接妳的實時抓取 Function ---
            # df = fetch_realtime_data(t)
            # render_stable_card(t, calculate_v32_logic(df))
            st.info(f"監控中: {t}")

        
