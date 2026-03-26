
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 定錨核心邏輯：動態計算 (V32.9.53) ---
def get_stock_metrics(ticker):
    """
    模擬從資料庫/API 抓取數據並計算。
    實際運作時應傳入真正的歷史 df。
    """
    # 這裡模擬過去 5 天的數據，確保軌跡是自動生成的
    dates = pd.date_range(end=pd.Timestamp.now(), periods=5)
    data = {
        'date': dates,
        'X1': np.random.randint(7, 11, size=5), # 趨勢對齊
        'X2': np.random.randint(6, 11, size=5), # 構造錨定
        'X3': np.random.randint(5, 11, size=5), # 能量活化
        'Price': [19.3, 19.5, 19.1, 18.9, 19.3], # 模擬股價
        'MA20': [18.5] * 5
    }
    df = pd.DataFrame(data)
    
    # 計算 PS: X1(30%) + X2(40%) + X3(30%)
    df['PS'] = (df['X1']*0.3 + df['X2']*0.4 + df['X3']*0.3).round(1)
    
    # AWI 天氣判定 (根據 PS 分數)
    def get_awi(ps):
        if ps >= 9.0: return '🎆'
        if ps >= 7.0: return '☀️'
        if ps >= 5.0: return '☁️'
        return '🌫️'
    df['AWI'] = df['PS'].apply(get_awi)
    
    return df

# --- 2. 密集型卡片組件 (解決溢出問題) ---
def render_card(ticker, df):
    latest = df.iloc[-1]
    ps_score = latest['PS']
    x1, x2, x3 = latest['X1'], latest['X2'], latest['X3']
    
    # 底色判定
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "#FFFFFF", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "#000000", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "#FFFFFF", "#000000", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "#FFFFFF", "💀 快逃命啊"
    
    # SBUY 點火判定
    is_fire = (x2 >= 7) and (latest['Price'] > latest['MA20'])
    fire_icon = "🔥" if is_fire else "❄️"
    
    # 軌跡字串 (自動累積)
    ps_hist = "→".join(df['PS'].astype(str).tolist())
    awi_hist = " ".join(df['AWI'].tolist())

    st.markdown(f"""
    <div style="background-color:{bg}; border-radius:8px; padding:8px 10px; color:{txt}; border:1px solid #ddd; margin-bottom:8px; line-height:1.1;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:15px;">{ticker}</b>
            <span style="font-size:16px;">{fire_icon}</span>
        </div>
        <div style="font-size:22px; font-weight:bold; margin:2px 0;">${latest['Price']}</div>
        
        <div style="font-size:11px; border-top:0.5px solid {txt}44; padding-top:4px; font-weight:bold;">
            PS: {ps_score} <span style="font-size:9px; font-weight:normal; opacity:0.8;">({ps_hist})</span>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:10px; margin-top:2px; letter-spacing:-0.5px;">
            <span>X1:{x1}(30%)</span><span>X2:{x2}(40%)</span><span>X3:{x3}(30%)</span>
        </div>
        
        <div style="font-size:10px; margin-top:4px; background:rgba(0,0,0,0.04); padding:2px 4px; border-radius:3px;">
            <b>AWI 軌跡:</b> {awi_hist}
        </div>
        
        <div style="font-size:11px; margin-top:4px; font-weight:bold;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. 頁面佈局 ---
st.set_page_config(layout="wide")
col_left, col_right = st.columns([1, 3])

with col_left:
    st.subheader("🚀 執行偵察診斷")
    target = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        stock_df = get_stock_metrics(target)
        render_card(target, stock_df)
        
        # 白話文分析區
        st.markdown("---")
        latest = stock_df.iloc[-1]
        st.write(f"### {target} 戰情情報")
        st.write(f"* **判定**：{latest['PS']} 分，屬於強勢區間。")
        st.write(f"* **分析**：X2 構造得分 {latest['X2']}，{'符合點火條件' if latest['X2']>=7 else '仍需等待構造收縮'}。")

with col_right:
    st.subheader("📊 11 大板塊監控")
    monitors = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
    cols = st.columns(4)
    for i, t in enumerate(monitors):
        with cols[i % 4]:
            render_card(t, get_stock_metrics(t))
