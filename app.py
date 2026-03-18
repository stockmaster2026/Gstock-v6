import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")

# --- 2. 核心指標手寫運算 (定錨邏輯：嚴格鎖定 F1/F2/F3，絕不修改) ---
def get_indicators(df):
    # MA 均線
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    # RSI (14) -> F1 50-70 使用
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    # MACD 柱狀體 (12, 26, 9) -> F1 翻紅使用
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    # KD (14, 3, 3) -> F1 金叉使用
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
    df['D'] = df['K'].rolling(3).mean()
    return df

# --- 3. 分析引擎 (F1, F2, F3 鎖定判定) ---
@st.cache_data(ttl=1800)
def analyze_v84_core(ticker):
    try:
        df = yf.download(ticker, period="300d", progress=False, timeout=12)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # F1: 技術指標共振 (MA20站穩1.5% + MACD翻紅 + KD金叉 + RSI 50-70)
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and \
             (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        
        # F2: 冠軍操盤手價格結構 (Stage 2 + MA200上升 + 52週位能 + 波動收縮)
        ma200_up = df['MA200'].diff(20).iloc[-1] > 0
        vcp = df['Close'].tail(10).std() < df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and ma200_up and \
             (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and vcp
        
        # F3: 成交量過濾器-主力足跡 (漲>1.3x/跌<0.8x 或 口袋支點) 且 20日吸籌>=派發
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        # 口袋支點：今日量 > 過去10天最大跌日成交量
        down_days = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]
        max_v_down = down_days['Volume'].max() if not down_days.empty else 0
        f3_vol = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8) or (is_up and curr['Volume'] > max_v_down)
        # 20日吸籌判定
        acc = len(df.tail(20)[(df.tail(20)['Close'] > df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        dist = len(df.tail(20)[(df.tail(20)['Close'] < df.tail(20)['Open']) & (df.tail(20)['Volume'] > vol_avg10)])
        f3 = f3_vol and (acc >= dist)
        
        return {"price": curr['Close'], "score": sum([f1, f2, f3]), "f1": f1, "f2": f2, "f3": f3, "v_ratio": v_ratio, "change": ((curr['Close']-prev['Close'])/prev['Close'])*100}
    except: return None

# --- 4. 戰略板塊清單 ---
SECTORS = {
    "🌈 光通訊核心": ["POET", "LITE", "COHR", "FN", "AAOI"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "💻 核心算力": ["NVDA", "AMD", "ARM", "TSM"],
    "🛰️ 太空經濟": ["RKLB", "PLTR", "ASTS", "LUNR"],
    "⚡ 能源電力": ["VST", "CEG", "OKLO", "SMR"],
    "🛡️ 國防科技": ["LMT", "RTX", "NOC"],
    "🤖 機器人": ["TSLA", "PATH", "SYM"]
}

# --- 5. UI 渲染 ---
st.title("🛡️ 三維戰略指揮中心 V8.4")
st.caption(f"定錨邏輯鎖定：F1技術共振 | F2冠軍結構 | F3主力足跡 | 時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 全域戰略晴雨表
st.subheader("📊 戰略晴雨表")
baro_cols = st.columns(len(SECTORS))
for i, sector in enumerate(SECTORS.keys()):
    baro_cols[i].metric(sector, "偵察中", "Active")

st.divider()

# 板塊顯示 (全自動展開)
for sector, tickers in SECTORS.items():
    st.header(sector)
    cols = st.columns(6)
    for i, t in enumerate(tickers):
        res = analyze_v84_core(t)
        if res:
            bg = "#1E4620" if res['score'] == 3 else "#46461E" if res['score'] == 2 else "#461E1E"
            lbl = "🟢 進攻" if res['score'] == 3 else "🟡 觀察" if res['score'] == 2 else "🔴 撤退"
            with cols[i % 6]:
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; border:1px solid #555;">
                    <h3 style="margin:0; color:#FFD700;">{t}</h3>
                    <p style="font-size:18px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:11px; color:#AAA;">漲跌:{res['change']:.1f}% | 量比:{res['v_ratio']:.2f}x</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:12px;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                    <p style="font-size:14px; font-weight:bold;">{lbl}</p>
                </div>
                """, unsafe_allow_html=True)

if st.sidebar.button("🔄 強制刷新全域數據"):
    st.cache_data.clear()
    st.rerun()


