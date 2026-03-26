
import streamlit as st
import pandas as pd

# --- 系統定錨：V32.9.53 穩定框架 ---
st.set_page_config(layout="wide", page_title="精密戰略指揮中心 Final")

# --- 核心數據抓取函式 (這部分請對接你早上的實時數據源) ---
def fetch_data(ticker):
    # 這裡請確保對接你早上「跑得動」的數據來源
    # 暫時用基準數值讓你先看 11 板塊的佈局
    return {
        "Ticker": ticker, "Price": 100, "MA20": 95, 
        "X1": 8.5, "X2": 7.5, "X3": 6.0
    }

# --- 11 大板塊完整清單 (依照之前討論補全) ---
sectors = {
    "AI 醫療/生物": ["TEM", "AIH", "RX", "SDGR"],
    "科技領航 (核心)": ["TSLA", "NVDA", "AMD", "AAPL"],
    "大數據/AI 平台": ["PLTR", "MSFT", "GOOGL", "SNOW"],
    "量子計算 (前瞻)": ["IONQ", "RGTI", "QUBT"],
    "航太/防禦系統": ["KTOS", "RKLB", "LMT", "GD"],
    "半導體設備": ["ASML", "AMAT", "LRCX", "KLAC"],
    "能源/核能轉型": ["OKLO", "SMR", "VST", "CEG"],
    "網路安全": ["CRWD", "PANW", "FTNT", "ZS"],
    "金融科技": ["SQ", "PYPL", "SOFI", "COIN"],
    "電動車鏈/電池": ["RIVN", "LCID", "CHPT", "QS"],
    "戰略特選": ["U", "PATH", "MSTR", "HOOD"]
}

st.title("🛡️ 精密戰略指揮中心 (11大板塊實時監控)")

# --- 側邊欄：偵察輸入區 ---
with st.sidebar:
    st.header("🎯 戰略指揮部")
    selected_sector = st.selectbox("選擇監控板塊", list(sectors.keys()))
    st.write("---")
    st.info("版本：V32.9.53 Final\n模式：實時數據抓取")

# --- 右側主畫面：板塊監控區 ---
cols = st.columns(4) # 一行顯示 4 檔股票
tickers = sectors[selected_sector]

for i, t in enumerate(tickers):
    # 1. 抓取數據
    raw = fetch_data(t)
    
    # 2. 計算 PS 分數 (40/30/30) 與 SBUY 點火
    ps = (raw['X1'] * 0.3) + (raw['X2'] * 0.4) + (raw['X3'] * 0.3)
    fire = raw['X2'] >= 7.0 and raw['Price'] > raw['MA20']
    
    # 3. 根據 PS 與 🔥 判定「底色與白話文」
    if ps >= 9.0:
        bg, text, sub = "#1E4620", "🚀 起飛衝鋒", ("🔥 強烈持有" if fire else "❄️ 🧐 乖離修正")
        font_c = "white"
    elif 7.0 <= ps < 9.0:
        bg, text, sub = "#2E7D32", "🚩 趨勢啟動", ("🔥 標準加碼" if fire else "❄️ ⚠️ 動能衰竭")
        font_c = "white"
    elif 5.0 <= ps < 7.0:
        bg, text, sub = "#FFFFFF", "✨ 完美伏擊", ("🔥 主力已動手" if fire else "❄️ 😴 靜默等待")
        font_c = "black"
    else:
        bg, text, sub = "#4E342E", "💀 快逃命啊", ("🐍 誘多陷阱" if fire else "❄️ 絕對空手")
        font_c = "white"

    # 4. 渲染卡片 (密集型設計)
    with cols[i % 4]:
        st.markdown(f"""
            <div style="background-color:{bg}; color:{font_c}; padding:15px; border-radius:10px; border:1px solid #ccc; margin-bottom:12px; height: 160px;">
                <h3 style="margin:0; font-size: 1.2em;">{t} {sub.split()[0]}</h3>
                <p style="font-size:1.1em; font-weight:bold; margin:5px 0;">{text}</p>
                <p style="font-size:0.85em; margin:0; opacity: 0.9;">{sub.split(' ', 1)[1] if ' ' in sub else ''}</p>
                <hr style="margin:8px 0; border:0; border-top:1px solid {font_c}; opacity: 0.2;">
                <div style="display:flex; justify-content:space-between; font-size:0.75em;">
                    <span><b>PS: {ps:.1f}</b></span>
                    <span>X1:{raw['X1']} | X2:{raw['X2']} | X3:{raw['X3']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
