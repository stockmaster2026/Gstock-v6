





import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- 0. 介面優化設定 ---
st.set_page_config(layout="wide", page_title="V32.5 Apex Ambush", page_icon="🛰️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心邏輯修正：權重 30/25/45 ---
W = {'A1': 0.25, 'A2': 0.30, 'A3': 0.45}

def run_apex_logic(ticker, df):
    try:
        if df.empty or len(df) < 35: return 0, 0, 0, 0
        
        # 【修正 A1: MACD 斜率邏輯】
        macd = df.ta.macd()
        m_val = macd.iloc[-1]['MACD_12_26_9']
        m_prev = macd.iloc[-2]['MACD_12_26_9']
        # 只要斜率向上(向上攻擊)就給 7 分，站上零軸給 10 分
        a1 = 10 if m_val > 0 else (7 if m_val > m_prev else 3)
        
        # 【修正 A2: 構造糾結度邏輯】
        ma10 = ta.sma(df['Close'], length=10)
        ma20 = ta.sma(df['Close'], length=20)
        diff = abs(ma10.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
        # 放寬門檻至 5%，專抓 VCP 壓縮
        a2 = 10 if diff < 0.05 else (6 if diff < 0.1 else 2)
        
        # 【修正 A3: 能量活化邏輯 - 權重 45%】
        v_avg = df['Volume'].rolling(10).mean().iloc[-1]
        v_curr = df['Volume'].iloc[-1]
        # 窒息量偵測與點火偵測
        if v_curr > v_avg * 1.3: a3 = 10   # 點火攻擊
        elif v_curr < v_avg * 0.7: a3 = 5  # 窒息洗盤
        else: a3 = 7
        
        score = (a1 * W['A1'] + a2 * W['A2'] + a3 * W['A3'])
        return round(score, 1), a1, a2, a3
    except: return 0, 0, 0, 0

# --- 2. 側邊欄與標的配置 ---
with st.sidebar:
    st.title("🛰️ 戰略指揮中心")
    main_ticker = st.text_input("📍 主控代號", "PL").upper()
    data_range = st.selectbox("📅 追蹤範圍", ["6mo", "1y", "1mo"])
    st.divider()
    st.write("**當前權重 (V32.5)**")
    st.write(f"A1 趨勢 (斜率修正): {W['A1']*100}%")
    st.write(f"A2 構造 (5% 糾結): {W['A2']*100}%")
    st.write(f"A3 能量 (核心加重): {W['A3']*100}%")

sectors = {
    "AI 晶片": "NVDA", "AI 醫療": "TEM", "太空影像": "PL", "衛星通訊": "ASTS",
    "無人機": "KTOS", "光通訊": "AAOI", "低軌衛星": "LUNR", "AI 基礎": "ARM",
    "支付巨頭": "V", "國防科技": "LMT", "網通設備": "GLW"
}

# --- 3. 三欄式佈局執行 ---
c1, c2, c3 = st.columns([1.1, 2.3, 1.1])

# 左欄：11 檔自動掃描
with c1:
    st.subheader("📡 板塊聯動")
    for label, t in sectors.items():
        data = yf.download(t, period="20d", progress=False)
        s, _, _, _ = run_apex_logic(t, data)
        st.metric(f"{label} ({t})", f"{s} Pts", f"{round(data['Close'].iloc[-1], 2)}")
        st.write("---")

# 中欄：K線與儀表板
with c2:
    st.subheader(f"📊 {main_ticker} 深度分析")
    m_df = yf.download(main_ticker, period=data_range)
    score, a1, a2, a3 = run_apex_logic(main_ticker, m_df)
    
    # 指針圖
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#2ecc71" if score > 8 else "#f1c40f"},
               'steps': [{'range': [0, 5], 'color': "#333"}, {'range': [5, 8], 'color': "#444"}]}))
    fig.update_layout(height=350, paper_bgcolor="#0e1117", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)
    
    # K線
    fig_k = go.Figure(data=[go.Candlestick(x=m_df.index, open=m_df['Open'], high=m_df['High'], low=m_df['Low'], close=m_df['Close'])])
    fig_k.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_k, use_container_width=True)

# 右欄：診斷報告
with c3:
    st.subheader("🧪 系統診斷")
    st.write(f"**A1 趨勢評分:** {a1}/10")
    st.progress(a1/10)
    st.write(f"**A2 構造評分:** {a2}/10")
    st.progress(a2/10)
    st.write(f"**A3 能量評分:** {a3}/10")
    st.progress(a3/10)
    st.divider()
    if a3 == 10: st.success("🔥 點火確認：能量強勁突破。")
    elif a3 == 5: st.warning("🌫️ 窒息信號：量能枯竭，主力洗盤。")
    else: st.info("☀️ 平穩區間：結構修復中。")
    st.divider()
    st.markdown("### 💡 實戰策略\n1. A3 從 5 轉 10 為最佳買點。\n2. 跌破 MA20 且 A3 < 7 應撤退。")

