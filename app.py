
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 核心邏輯定錨：數據自動累積 (V32.9.54) ---
# 確保軌跡數據是從 DataFrame 動態產生的，嚴禁绑死數據
def get_metrics_from_df(ticker, mock=False):
    """
    實際運作時應從資料庫抓取 df，這裡用 mock 模擬。
     mock_df 的每一列代表一天，tail(1) 即為當日最新數據。
    """
    if mock:
        # 模擬過去 5-10 天的數據，確保軌跡自動累積生成
        data = {
            'Close': np.random.uniform(18.0, 20.0, size=10).round(2),
            'X1': np.random.randint(5, 11, size=10), # 趨勢得分
            'X2': np.random.randint(4, 11, size=10), # 構造得分
            'X3': np.random.randint(4, 11, size=10), # 能量得分
            'MA20': [18.5] * 10 # 假設均線位置
        }
    else:
        # 這裡是您實際串接 API 抓取數據的地方
        # data = fetch_real_data(ticker)
        data = {} # 暫代
        
    df = pd.DataFrame(data)
    
    # 根據 V32.9 權重動態計算 PS 分數: X1*0.3 + X2*0.4 + X3*0.3
    df['PS'] = (df['X1']*0.3 + df['X2']*0.4 + df['X3']*0.3).round(1)
    
    # SBUY 點火判定: X2 >= 7.0 且價格在 MA20 之上
    df['SBUY'] = (df['X2'] >= 7.0) & (df['Close'] > df['MA20'])
    
    # AWI 符號生成 (依據 PS 分數)
    conditions = [df['PS'] >= 9, df['PS'] >= 7, df['PS'] >= 5]
    icons = ['🎆', '☀️', '☁️', '🌫️']
    df['AWI_Icon'] = np.select(conditions, icons[:3], default='🌫️')
    
    return df

# --- 2. 密集型卡片組件 (不溢出設計，修正 HTML 噴出問題) ---
def render_stock_card(ticker, df):
    # 抓取最新數據
    latest = df.iloc[-1]
    ps_score = latest['PS']
    x1, x2, x3 = latest['X1'], latest['X2'], latest['X3']
    
    # 提取五日軌跡 (自動累積顯示)
    ps_history = df['PS'].tail(5).tolist()
    awi_history = df['AWI_Icon'].tail(5).tolist()
    
    # 判定底色與診斷字串
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "white", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "black", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "white", "black", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "white", "💀 快逃命啊"
    
    # 點火訊號
    fire_icon = "🔥" if latest['SBUY'] else "❄️"
    
    # 軌跡字串化 (密集顯示)
    ps_str = "→".join([str(round(x, 1)) for x in ps_history])
    awi_str = " ".join(awi_history)

    # 組合密集型 HTML (font-size 密集化，line-height 縮小)
    html_code = f"""
    <div style="background-color:{bg}; border-radius:8px; padding:10px; color:{txt}; border:1px solid #ddd; margin-bottom:10px; line-height:1.1; font-family: sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:16px;">{ticker}</b>
            <span style="font-size:18px;">{fire_icon}</span>
        </div>
        <div style="font-size:28px; font-weight:bold; margin:6px 0;">${latest['Close']}</div>
        
        <div style="font-size:12px; border-top:0.5px solid {txt}77; padding-top:6px; font-weight:bold; opacity:0.9;">
            PS: {ps_score} <span style="font-size:10px; font-weight:normal;">({ps_str})</span>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-top:5px; font-weight:600;">
            <span>X1:{x1}(30%)</span>
            <span>X2:{x2}(40%)</span>
            <span>X3:{x3}(30%)</span>
        </div>

        <div style="font-size:11px; margin-top:8px; background:rgba(0,0,0,0.08); padding:4px; border-radius:4px;">
            <b>AWI 軌跡:</b> {awi_str}
        </div>
        
        <div style="font-size:12px; margin-top:6px; font-weight:bold; text-align:right;">
            {label}
        </div>
    </div>
    """
    
    # 🛠️ [關鍵修正]：這裡必須啟用 unsafe_allow_html=True，否則會噴原始碼
    st.markdown(html_code, unsafe_allow_html=True)

# --- 3. 頁面佈局架構 ---
st.set_page_config(layout="wide")
st.title("🚀 Apex Ambush V32.9.54 偵察系統")

col_left, col_right = st.columns([1, 3])

# 準備模擬數據 (此處應換成您真實的數據字典)
monitors = ["AAOI", "GLW", "AVGO", "RKLB", "LUNR", "ONDS", "KTOS", "OKLO"]
data_repo = {t: get_metrics_from_df(t, mock=True) for t in monitors}

with col_left:
    st.subheader("🎯 執行偵察診斷")
    input_ticker = st.text_input("輸入代號", value="LUNR").upper()
    if st.button("啟動分析"):
        # 抓取最新數據與軌跡
        target_df = data_repo.get(input_ticker, data_repo["LUNR"])
        latest = target_df.iloc[-1]
        
        # 顯示完整數據卡片
        render_stock_card(input_ticker, target_df)
        
        # 顯示下方的白話文分析
        st.info(f"**戰情情報：** {input_ticker} 目前處於{latest['PS']}分，X2構造判定為{latest['X2']}，{'主力已點火' if latest['SBUY'] else '目前靜默'}。")
        st.markdown("---")
        st.write("* **判定：🚩 趨勢啟動**。標線站穩。建議標準加碼，守住 20MA。")

with col_right:
    st.subheader("📊 11 大板塊監控區")
    cols = st.columns(4)
    for i, t in enumerate(monitors):
        with cols[i % 4]:
            render_stock_card(t, data_repo[t])
