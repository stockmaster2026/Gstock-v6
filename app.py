import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (F1/F2/F3 定錨邏輯) ---
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
def analyze_v92(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
        vol_r = float(curr['Volume'] / df['Volume'].tail(10).mean())

        # F2 價格結構 (50% - 5分)
        f2_v = (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985)
        f2_s = 5 if f2_v else 0
        
        # F3 主力籌碼 (30% - 3分)
        f3_v = (p > prev['Close'] and vol_r > 1.2) or (p < prev['Close'] and vol_r < 0.8)
        f3_s = 3 if (f3_v and rsi > 45) else 0
        
        # F1 技術共振 (20% - 2分)
        f1_v = (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20)
        f1_s = 2 if f1_v else 0

        total = f2_s + f3_s + f1_s
        
        # --- 戰略狀態與動作判定 (定錨執行) ---
        if total >= 10:
            stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8:
            stat, cmd = "✅ 積極建倉", "建立 1/2 倉位 / 分批加碼"
        elif total >= 5:
            stat, cmd = "🟡 試探摸索", "建立 1/4 底倉 / 嚴守停損"
        elif total >= 3:
            stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else:
            stat, cmd = "❌ 權利撤退", "清倉空手 / 嚴禁買入"
            
        return {
            "p": p, "r": rsi, "s": total, "stat": stat, "cmd": cmd,
            "d1": f"F1 技術(20%): {'✅' if f1_s==2 else '❌'} {f1_s}/2",
            "d2": f"F2 結構(50%): {'✅' if f2_s==5 else '❌'} {f2_s}/5",
            "d3": f"F3 籌碼(30%): {'✅' if f3_s==3 else '❌'} {f3_s}/3",
            "ch": ((p-prev['Close'])/prev['Close'])*100
        }
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V9.2 戰略指揮中心", layout="wide")
st.sidebar.title("🕹️ 戰略控制台")
custom_t = st.sidebar.text_input("🔍 自定義查詢 (如: PLTR)", "").upper()

st.title("🛡️ 三維戰略指揮中心 V9.2")
st.markdown("### 📊 科學權重：F2 結構(50%) + F3 籌碼(30%) + F1 技術(20%)")

# 板塊清單
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

# 自定義查詢渲染
if custom_t:
    res = analyze_v92(custom_t)
    if res:
        st.info(f"🎯 {custom_t} 報告：{res['stat']} | 指令：{res['cmd']}")

# 11 板塊渲染
for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v92(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:10px; text-align:center; color:white; border:1px solid #555;">
                    <h3 style="margin:0; font-size:16px;">{t}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:10px; text-align:left;">{res['d2']}</p>
                    <p style="font-size:10px; text-align:left;">{res['d3']}</p>
                    <p style="font-size:10px; text-align:left;">{res['d1']}</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:15px; font-weight:bold; color:#FFD700;">{res['s']} Pts | {res['stat']}</p>
                    <p style="font-size:11px; margin-top:3px;"><b>👉 {res['cmd']}</b></p>
                </div>
                """, unsafe_allow_html=True)

