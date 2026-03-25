
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 0. 頁面配置：完全沿用昨天跑最順的 iPad 佈局 ---
st.set_page_config(layout="wide", page_title="Commander V32.5", page_icon="🛰️")

# 這裡是你最愛的自定義 CSS 外觀，一字不差
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1c2128; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心邏輯定錨：V32.5 (30/25/45 權重) ---
# 這是今早討論出的最理想權重與 MACD 斜率修正
W = {'A1': 0.25, 'A2': 0.30, 'A3': 0.45}

def calculate_apex_logic(ticker, df):
    try:
        if df.empty or len(df) < 35: return 0, 0, 0, 0
        
        # 【A1 趨勢：手動計算 MACD 斜率修正 - 解決 AAOI 漏球問題】
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        m_val = macd_line.iloc[-1]
        m_prev = macd_line.iloc[-2]
        # 修正：斜率轉正即給 7 分 (提前佈局)，零軸上 10 分
        a1 = 10 if m_val > 0 else (7 if m_val > m_prev else 3)
        
        # 【A2 構造：手動計算 MA 糾結 - 5% 寬容度修正 LUNR 誤判】
        ma10 = df['Close'].rolling(window=10).mean().iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        dist = abs(ma10 - ma20) / ma20
        # 修正：只要縮在 5% 以內都是高度壓縮 (VCP 核心)
        a2 = 10 if dist < 0.05 else (6 if dist < 0.1 else 2)
        
        # 【A3 能量：權重 45% 核心加重 - 抓點火與窒息】
        v_avg = df['Volume'].rolling(10).mean().iloc[-1]
        v_curr = df['Volume'].iloc[-1]
        if v_curr > v_avg * 1.3: a3 = 10   # 點火確認
        elif v_curr < v_avg * 0.7: a3 = 5  # 窒息洗盤
        else: a3 = 7
        
        score = (a1 * W['A1'] + a2 * W['A2'] + a3 * W['A3'])
        return round(float(score), 1), a1, a2, a3
    except:
        return 0, 0, 0, 0

# --- 2. 戰略標的與側邊欄 ---
sectors = {
    "AI 晶片": "NVDA", "AI 醫療": "TEM", "太空影像": "PL", "衛星通訊": "ASTS",
    "無人機": "KTOS", "光通訊": "AAOI", "低軌衛星": "LUNR", "AI 基礎": "ARM",
    "支付巨頭": "V", "國防科技": "LMT", "網通設備": "GLW"
}

with st.sidebar:
    st.title("🛰️ 指揮中心配置")
    main_tkr = st.text_input("📍 主控代號輸入", "PL").upper()
    data_p = st.selectbox("📅 數據溯源區間", ["6mo", "1y", "1mo"])
    st.divider()
    st.info(f"**V32.5 修正權重**\nA1 趨勢: 25% | A2 構造: 30% | A3 能量: 45%")
    st.write("環境狀態: 🟢 已避開依賴衝突")

# --- 3. 主畫面佈局 (昨日完整三欄式) ---
c1, c2, c3 = st.columns([1.1, 2.2, 1.2])

# 【左一欄】11 檔板塊連動掃描
with c1:
    st.subheader("📡 板塊即時監控")
    for label, t in sectors.items():
        try:
            s_df = yf.download(t, period="20d", progress=False)
            s_val, _, _, _ = calculate_apex_logic(t, s_df)
            color = "inverse" if s_val >= 8.5 else "normal"
            st.metric(f"{label} ({t})", f"{s_val} Pts", f"${round(s_df['Close'].iloc[-1], 2)}", delta_color=color)
        except:
            st.error(f"{t} 獲取失敗")
        st.write("---")

# 【中間欄】儀表板與核心圖表
with c2:
    st.subheader(f"📊 {main_tkr} 戰略深度分析")
    m_df = yf.download(main_tkr, period=data_p)
    score, a1, a2, a3 = calculate_apex_logic(main_tkr, m_df)
    
    # 指針儀表板
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#1f77b4"},
               'steps': [{'range': [0, 5], 'color': "#30363d"},
                        {'range': [5, 8], 'color': "#f1c40f"},
                        {'range': [8, 10], 'color': "#27ae60"}]}))
    fig_g.update_layout(height=350, paper_bgcolor="#0e1117", font={'color': "white"}, margin=dict(l=30, r=30, t=50, b=0))
    st.plotly_chart(fig_g, use_container_width=True)
    
    # 蠟燭 K 線
    fig_k = go.Figure(data=[go.Candlestick(x=m_df.index, open=m_df['Open'], high=m_df['High'], low=m_df['Low'], close=m_df['Close'])])
    fig_k.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_k, use_container_width=True)

# 【右一欄】三維診斷報告
with c3:
    st.subheader("🧪 系統診斷 (V32.5)")
    st.write(f"**A1 趨勢評分:** {a1}/10")
    st.progress(a1/10)
    st.write(f"**A2 構造評分:** {a2}/10")
    st.progress(a2/10)
    st.write(f"**A3 能量評分:** {a3}/10")
    st.progress(a3/10)
    
    st.divider()
    if a3 == 10: st.success("🔥 **點火確認**：能量噴發突破，主力資金進場。")
    elif a3 == 5: st.warning("🌫️ **窒息信號**：量能極度縮減，深層洗盤中。")
    else: st.info("☀️ **平穩信號**：能量結構正常修復。")
    
    st.divider()
    st.markdown("""
    ### 🛡️ 實戰防火牆
    1. **AAOI 類奇襲**：看 A3 是否從 5 突然跳 10。
    2. **PL 類穩健**：V26 > 8.5 且 A3 維持 7 以上。
    """)
