import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

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
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
    df['D'] = df['K'].rolling(3).mean()
    return df

@st.cache_data(ttl=600)
def analyze_v85(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", interval="1d", timeout=20)
        if df.empty or len(df) < 200: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # F1/F2/F3 定錨
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and ma200_up and (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and vcp
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        max_v_down = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]['Volume'].max() if not df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']].empty else 0
        f3_vol = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and curr['Volume'] > max_v_down)
        acc = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vol and (acc >= dist)
        
        # 加權得分 (F2:5, F3:3, F1:2)
        score = (int(f2)*5) + (int(f3)*3) + (int(f1)*2)
        return {"price": curr['Close'], "score": score, "f1": f1, "f2": f2, "f3": f3, "v_ratio": v_ratio, "change": ((curr['Close']-prev['Close'])/prev['Close'])*100}
    except: return None

# --- 2. 指揮中心介面 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.5", layout="wide")
st.title("🛡️ 三維戰略指揮中心 V8.5")

# 擴充後的板塊清單
SECTORS = {
    "🌈 光通訊核心": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D wave"],
    "💻 核心算力/AI": ["NVDA", "AMD", "TSM", "AVGO", "SMCI"],
    "🚀 太空經濟": ["RKLB", "PL", "ASTS", "SPIR"],
    "🤖 機器人/設備": ["ASML", "AMAT", "LRCX", "ISR"],
    "⚡ 能源轉型": ["VST", "CEG", "NNE", "OKLO"]
}

# 執行分析
st.subheader("📊 戰略加權晴雨表 (10分制)")
baro_cols = st.columns(len(SECTORS))
all_data = {}

for i, (name, tickers) in enumerate(SECTORS.items()):
    results = []
    for t in tickers:
        res = analyze_v85(t)
        results.append(res)
        time.sleep(0.3) # 緩衝
    
    valid = [r for r in results if r is not None]
    avg = sum([r['score'] for r in valid]) / len(valid) if valid else 0.0
    weather = "☀️ 強勢" if avg >= 8 else "🌤️ 震盪" if avg >= 5 else "🌧️ 風險"
    
    all_data[name] = {"avg": avg, "weather": weather, "results": results}
    baro_cols[i].metric(name, f"{avg:.1f} Pts", weather)

st.divider()

# 個股渲染 (強化視覺清晰度)
for name, info in all_data.items():
    st.header(name)
    cols = st.columns(6)
    for j, res in enumerate(info['results']):
        t_name = SECTORS[name][j]
        with cols[j % 6]:
            if res:
                # 根據得分決定背景，但文字統一強化為白色
                bg = "#1E4620" if res['score'] >= 8 else "#46461E" if res['score'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; border:1px solid #555; color: white;">
                    <h3 style="margin:0; color:#FFD700; font-size:22px;">{t_name}</h3>
                    <p style="font-size:24px; font-weight:bold; margin:5px 0; color: #FFFFFF; text-shadow: 1px 1px 2px black;">${res['price']:.2f}</p>
                    <p style="font-size:13px; color:#EEEEEE; margin:0;">漲跌:{res['change']:.1f}% | 量比:{res['v_ratio']:.2f}x</p>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:14px; margin:0;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                    <p style="font-size:16px; font-weight:bold; margin-top:5px; color:#FFD700;">得分: {res['score']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"{t_name} 獲取失敗")

