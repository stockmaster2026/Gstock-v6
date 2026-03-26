
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 核心數據引擎：確保軌跡自動累積 ---
def get_v32_data(ticker):
    # 模擬 5 天歷史數據，實際應串接您的資料源
    history_days = 5
    data = {
        'price': [19.64] * history_days,
        'x1': np.random.randint(6, 11, size=history_days), # 趨勢
        'x2': np.random.randint(5, 11, size=history_days), # 構造
        'x3': np.random.randint(4, 11, size=history_days), # 能量
    }
    df = pd.DataFrame(data)
    
    # 計算 PS 分數 (權重 3:4:3)
    df['ps'] = (df['x1']*0.3 + df['x2']*0.4 + df['x3']*0.3).round(1)
    
    # SBUY 判定 (AWI 核心邏輯)：X2>=7 且 價格 > MA20 (此處模擬)
    df['sbuy_active'] = df['x2'] >= 7 
    return df

# --- 2. 寬幅密集型卡片渲染器 (V32.9.55) ---
def render_apex_card(ticker, df):
    latest = df.iloc[-1]
    ps_score = latest['ps']
    
    # 1. PS 五日軌跡
    ps_hist = "→".join(df['ps'].astype(str).tolist())
    
    # 2. SBUY (AWI) 五日累積軌跡 (🔥/❄️)
    sbuy_hist = " ".join(["🔥" if s else "❄️" for s in df['sbuy_active'].tolist()])
    
    # 底色與文字判定
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "white", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "black", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "#FFFFFF", "black", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "white", "💀 快逃命啊"

    # HTML 密集封裝 (解決窄長與代碼外噴)
    card_html = f"""
    <div style="background-color:{bg}; border-radius:12px; padding:12px 16px; color:{txt}; border:1px solid #ddd; margin-bottom:15px; font-family: sans-serif; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); min-width: 200px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:18px;">{ticker}</b>
            <span style="font-size:18px;">{"🔥" if latest['sbuy_active'] else "❄️"}</span>
        </div>
        
        <div style="font-size:30px; font-weight:800; margin:5px 0;">${latest['price']}</div>
        
        <div style="border-top:1px solid {txt}44; margin:8px 0; padding-top:8px;">
            <div style="font-size:14px; font-weight:bold;">PS 軌跡 ({ps_score})</div>
            <div style="font-size:11px; opacity:0.8; margin-top:2px;">{ps_hist}</div>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-top:8px; background:rgba(0,0,0,0.05); padding:5px; border-radius:4px;">
            <div style="text-align:center;"><b>X1</b><br>30%<br>{latest['x1']}</div>
            <div style="text-align:center;"><b>X2</b><br>40%<br>{latest['x2']}</div>
            <div style="text-align:center;"><b>X3</b><br>30%<br>{latest['x3']}</div>
        </div>

        <div style="font-size:11px; margin-top:10px; padding:4px; border-left:3px solid {txt};">
            <b>SBUY (AWI) 五日軌跡:</b><br>
            <span style="font-size:14px; letter-spacing:2px;">{sbuy_hist}</span>
        </div>
        
        <div style="font-size:13px; margin-top:10px; font-weight:bold; text-align:right; text-transform:uppercase;">
            {label}
        </div>
    </div>
    """
    # ❗ 強制 HTML 渲染
    st.markdown(card_html, unsafe_allow_html=True)

# --- 3. 介面佈局 ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.9.55")

# 修正欄位比例：增加卡片橫向空間
col_left, col_right = st.columns([1.2, 4.8])

with col_left:
    st.subheader("🎯 偵察診斷")
    ticker_input = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        data_df = get_v32_data(ticker_input)
        render_apex_card(ticker_input, data_df)
        st.success(f"系統已自動累計 {ticker_input} 過去五日之 PS 與 SBUY 軌跡。")

with col_right:
    st.subheader("📊 11 大板塊監控區")
    tickers = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
    cols = st.columns(4) # 維持 4 欄，但整體佈局變寬
    for i, t in enumerate(tickers):
        with cols[i % 4]:
            render_apex_card(t, get_v32_data(t))
