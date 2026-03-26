
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 頁面全域設定 (維持早上佈局) ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.60")

# --- 2. 核心數據處理引擎 (維持早上穩定邏輯，加入軌跡累積) ---
def process_stock_data(ticker):
    """
    這部分對接妳系統的實時數據。
    這裡暫用 df 結構演示，請確保妳的數據源傳入 Price, X1, X2, X3, MA20。
    """
    # 模擬 5 天歷史，確保 PS 與 SBUY 軌跡自動累積 (這部分請對接妳的實時 API)
    # 這裡的 Price, X1, X2, X3 必須是妳抓到的真實數據
    dates = pd.date_range(end=pd.Timestamp.now(), periods=5)
    data = {
        'Date': dates,
        'Price': [19.21] * 5, # 範例，會被妳的實時數據取代
        'X1': [10, 10, 9, 10, 10], 
        'X2': [10, 10, 10, 10, 10], 
        'X3': [4, 4, 5, 4, 4],
        'MA20': [18.5] * 5
    }
    df = pd.DataFrame(data)
    
    # PS 權重計算: X1(30%) + X2(40%) + X3(30%)
    df['ps'] = (df['X1']*0.3 + df['X2']*0.4 + df['X3']*0.3).round(1)
    
    # SBUY 判定 (五日火點累積基準)
    df['sbuy'] = (df['X2'] >= 7.0) & (df['Price'] > df['MA20'])
    
    return df

# --- 3. 密集型卡片組件 (修正 HTML 噴代碼問題，找回軌跡與佔比) ---
def render_v32_card(ticker, df):
    latest = df.iloc[-1]
    ps_score = latest['ps']
    
    # 軌跡數據生成 (自動從 df 累積)
    ps_hist = "→".join(df['ps'].astype(str).tolist())
    sbuy_hist = " ".join(["🔥" if s else "❄️" for s in df['sbuy'].tolist()])
    
    # 底色判定
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "white", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "black", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "#FFFFFF", "black", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "white", "💀 快逃命啊"

    fire_icon = "🔥" if latest['sbuy'] else "❄️"

    # HTML 密集封裝 (不溢出、不噴代碼)
    card_html = f"""
    <div style="background-color:{bg}; border-radius:10px; padding:12px; color:{txt}; border:1px solid #ddd; margin-bottom:15px; font-family: sans-serif; line-height:1.2;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:18px;">{ticker}</b>
            <span style="font-size:18px;">{fire_icon}</span>
        </div>
        <div style="font-size:30px; font-weight:bold; margin:5px 0;">${latest['Price']}</div>
        
        <div style="border-top:1px solid {txt}44; padding-top:8px;">
            <div style="font-size:13px; font-weight:bold;">PS 五日軌跡: {ps_score}</div>
            <div style="font-size:10px; opacity:0.8; margin-top:2px;">({ps_hist})</div>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-top:10px; background:rgba(0,0,0,0.05); padding:6px; border-radius:6px;">
            <div style="text-align:center;"><b>X1</b><br>30%<br>{latest['X1']}</div>
            <div style="text-align:center;"><b>X2</b><br>40%<br>{latest['X2']}</div>
            <div style="text-align:center;"><b>X3</b><br>30%<br>{latest['X3']}</div>
        </div>

        <div style="font-size:11px; margin-top:10px; padding:5px; border-left:4px solid {txt};">
            <b>SBUY 五日累積軌跡:</b><br>
            <span style="font-size:15px; letter-spacing:3px;">{sbuy_hist}</span>
        </div>
        
        <div style="font-size:13px; margin-top:10px; font-weight:bold; text-align:right;">
            {label}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# --- 4. 主佈局架構 (完全維持早上穩定版) ---
col_left, col_right = st.columns([1.2, 4.8])

with col_left:
    st.subheader("🎯 執行偵察診斷")
    input_t = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        data = process_stock_data(input_t)
        render_v32_card(input_t, data)
        st.info(f"系統已自動累計 {input_t} 過去五日 PS 與 SBUY 軌跡。")

with col_right:
    st.subheader("📊 11 大板塊監控區")
    monitors = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
    # 改為 3 欄，確保卡片夠寬不窄長
    cols = st.columns(3) 
    for i, t in enumerate(monitors):
        with cols[i % 3]:
            data = process_stock_data(t)
            render_v32_card(t, data)
