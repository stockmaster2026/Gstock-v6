import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")

# --- 2. 核心指標運算 (F1/F2/F3 定錨邏輯，絕不修改) ---
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
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
    df['D'] = df['K'].rolling(3).mean()
    return df

@st.cache_data(ttl=600)
def analyze_v84(ticker):
    try:
        df = yf.download(ticker, period="300d", progress=False, timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # F1: MA20站穩1.5% + MACD翻紅 + KD金叉 + RSI 50-70
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        # F2: Stage 2 + MA200上升 + 52週位能 + 波動收縮
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and ma200_up and (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and vcp
        # F3: 主力足跡 (漲>1.3x/跌<0.8x + 口袋支點 + 吸籌)
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        max_v_down = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]['Volume'].max()
        f3_vol = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and curr['Volume'] > max_v_down)
        acc = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vol and (acc >= dist)
        
        return {"price": curr['Close'], "score": sum([f1, f2, f3]), "f1": f1, "f2": f2, "f3": f3, "v_ratio": v_ratio, "change": ((curr['Close']-prev['Close'])/prev['Close'])*100}
    except: return "Error"

# --- 3. UI 渲染 ---
st.title("🛡️ 三維戰略指揮中心 V8.4")

SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT"],
    "💻 核心算力": ["NVDA", "AMD", "TSM"]
}

# 頂部戰略晴雨表
st.subheader("📊 戰略晴雨表")
baro_cols = st.columns(len(SECTORS))
for i, sector in enumerate(SECTORS.keys()):
    baro_cols[i].metric(sector, "偵察中", "Active")

st.divider()

for sector, tickers in SECTORS.items():
    st.header(sector)
    cols = st.columns(6)
    for i, t in enumerate(tickers):
        res = analyze_v84(t)
        with cols[i % 6]:
            if res == "Error":
                st.error(f"{t} 連線失敗")
            elif res:
                bg = "#1E4620" if res['score'] == 3 else "#46461E" if res['score'] == 2 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; border:1px solid #555;">
                    <h3 style="margin:0; color:#FFD700;">{t}</h3>
                    <p style="font-size:18px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:11px; color:#AAA;">{res['change']:.1f}% | 量:{res['v_ratio']:.2f}x</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:12px;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                </div>
                """, unsafe_allow_html=True)

if st.sidebar.button("🔄 強制刷新"):
    st.cache_data.clear()
    st.rerun()



