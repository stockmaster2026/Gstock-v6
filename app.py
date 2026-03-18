import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- 1. 核心指標運算 (F1/F2/F3 定錨邏輯，絕對鎖定不修改) ---
def get_indicators(df):
    # MA 均線
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    # MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    # KD (14, 3, 3)
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
    df['D'] = df['K'].rolling(3).mean()
    return df

@st.cache_data(ttl=600)
def analyze_v84_final(ticker):
    try:
        # 使用更穩定的抓取參數與超時設定
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="300d", interval="1d", timeout=20)
        
        if df.empty or len(df) < 250:
            return None
            
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # F1: 技術共振 (20%)
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        
        # F2: 冠軍結構 (50%)
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and ma200_up and (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and vcp
        
        # F3: 主力足跡 (30%)
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        down_days = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]
        max_v_down = down_days['Volume'].max() if not down_days.empty else 0
        f3_vol = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and curr['Volume'] > max_v_down)
        acc = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vol and (acc >= dist)
        
        # 原始討論加權：F2(5) + F3(3) + F1(2)
        weighted_score = (int(f2) * 5.0) + (int(f3) * 3.0) + (int(f1) * 2.0)
        
        return {
            "price": float(curr['Close']), 
            "score": weighted_score, 
            "f1": f1, "f2": f2, "f3": f3, 
            "v_ratio": float(v_ratio), 
            "change": float(((curr['Close']-prev['Close'])/prev['Close'])*100)
        }
    except Exception as e:
        return None

# --- 2. 介面渲染 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")
st.title("🛡️ 三維戰略指揮中心 V8.4 (終極加權定錨版)")

SECTORS = {
    "🌈 光通訊核心": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算核心": ["IONQ", "RGTI", "QUBT"],
    "💻 核心算力": ["NVDA", "AMD", "TSM"]
}

# 🛠️ 加權晴雨表
st.subheader("📊 戰略加權晴雨表 (10分制)")
baro_cols = st.columns(len(SECTORS))
all_results = {}

for i, (name, tickers) in enumerate(SECTORS.items()):
    res_list = []
    for t in tickers:
        res = analyze_v84_final(t)
        res_list.append(res)
        time.sleep(0.5) # 加入防封鎖延遲
        
    valid_res = [r for r in res_list if r is not None]
    avg_score = sum([r['score'] for r in valid_res]) / len(valid_res) if valid_res else 0.0
    
    if avg_score >= 8.0: weather = "☀️ 強勢進攻"
    elif avg_score >= 5.0: weather = "🌤️ 震盪觀察"
    else: weather = "🌧️ 風險撤退"
    
    all_results[name] = {"avg": avg_score, "weather": weather, "data": res_list}
    baro_cols[i].metric(name, f"{avg_score:.1f} Pts", weather)

st.divider()

# 板塊細節
for name, info in all_results.items():
    st.header(name)
    cols = st.columns(6)
    for j, res in enumerate(info['data']):
        t_name = SECTORS[name][j]
        with cols[j % 6]:
            if res:
                bg = "#1E4620" if res['score'] >= 8 else "#46461E" if res['score'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; border:1px solid #555;">
                    <h3 style="margin:0; color:#FFD700;">{t_name}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:11px; color:#AAA;">漲跌:{res['change']:.1f}% | 量比:{res['v_ratio']:.2f}x</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:12px;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                    <p style="font-size:14px; font-weight:bold;">得分: {res['score']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"{t_name} 數據缺失")

