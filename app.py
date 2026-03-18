
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")

# --- 2. 11 大美股戰略板塊 (定案版) ---
SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN", "ACMR", "AAOI", "INFN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE", "QCI", "ARQQ"],
    "💾 存儲板塊": ["MU", "WDC", "STX", "PSTG", "NTAP", "SNDK"],
    "🛰️ 太空經濟": ["RKLB", "PLTR", "ASTS", "LUNR", "BKSY", "SPIR"],
    "💻 核心算力": ["NVDA", "AMD", "ARM", "TSM", "AVGO", "MRVL"],
    "⚡ 能源電力": ["VST", "CEG", "OKLO", "SMR", "TLN", "GEV"],
    "❄️ 液冷散熱": ["VRT", "SMCI", "MOD", "AAON", "JCI", "NVENT"],
    "🛡️ 國防科技": ["LMT", "RTX", "NOC", "LHX", "LDOS", "BWXT"],
    "🧬 生物 AI": ["RXRX", "SDGR", "EXAI", "ISRG", "AMGN", "VRTX"],
    "🤖 機器人": ["TSLA", "PATH", "SYM", "TER", "CGNX"],
    "📈 槓桿指數": ["SOXL", "TQQQ", "BITI", "SQQQ", "UPRO", "UVXY"]
}

# --- 3. 核心運算引擎 (手寫所有指標，確保不簡化) ---
def calculate_metrics(df):
    # MA 計算
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI 計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD 計算 (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_h'] = df['MACD'] - df['Signal']
    
    # KD 計算 (14, 3, 3)
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
    df['D'] = df['K'].rolling(window=3).mean()
    
    return df

@st.cache_data(ttl=3600)
def analyze_v84_hardcore(ticker):
    try:
        df = yf.download(ticker, period="300d", interval="1d", progress=False)
        if df.empty or len(df) < 250: return None
        df = calculate_metrics(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # [F1: 技術指標共振] - 鎖定內容：MA20緩衝、MACD翻紅、KD金叉、RSI 50-70
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and (curr['MACD_h'] > 0) and \
             (curr['K'] > curr['D']) and (50 <= curr['RSI'] <= 70)
        
        # [F2: 冠軍結構] - 鎖定內容：Stage 2、MA200上升、52週高點25%內、波動收縮
        ma200_slope = df['MA200'].diff(20).iloc[-1]
        std_10 = df['Close'].tail(10).std()
        std_30 = df['Close'].tail(30).std()
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and (ma200_slope > 0) and \
             (curr['Close'] > high_52 * 0.75) and (curr['Close'] > low_52 * 1.3) and (std_10 < std_30)
        
        # [F3: 主力足跡] - 鎖定內容：漲1.3x/跌0.8x、口袋支點、20日吸籌>派發
        is_up = curr['Close'] > prev['Close']
        v_ratio = curr['Volume'] / vol_avg10
        f3_std = (is_up and v_ratio > 1.3) or (not is_up and v_ratio < 0.8)
        max_down_v10 = df.tail(10)[df.tail(10).apply(lambda x: x['Close'] < x['Open'], axis=1)]['Volume'].max()
        f3_pocket = is_up and (curr['Volume'] > (max_down_v10 if not np.isnan(max_down_v10) else 0))
        recent20 = df.tail(20)
        acc = len(recent20[(recent20['Close'] > recent20['Open']) & (recent20['Volume'] > vol_avg10)])
        dist = len(recent20[(recent20['Close'] < recent20['Open']) & (recent20['Volume'] > vol_avg10)])
        f3 = (f3_std or f3_pocket) and (acc >= dist)
        
        score = sum([1 for f in [f1, f2, f3] if f])
        return {"price": curr['Close'], "change": ((curr['Close']-prev['Close'])/prev['Close'])*100,
                "score": score, "f1": f1, "f2": f2, "f3": f3, "vol_ratio": v_ratio}
    except: return None

# --- UI 渲染 (維持旗艦版豪華介面) ---
st.title("🛡️ 三維戰略指揮中心 V8.4 (定錨改寫版)")
st.markdown(f"**核心鎖定：** F1/F2/F3 科學指標 | **時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for sector, tickers in SECTORS.items():
    st.subheader(f"📍 {sector}")
    cols = st.columns(6)
    for i, t in enumerate(tickers):
        res = analyze_v84_hardcore(t)
        if res:
            with cols[i % 6]:
                bg = "#1E4620" if res['score'] == 3 else "#46461E" if res['score'] == 2 else "#461E1E"
                lbl = "🔥 全力進攻" if res['score'] == 3 else "⚠️ 謹慎持有" if res['score'] == 2 else "🚨 全力撤退"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:12px; border-radius:10px; border:1px solid #444; text-align:center; min-height:170px;">
                    <h4 style="margin:0; color:#FFD700;">{t}</h4>
                    <p style="font-size:22px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:11px;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                    <hr style="margin:8px 0; opacity:0.2;">
                    <p style="font-size:13px; font-weight:bold;">{lbl}</p>
                </div>
                """, unsafe_allow_html=True)

if st.sidebar.button("🔄 強制刷新"):
    st.cache_data.clear()
    st.rerun()
