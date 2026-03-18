
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- 1. 核心指標運算 (定錨邏輯：嚴禁修改) ---
def get_indicators(df):
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
def analyze_v85_strategy(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=20)
        if df.empty or len(df) < 252: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # --- F1: 技術共振 (20%) ---
        c_f1 = [
            curr['Close'] > curr['MA20'] * 1.015, # MA20 1.5% 緩衝
            curr['MACD_h'] > 0,                   # MACD 翻紅
            curr['K'] > curr['D'],                # KD 金叉
            50 <= curr['RSI'] <= 70               # RSI 強勢區
        ]
        f1 = all(c_f1)
        diag_f1 = "技術共振" if f1 else "指標疲弱"
        
        # --- F2: 冠軍結構 (50%) ---
        ma_order = curr['MA20'] > curr['MA50'] > curr['MA200']
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std() # 波動收縮
        near_high = curr['Close'] > high_52 * 0.75 # 52週高點25%內
        f2 = ma_order and ma200_up and vcp and near_high
        diag_f2 = "Stage 2 強勢" if f2 else "結構調整中"
        
        # --- F3: 主力足跡 (30%) ---
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        # 口袋支點：上漲放量蓋過近期最大跌量
        max_v_down = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]['Volume'].max() if not df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']].empty else 0
        f3_vol = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and curr['Volume'] > max_v_down)
        acc_days = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist_days = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vol and (acc_days >= dist_days)
        diag_f3 = "主力進場" if f3 else "縮量洗盤" if (not is_up and v_ratio < 0.8) else "籌碼渙散"
        
        # 加權得分 5:3:2
        score = (int(f2)*5) + (int(f3)*3) + (int(f1)*2)
        
        # --- 加減碼戰略建議 ---
        if score >= 10: 
            action = "🔥 全力進攻：F123三維共振，重倉持有。"
        elif score >= 8: 
            action = "✅ 積極加碼：趨勢確立，動能充足。"
        elif score >= 5: 
            action = "🟡 試探建倉：結構尚可，分批布局。"
        elif score > 0: 
            action = "⚠️ 觀望/減碼：部分指標背離，不宜躁進。"
        else: 
            action = "❌ 撤退空倉：不符戰略邏輯，保護資金。"
            
        return {
            "price": curr['Close'], "score": score, "action": action,
            "f1": f1, "f2": f2, "f3": f3,
            "df1": diag_f1, "df2": diag_f2, "df3": diag_f3,
            "v_ratio": v_ratio, "change": ((curr['Close']-prev['Close'])/prev['Close'])*100
        }
    except: return None

# --- 2. 介面設計 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.5", layout="wide")
st.sidebar.title("🕹️ 戰略控制台")
custom_ticker = st.sidebar.text_input("🔍 自定義偵察代碼 (如: NVDA)", "").upper()

st.title("🛡️ 三維戰略指揮中心 V8.5")

# 渲染自定義診斷
if custom_ticker:
    st.header(f"🎯 戰略對帳：{custom_ticker}")
    res = analyze_v85_strategy(custom_ticker)
    if res:
        st.subheader(f"戰略建議：{res['action']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("價格/漲跌", f"${res['price']:.2f}", f"{res['change']:.1f}%")
        c2.metric("加權總分", f"{res['score']} Pts", "滿分 10")
        c3.metric("主力動能", f"{res['v_ratio']:.2f}x", "量比")
        st.write(f"📊 **診斷細節**：F1-{res['df1']} | F2-{res['df2']} | F3-{res['df3']}")
    st.divider()

# --- 原始板塊清單 ---
SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "🚀 太空經濟": ["RKLB", "PLTR", "ASTS", "SPIR"],
    "💻 核心算力": ["NVDA", "AMD", "TSM", "AVGO"]
}

# 晴雨表
cols = st.columns(len(SECTORS))
for i, (name, tickers) in enumerate(SECTORS.items()):
    results = [analyze_v85_strategy(t) for t in tickers]
    valid = [r for r in results if r is not None]
    avg = sum([r['score'] for r in valid]) / len(valid) if valid else 0.0
    weather = "☀️" if avg >= 8 else "🌤️" if avg >= 5 else "🌧️"
    cols[i].metric(name, f"{avg:.1f} Pts", weather)

st.divider()

# 板塊明細卡片
for name, tickers in SECTORS.items():
    st.header(name)
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v85_strategy(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['score'] >= 8 else "#46461E" if res['score'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; color:white; border:1px solid #555;">
                    <h3 style="margin:0; color:#FFD700;">{t}</h3>
                    <p style="font-size:24px; font-weight:bold; color:white; text-shadow:1px 1px 2px black;">${res['price']:.2f}</p>
                    <p style="font-size:12px; margin:0;">{res['change']:.1f}% | 量:{res['v_ratio']:.2f}x</p>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:12px; color:#FFD700;"><b>建議：{res['action'].split('：')[0]}</b></p>
                    <p style="font-size:11px; text-align:left;">F1:{'✅' if res['f1'] else '❌'} {res['df1']}</p>
                    <p style="font-size:11px; text-align:left;">F2:{'✅' if res['f2'] else '❌'} {res['df2']}</p>
                    <p style="font-size:11px; text-align:left;">F3:{'✅' if res['f3'] else '❌'} {res['df3']}</p>
                </div>
                """, unsafe_allow_html=True)
