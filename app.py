import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🛡️ 三維戰略 V7.0", layout="wide")

# CSS 強化：極大化代號、氣候標籤與戰略顏色
st.markdown("""
    <style>
    .sector-card { background-color: #112233; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #445566; }
    .sentiment-hot { color: #FF4B4B; font-size: 24px; font-weight: bold; }
    .sentiment-cold { color: #1E90FF; font-size: 24px; font-weight: bold; }
    .stock-id { font-size: 55px !important; font-weight: bold; color: #FFD700; margin-bottom: -10px; }
    .status-badge { padding: 10px; border-radius: 8px; font-size: 18px; font-weight: bold; margin-top: 10px; }
    .action-buy { background-color: #007A33; color: white; }
    .action-sell { background-color: #A50021; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 1. 定義六大戰略板塊與精銳部隊
SECTORS = {
    "核心算力 (AI Core)": ["NVDA", "AVGO", "AMD", "ARM"],
    "矽光子 (Optical)": ["POET", "LUKE", "ALTR", "MARV"],
    "量子計算 (Quantum)": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "晶圓基礎 (Foundry)": ["TSM", "ASML", "AMAT", "INTC"],
    "終端應用 (Big Tech)": ["MSFT", "AAPL", "GOOGL", "META"],
    "AI 能源 (Power)": ["VST", "OKLO", "SMR", "TLN"]
}

@st.cache_data(ttl=3600)
def get_stock_data(t):
    try:
        df = yf.download(t, period="40d", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        c = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        prev_c = float(df['Close'].iloc[-2])
        return {"price": c, "ma20": ma20, "is_bull": c > ma20, "change": ((c-prev_c)/prev_c)*100}
    except: return None

# 主標題
st.markdown("<h1 style='text-align: center;'>🛡️ 三維戰略指揮中心 V7.0</h1>", unsafe_allow_html=True)
st.divider()

# 2. 板塊氣候總表 (AI 掃描)
st.markdown("### 🌡️ 板塊氣候情雨表")
weather_cols = st.columns(6)
sector_results = {}

for i, (s_name, t_list) in enumerate(SECTORS.items()):
    bull_count = 0
    valid_count = 0
    details = []
    for t in t_list:
        data = get_stock_data(t)
        if data:
            valid_count += 1
            if data['is_bull']: bull_count += 1
            details.append((t, data))
    
    sector_results[s_name] = details
    # 計算板塊熱度
    heat_ratio = bull_count / valid_count if valid_count > 0 else 0
    with weather_cols[i]:
        if heat_ratio >= 0.75:
            weather = "🔥 沸騰"
            class_name = "sentiment-hot"
        elif heat_ratio >= 0.5:
            weather = "☀️ 晴朗"
            class_name = "sentiment-hot"
        elif heat_ratio >= 0.25:
            weather = "☁️ 多雲"
            class_name = "sentiment-cold"
        else:
            weather = "⛈️ 雷雨"
            class_name = "sentiment-cold"
        
        st.markdown(f"<div class='sector-card'><b>{s_name}</b><br><span class='{class_name}'>{weather}</span></div>", unsafe_allow_html=True)

st.divider()

# 3. 板塊詳細戰報 (縱向排列)
st.markdown("### 📡 全域戰場細節掃描")

for s_name, stocks in sector_results.items():
    with st.expander(f"📍 查看板塊詳情：{s_name}", expanded=True):
        cols = st.columns(4)
        for i, (t, data) in enumerate(stocks):
            with cols[i % 4]:
                st.markdown(f"<div class='stock-id'>{t}</div>", unsafe_allow_html=True)
                if data['is_bull']:
                    st.markdown(f"<div class='status-badge action-buy'>🚀 主升段<br>🔥 加碼進攻</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='status-badge action-sell'>📉 走跌段<br>🏃 全力撤退</div>", unsafe_allow_html=True)
                st.write(f"**價格：** ${data['price']:.2f} ({data['change']:+.2f}%)")

