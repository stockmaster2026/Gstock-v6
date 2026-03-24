
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面配置與舊版 CSS 樣式 ---
st.set_page_config(page_title="Apex Ambush V32.5", page_icon="🛰️", layout="wide")

st.markdown("""
    <style>
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        height: 100%;
    }
    .metric-label { font-size: 0.85rem; color: #666; }
    .metric-value { font-size: 1.1rem; font-weight: bold; color: #1f2937; }
    .awi-tag { font-size: 1.5rem; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_code=True)

# --- 2. 左側 Sidebar Input 欄位 (完整保留舊版功能) ---
st.sidebar.header("⚙️ 系統參數設定")
manual_tickers = st.sidebar.text_input(
    "監控標的 (請用逗號隔開)", 
    "AAOI, PL, LUNR, TSLA, NVDA, TSEM, CRDO, MSFT, GOOGL, META, AAPL"
)
WATCH_LIST = [t.strip().upper() for t in manual_tickers.split(",")]

ma_short = st.sidebar.number_input("A2 構造-短均線 (10MA)", value=10)
ma_mid = st.sidebar.number_input("F1 命脈-中均線 (20MA)", value=20)
ma_long = st.sidebar.number_input("趨勢定錨-長均線 (50MA)", value=50)

st.sidebar.markdown("---")
st.sidebar.write("📌 **V26.5 評分權重**")
st.sidebar.info("""
- **A1 趨勢 (MACD):** 20%
- **A2 構造 (均線糾結):** 40%
- **A3 能量 (RS+成交量):** 40%
""")

# --- 3. 原生技術指標計算 (穩定版) ---
def calculate_indicators(df):
    try:
        if df is None or df.empty: return None
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        # 均線計算
        df['MA10'] = df['Close'].rolling(window=ma_short).mean()
        df['MA20'] = df['Close'].rolling(window=ma_mid).mean()
        df['MA50'] = df['Close'].rolling(window=ma_long).mean()
        
        # MACD 原生計算
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        return df
    except: return None

# --- 4. 核心評分引擎：V26.5 三維度邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    try:
        if df is None or len(df) < 50: return None
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # [A1: 空間/趨勢 20%]
        a1_val = 10 if latest['MACD'] > 0 else (6 if latest['MACD'] > prev['MACD'] else 0)
        a1_final = a1_val * 0.2
        
        # [A2: 構造/糾結 40%]
        ma_list = [float(latest['MA10']), float(latest['MA20']), float(latest['MA50'])]
        comp = (np.std(ma_list) / np.mean(ma_list)) * 100
        a2_val = 10 if comp < 1.5 else (8 if comp < 3.0 else 4)
        a2_final = a2_val * 0.4
        
        # [A3: 能量/推力 40%] (量比 5分 + RS 5分)
        vol_ratio = latest['Volume'] / df['Volume'].tail(10).mean()
        vol_score = 5 if vol_ratio > 1.3 or vol_ratio < 0.5 else 0
        
        rs = ((latest['Close']/df.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close']))
        rs_score = 5 if rs > 0.02 else (3 if rs > 0 else 0)
        a3_val = vol_score + rs_score
        a3_final = a3_val * 0.4
        
        total_score = round(a1_final + a2_final + a3_final, 1)
        
        # AWI 天氣轉換
        if total_score >= 9: awi, icon = "噴發態", "🎆"
        elif total_score >= 7: awi, icon = "強勢態", "☀️"
        elif total_score >= 5: awi, icon = "整理態", "☁️"
        else: awi, icon = "危險態", "🌫️"
        
        # F1 過濾
        dist_ma20 = abs(latest['Close'] - latest['MA20']) / latest['MA20']
        buffer = 0.05 if a3_val >= 8 else 0.015
        f1_pass = dist_ma20 <= buffer
        
        return {
            "ticker": ticker, "icon": icon, "awi": awi, "total": total_score,
            "a1": a1_val, "a1_w": round(a1_final, 1),
            "a2": a2_val, "a2_w": round(a2_final, 1),
            "a3": a3_val, "a3_w": round(a3_final, 1),
            "f1": f1_pass, "price": round(latest['Close'], 2),
            "comp": round(comp, 2), "rs": round(rs*100, 2), "vol": round(vol_ratio, 2)
        }
    except: return None

# --- 5. 畫面渲染：還原 11 個獨立板塊佈局 ---
st.title("🛰️ V32.5 Apex Ambush 巔峰埋伏監控看板")
st.markdown(f"**最後更新：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

spy_raw = yf.download("SPY", period="4mo", auto_adjust=True, progress=False)
spy_df = calculate_indicators(spy_raw)

if spy_df is not None:
    # 這裡維持妳喜歡的網格佈局，每排 3 個板塊
    rows = [WATCH_LIST[i:i + 3] for i in range(0, len(WATCH_LIST), 3)]
    
    for row in rows:
        cols = st.columns(3)
        for i, ticker in enumerate(row):
            with cols[i]:
                stock_raw = yf.download(ticker, period="4mo", auto_adjust=True, progress=False)
                df = calculate_indicators(stock_raw)
                res = calculate_apex_score(ticker, df, spy_df)
                
                if res:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div class="awi-tag">{res['icon']} {res['awi']}</div>
                        <h2 style="margin:0;">{res['ticker']} <span style="font-size:1.2rem; color:#888;">${res['price']}</span></h2>
                        <h1 style="color:#ff4b4b; margin:10px 0;">{res['total']} <small style="font-size:1rem;">總分</small></h1>
                        <p style="background-color:{'#d1fae5' if res['f1'] else '#fee2e2'}; padding:5px; border-radius:5px; text-align:center;">
                            <b>F1 過濾：{'✅ PASS' if res['f1'] else '❌ WAIT'}</b>
                        </p>
                        <hr>
                        <table style="width:100%; font-size:0.9rem;">
                            <tr><td>A1 趨勢(20%)</td><td align="right"><b>{res['a1']}分</b> ({res['a1_w']})</td></tr>
                            <tr><td>A2 構造(40%)</td><td align="right"><b>{res['a2']}分</b> ({res['a2_w']})</td></tr>
                            <tr><td>A3 能量(40%)</td><td align="right"><b>{res['a3']}分</b> ({res['a3_w']})</td></tr>
                        </table>
                        <hr>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                            <div><span class="metric-label">均線壓縮</span><br><span class="metric-value">{res['comp']}%</span></div>
                            <div><span class="metric-label">RS 強度</span><br><span class="metric-value">{res['rs']}%</span></div>
                            <div><span class="metric-label">成交量比</span><br><span class="metric-value">{res['vol']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_code=True)
                else:
                    st.error(f"{ticker} 抓取中...")
