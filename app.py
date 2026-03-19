
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (科學定錨) ---
def get_indicators(df):
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    return df

@st.cache_data(ttl=600)
def analyze_v90_final(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
        vol_r = float(curr['Volume'] / df['Volume'].tail(10).mean())

        # --- F2 價格結構 (權重 50% - 5分) ---
        f2_v = (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985)
        f2_s = 5 if f2_v else 0
        
        # --- F3 主力足跡 (權重 30% - 3分) ---
        f3_v = (p > prev['Close'] and vol_r > 1.2) or (p < prev['Close'] and vol_r < 0.8)
        f3_s = 3 if (f3_v and rsi > 45) else 0
        
        # --- F1 技術買點 (權重 20% - 2分) ---
        f1_v = (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20)
        f1_s = 2 if f1_v else 0

        total = f2_s + f3_s + f1_s
        action = "🔥 全力進攻" if total >= 8 else "🟡 試探建倉" if total >= 5 else "❌ 權利撤退"
        
        return {
            "p": p, "r": rsi, "s": total, "act": action,
            "d1": "✅買點" if f1_s==2 else "❌弱勢",
            "d2": "✅結構" if f2_s==5 else "❌損毀",
            "d3": "✅主力" if f3_s==3 else "❌散亂",
            "s1": f1_s, "s2": f2_s, "s3": f3_s,
            "ch": ((p-prev['Close'])/prev['Close'])*100
        }
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V9.0 戰略指揮中心", layout="wide")

# 🕹️ 自定義查詢按鈕 (側邊欄)
st.sidebar.title("🕹️ 戰略控制台")
custom_t = st.sidebar.text_input("🔍 輸入股票代碼查詢 (如: PLTR, TSLA)", "").upper()

st.title("🛡️ 三維戰略指揮中心 V9.0")
st.markdown("### 📊 科學權重公示：F2 結構(50%) + F3 主力(30%) + F1 技術(20%)")

# 處理自定義查詢
if custom_t:
    res = analyze_v90_final(custom_t)
    if res:
        st.success(f"🎯 {custom_t} 報告：{res['act']} | 總分: {res['s']}/10")
        st.write(f"F2 結構 (50%): {res['d2']} ({res['s2']}/5) | F3 主力 (30%): {res['d3']} ({res['s3']}/3) | F1 技術 (20%): {res['d1']} ({res['s1']}/2)")
    else: st.error("查無數據")

st.divider()

# --- 11 大完整板塊 ---
SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "🚀 太空經濟": ["RKLB", "ASTS", "SPIR", "BKSY"],
    "💻 核心算力": ["NVDA", "AMD", "AVGO", "TSM"],
    "🤖 機器人/AI": ["ASML", "AMAT", "LRCX", "ISRG"],
    "⚡ 能源轉型": ["VST", "CEG", "NNE", "OKLO"],
    "🧬 生物/醫療": ["TEM", "RXRX", "DNA", "MNA"],
    "☁️ 雲端軟體": ["PLTR", "SNOW", "CRM", "MSFT"],
    "🚗 電動車/傳產": ["TSLA", "RIVN", "F", "GM"],
    "🛰️ 國防安全": ["KTOS", "LMT", "LHX"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

# 渲染卡片
for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v90_final(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:10px; text-align:center; color:white; border:1px solid #555;">
                    <h3 style="margin:0; font-size:16px;">{t}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:10px; text-align:left;">F2(50%): {res['d2']} <b>{res['s2']}/5</b></p>
                    <p style="font-size:10px; text-align:left;">F3(30%): {res['d3']} <b>{res['s3']}/3</b></p>
                    <p style="font-size:10px; text-align:left;">F1(20%): {res['d1']} <b>{res['s1']}/2</b></p>
                    <p style="font-size:14px; font-weight:bold; color:#FFD700; margin-top:5px;">總分：{res['s']} Pts</p>
                </div>
                """, unsafe_allow_html=True)
