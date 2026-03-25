
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 0. 頁面配置 (沿用昨日 iPad 橫屏優化版) ---
st.set_page_config(layout="wide", page_title="Apex Ambush V32.5", page_icon="🛰️")

# 自定義 CSS 樣式
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1c2128; border: 1px solid #30363d; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心邏輯定錨：V32.5 (30/25/45 權重) ---
# A1: 趨勢(25%), A2: 構造(30%), A3: 能量(45%)
W = {'A1': 0.25, 'A2': 0.30, 'A3': 0.45}

def calculate_v32_5_logic(ticker, df):
    try:
        if df.empty or len(df) < 35: return 0, 0, 0, 0
        
        # 【修正 A1: 手動計算 MACD 斜率 - 抓 AAOI 類起漲】
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        m_val = macd_line.iloc[-1]
        m_prev = macd_line.iloc[-2]
        # 斜率向上(正在變好)給 7 分，站上零軸給 10 分
        a1_score = 10 if m_val > 0 else (7 if m_val > m_prev else 3)
        
        # 【修正 A2: 手動計算 MA 糾結度 - 5% 寬容度】
        ma10 = df['Close'].rolling(window=10).mean().iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        # 修正：只要在 5% 以內都視為高度擠壓 (VCP 型態核心)
        a2_score = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
        
        # 【修正 A3: 能量活化 - 權重 45% 核心加重】
        vol_avg = df['Volume'].rolling(10).mean().iloc[-1]
        vol_curr = df['Volume'].iloc[-1]
        # 偵測「窒息量」與「點火量」
        if vol_curr > vol_avg * 1.3: a3_score = 10   # 點火突破
        elif vol_curr < vol_avg * 0.7: a3_score = 5  # 窒息洗盤
        else: a3_score = 7
        
        final = (a1_score * W['A1'] + a2_score * W['A2'] + a3_score * W['A3'])
        return round(final, 1), a1_score, a2_score, a3_score
    except:
        return 0, 0, 0, 0

# --- 2. 側邊欄配置 ---
with st.sidebar:
    st.title("🛰️ 戰略指揮中心")
    main_tkr = st.text_input("📍 主控標的", "PL").upper()
    data_p = st.selectbox("📅 追蹤區間", ["6mo", "1y", "1mo"])
    st.divider()
    st.info("**V32.5 巔峰埋伏系統**\n- A1 趨勢: 25%\n- A2 構造: 30%\n- A3 能量: 45%")
    st.write("版本狀態: 🟢 邏輯已定錨")

# 11 檔板塊連動清單
sectors = {
    "AI 晶片": "NVDA", "AI 醫療": "TEM", "太空影像": "PL", "衛星通訊": "ASTS",
    "無人機": "KTOS", "光通訊": "AAOI", "低軌衛星": "LUNR", "AI 基礎": "ARM",
    "支付巨頭": "V", "國防科技": "LMT", "網通設備": "GLW"
}

# --- 3. 三欄式佈局 (昨日完整 UI) ---
col1, col2, col3 = st.columns([1.1, 2.3, 1.1])

# 【左欄】板塊連動自動掃描
with col1:
    st.subheader("📡 板塊即時監控")
    for label, t in sectors.items():
        try:
            s_df = yf.download(t, period="20d", progress=False)
            s_val, _, _, _ = calculate_v32_5_logic(t, s_df)
            color = "inverse" if s_val >= 8.5 else "normal"
            st.metric(f"{label} ({t})", f"{s_val} Pts", f"${round(s_df['Close'].iloc[-1], 2)}", delta_color=color)
        except:
            st.error(f"{t} 數據獲取失敗")
        st.write("---")

# 【中欄】主控圖表與儀表板
with col2:
    st.subheader(f"📊 {main_tkr} 戰略深度分析")
    m_df = yf.download(main_tkr, period=data_p)
    score, a1, a2, a3 = calculate_v32_5_logic(main_tkr, m_df)
    
    # 儀表板 (Gauge Chart)
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#1f77b4"},
               'steps': [{'range': [0, 5], 'color': "#30363d"},
                        {'range': [5, 8], 'color': "#f1c40f"},
                        {'range': [8, 10], 'color': "#27ae60"}]}))
    fig_g.update_layout(height=350, paper_bgcolor="#0e1117", font={'color': "white"}, margin=dict(l=30, r=30, t=50, b=0))
    st.plotly_chart(fig_g, use_container_width=True)
    
    # K 線圖
    fig_k = go.Figure(data=[go.Candlestick(x=m_df.index, open=m_df['Open'], high=m_df['High'], low=m_df['Low'], close=m_df['Close'])])
    fig_k.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_k, use_container_width=True)

# 【右欄】診斷與實戰建議
with col3:
    st.subheader("🧪 核心診斷 (V32.5)")
    st.write(f"**A1 趨勢得分:** {a1}/10")
    st.progress(a1/10)
    st.write(f"**A2 構造得分:** {a2}/10")
    st.progress(a2/10)
    st.write(f"**A3 能量得分:** {a3}/10")
    st.progress(a3/10)
    
    st.divider()
    # 基於 A3 45% 權重的動態評語
    if a3 == 10:
        st.success("🔥 **點火訊號**：能量噴發突破，主力資金進場標記。")
    elif a3 == 5:
        st.warning("🌫️ **窒息訊號**：量能極度縮減，正在進行深層洗盤。")
    else:
        st.info("☀️ **平穩訊號**：能量結構正常修復中。")
        
    st.divider()
    st.markdown("""
    ### 🛡️ 實戰策略建議
    1. **AAOI 類奇襲**：觀察 A3 是否從 5 (窒息) 突然跳至 10 (噴發)。
    2. **LUNR 類陷阱**：若 A2 分數高但 A3 長期處於 5-7，代表「有型無量」，需警惕。
    3. **出局條件**：總分跌破 6.5 或 A3 出現背離。
    """)
