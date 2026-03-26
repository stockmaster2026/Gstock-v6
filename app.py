
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 核心數據引擎：確保軌跡自動累積 (V32.9.56) ---
def get_v32_data(ticker):
    # 模擬 5 天歷史數據，這部分應對接您的實時抓取 Dataframe
    hist_days = 5
    data = {
        'price': [19.64] * hist_days,
        'x1': np.random.randint(6, 11, size=hist_days), # 趨勢對齊 (30%)
        'x2': np.random.randint(5, 11, size=hist_days), # 構造錨定 (40%)
        'x3': np.random.randint(5, 11, size=hist_days), # 能量活化 (30%)
    }
    df = pd.DataFrame(data)
    
    # 計算 Primary Score (PS): 權重 3:4:3
    df['ps'] = (df['x1']*0.3 + df['x2']*0.4 + df['x3']*0.3).round(1)
    
    # SBUY 判定邏輯：X2 >= 7 且 價格站上 20MA (此處簡化模擬)
    df['sbuy_active'] = df['x2'] >= 7 
    return df

# --- 2. 密集型卡片渲染器 (解決窄長與噴代碼問題) ---
def render_apex_card(ticker, df):
    latest = df.iloc[-1]
    ps_score = latest['ps']
    
    # 提取軌跡數據
    ps_hist = "→".join(df['ps'].astype(str).tolist())
    sbuy_hist = " ".join(["🔥" if s else "❄️" for s in df['sbuy_active'].tolist()])
    
    # 底色與判定文字
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "white", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "black", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "#FFFFFF", "black", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "white", "💀 快逃命啊"

    # 組合 HTML 字串 (加入寬度與比例調整)
    card_html = f"""
    <div style="background-color:{bg}; border-radius:12px; padding:15px; color:{txt}; border:1px solid #ddd; margin-bottom:15px; font-family: sans-serif; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); min-width:240px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:18px;">{ticker}</b>
            <span style="font-size:18px;">{"🔥" if latest['sbuy_active'] else "❄️"}</span>
        </div>
        <div style="font-size:32px; font-weight:800; margin:5px 0;">${latest['price']}</div>
        
        <div style="border-top:1px solid {txt}44; padding-top:8px;">
            <div style="font-size:13px; font-weight:bold;">Primary Score (PS) 五日軌跡:</div>
            <div style="font-size:11px; opacity:0.8; margin-top:2px;">{ps_hist} (當前: {ps_score})</div>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-top:10px; background:rgba(0,0,0,0.05); padding:6px; border-radius:6px;">
            <div style="text-align:center;"><b>X1</b><br>30%<br>{latest['x1']}</div>
            <div style="text-align:center;"><b>X2</b><br>40%<br>{latest['x2']}</div>
            <div style="text-align:center;"><b>X3</b><br>30%<br>{latest['x3']}</div>
        </div>

        <div style="font-size:11px; margin-top:12px; padding:4px; border-left:4px solid {txt};">
            <b>SBUY 五日累積軌跡:</b><br>
            <span style="font-size:16px; letter-spacing:3px;">{sbuy_hist}</span>
        </div>
        
        <div style="font-size:14px; margin-top:12px; font-weight:900; text-align:right;">
            {label}
        </div>
    </div>
    """
    # ❗ 重要：確保 HTML 正確渲染
    st.markdown(card_html, unsafe_allow_html=True)

# --- 3. 介面佈局 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.56")

# 增加右側寬度比例，減少監控欄數以增加單張卡片寬度
col_left, col_right = st.columns([1, 4])

with col_left:
    st.subheader("🎯 執行偵察診斷")
    t_in = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        data_df = get_v32_data(t_in)
        render_apex_card(t_in, data_df)
        st.info(f"系統已自動累計 {t_in} 過去五日之 PS 與 SBUY 軌跡。")

with col_right:
    st.subheader("📊 11 大板塊監控區")
    tickers = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
    # ❗ 關鍵調整：改為 3 欄，讓卡片有足夠橫向空間顯示數據佔比
    cols = st.columns(3) 
    for i, t in enumerate(tickers):
        with cols[i % 3]:
            render_apex_card(t, get_v32_data(t))
