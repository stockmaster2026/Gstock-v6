import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 核心指標手寫運算 (嚴格執行定錨邏輯，絕不簡化) ---
def get_indicators(df):
    # MA 均線
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    # RSI 14
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

# --- 2. 核心分析引擎 (F1, F2, F3 鎖定判定) ---
def analyze_v84_hardcore(ticker):
    try:
        # 抓取 300 天真實數據，不使用隨機值
        df = yf.download(ticker, period="300d", progress=False, timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # [F1: 技術共振] 
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        
        # [F2: 冠軍結構] (Stage 2 + MA200上升 + 52週高點25%內 + 底部起漲30% + 波動收縮)
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and ma200_up and (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and vcp
        
        # [F3: 主力足跡] (漲>1.3x/跌<0.8x + 口袋支點 + 20日吸籌)
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        # 口袋支點：今日量 > 過去10天最大跌量
        max_v_down = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]['Volume'].max()
        f3_vp = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and v_ratio > 0 and curr['Volume'] > (max_v_down if not np.isnan(max_v_down) else 0))
        # 20日吸籌天數 >= 派發天數
        acc = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vp and (acc >= dist)
        
        return {"price": float(curr['Close']), "score": sum([f1, f2, f3]), "f1": f1, "f2": f2, "f3": f3, "vol": v_ratio}
    except: return None

# --- 3. UI 介面 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")
st.title("🛡️ 三維戰略指揮中心 V8.4 (最終定錨版)")

# 核心板塊清單
SECTORS = {
    "🌈 光通訊核心": ["POET", "LITE", "COHR", "FN", "AAOI"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "💻 核心算力": ["NVDA", "AMD", "ARM", "TSM", "AVGO"],
    "🛰️ 太空經濟": ["RKLB", "PLTR", "ASTS", "LUNR"],
    "⚡ 能源電力": ["VST", "CEG", "OKLO", "SMR"],
    "🤖 機器人": ["TSLA", "PATH", "SYM"]
}

# 側邊欄：手動選擇板塊 (解決卡死問題)
st.sidebar.header("🕹️ 指揮控制")
selected_sector = st.sidebar.selectbox("請選擇偵察板塊", ["請選擇"] + list(SECTORS.keys()))

if selected_sector != "請選擇":
    st.header(f"📍 當前戰場：{selected_sector}")
    tickers = SECTORS[selected_sector]
    cols = st.columns(len(tickers))
    
    with st.spinner('正在調度即時數據...'):
        for i, t in enumerate(tickers):
            res = analyze_v84_hardcore(t)
            if res:
                bg = "#1E4620" if res['score'] == 3 else "#46461E" if res['score'] == 2 else "#461E1E"
                lbl = "🟢 進攻" if res['score'] == 3 else "🟡 觀察" if res['score'] == 2 else "🔴 撤退"
                cols[i].markdown(f"""
                    <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; min-height:200px; border:1px solid #555;">
                        <h2 style="color:#FFD700; margin:0;">{t}</h2>
                        <h3 style="margin:10px 0;">${res['price']:.2f}</h3>
                        <p style="font-size:14px;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                        <p style="font-size:12px;">量比: {res['vol']:.2f}x</p>
                        <hr style="opacity:0.3;">
                        <h4 style="margin:0;">{lbl}</h4>
                    </div>
                """, unsafe_allow_html=True)
            else:
                cols[i].error(f"{t} 連線超時")
else:
    st.info("請從左側選單選擇板塊，開始執行三維過濾偵察。")

