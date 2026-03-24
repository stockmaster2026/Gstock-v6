
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面配置與舊版 V32 樣式還原 ---
st.set_page_config(page_title="Apex Ambush V32.5", page_icon="🛰️", layout="wide")

# 套用妳原本最熟悉的卡片式外觀 CSS
st.markdown("""
    <style>
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #f8fafc;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
    }
    .metric-label { font-size: 0.75rem; color: #64748b; }
    .metric-value { font-size: 1rem; font-weight: bold; color: #1e293b; }
    </style>
    """, unsafe_allow_code=True)

# --- 2. 左側 Sidebar 參數輸入 (完整保留妳原本的 Input 欄位) ---
st.sidebar.header("⚙️ 系統參數設定")
manual_tickers = st.sidebar.text_input(
    "監控標的 (請用逗號隔開)", 
    "AAOI, PL, LUNR, TSLA, NVDA, TSEM, CRDO, MSFT, GOOGL, META, AAPL"
)
WATCH_LIST = [t.strip().upper() for t in manual_tickers.split(",")]

ma_s = st.sidebar.number_input("A2 短均線 (10MA)", value=10)
ma_m = st.sidebar.number_input("F1 命脈線 (20MA)", value=20)
ma_l = st.sidebar.number_input("長均定錨 (50MA)", value=50)

st.sidebar.markdown("---")
st.sidebar.info("""
**V26.5 評分邏輯權重：**
- A1 趨勢 (MACD): 20%
- A2 構造 (均線糾結): 40%
- A3 能量 (RS + 成交量): 40%
""")

# --- 3. 原生指標計算引擎 (穩定不報錯版) ---
def get_indicators(df):
    try:
        if df is None or df.empty: return None
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 均線
        df['MA10'] = df['Close'].rolling(window=ma_s).mean()
        df['MA20'] = df['Close'].rolling(window=ma_m).mean()
        df['MA50'] = df['Close'].rolling(window=ma_l).mean()
        
        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        return df
    except: return None

# --- 4. 核心戰略評分：V26.5 三維度邏輯 ---
def get_apex_data(ticker, df, spy_df):
    try:
        if df is None or len(df) < 50: return None
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # A1 趨勢 (20%)
        a1_raw = 10 if latest['MACD'] > 0 else (6 if latest['MACD'] > prev['MACD'] else 0)
        a1_score = a1_raw * 0.2
        
        # A2 構造 (40%)
        mas = [float(latest['MA10']), float(latest['MA20']), float(latest['MA50'])]
        comp = (np.std(mas) / np.mean(mas)) * 100
        a2_raw = 10 if comp < 1.5 else (8 if comp < 3.0 else 4)
        a2_score = a2_raw * 0.4
        
        # A3 能量 (40%)
        vol_ratio = latest['Volume'] / df['Volume'].tail(10).mean()
        v_score = 5 if vol_ratio > 1.3 or vol_ratio < 0.5 else 0
        rs = ((latest['Close']/df.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close']))
        r_score = 5 if rs > 0.02 else (3 if rs > 0 else 0)
        a3_raw = v_score + r_score
        a3_score = a3_raw * 0.4
        
        total = round(a1_score + a2_score + a3_score, 1)
        
        # AWI 天氣與 F1 過濾
        awi_map = {9: ("🎆", "噴發態"), 7: ("☀️", "強勢態"), 5: ("☁️", "整理態"), 0: ("🌫️", "危險態")}
        icon, weather = next(v for k, v in awi_map.items() if total >= k)
        
        buffer = 0.05 if a3_raw >= 8 else 0.015
        f1_pass = abs(latest['Close'] - latest['MA20']) / latest['MA20'] <= buffer
        
        return {
            "tk": ticker, "ic": icon, "we": weather, "tt": total,
            "a1": a1_raw, "a1s": round(a1_score, 1),
            "a2": a2_raw, "a2s": round(a2_score, 1),
            "a3": a3_raw, "a3s": round(a3_score, 1),
            "f1": f1_pass, "cp": round(comp, 2), "rs": round(rs*100, 2),
            "vol": round(vol_ratio, 2), "pr": round(latest['Close'], 2)
        }
    except: return None

# --- 5. 畫面渲染：還原 11 個卡片式板塊 ---
st.title("🛰️ Apex Ambush V32.5 巔峰埋伏系統")

spy_data = get_indicators(yf.download("SPY", period="4mo", auto_adjust=True, progress=False))

if spy_data is not None:
    # 建立網格佈局，每橫排 3 個板塊
    for i in range(0, len(WATCH_LIST), 3):
        cols = st.columns(3)
        for j, ticker in enumerate(WATCH_LIST[i:i+3]):
            with cols[j]:
                raw = yf.download(ticker, period="4mo", auto_adjust=True, progress=False)
                df = get_indicators(raw)
                res = get_apex_data(ticker, df, spy_data)
                
                if res:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="font-size:1.5rem;">{res['ic']} {res['we']}</div>
                        <h2 style="margin:5px 0;">{res['tk']} <small style="font-size:1rem; color:#888;">${res['pr']}</small></h2>
                        <h1 style="color:#ff4b4b; margin:10px 0;">{res['tt']} <small style="font-size:1rem;">總分</small></h1>
                        <p style="background-color:{'#dcfce7' if res['f1'] else '#fee2e2'}; padding:5px; border-radius:5px; text-align:center;">
                            <b>F1 過濾：{'✅ PASS' if res['f1'] else '❌ WAIT'}</b>
                        </p>
                        <hr>
                        <table style="width:100%; font-size:0.85rem;">
                            <tr><td>A1 趨勢(20%)</td><td align="right"><b>{res['a1']}分</b> ({res['a1s']})</td></tr>
                            <tr><td>A2 構造(40%)</td><td align="right"><b>{res['a2']}分</b> ({res['a2s']})</td></tr>
                            <tr><td>A3 能量(40%)</td><td align="right"><b>{res['a3']}分</b> ({res['a3s']})</td></tr>
                        </table>
                        <hr>
                        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:5px;">
                            <div class="metric-box"><span class="metric-label">壓縮</span><br><span class="metric-value">{res['cp']}%</span></div>
                            <div class="metric-box"><span class="metric-label">RS</span><br><span class="metric-value">{res['rs']}%</span></div>
                            <div class="metric-box"><span class="metric-label">量比</span><br><span class="metric-value">{res['vol']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_code=True)
                else:
                    st.warning(f"{ticker} 抓取超時...")
