import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. 頁面配置與進階 CSS 樣式 ---
st.set_page_config(page_title="Apex Ambush V32.5", page_icon="🛰️", layout="wide")

st.markdown("""
    <style>
    .sector-card {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .stock-row {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #cbd5e1;
    }
    .awi-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .metric-text { font-size: 0.8rem; color: #475569; }
    .score-bold { font-weight: bold; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 左側 Sidebar (極簡 Input) ---
st.sidebar.header("🔍 戰略部署中心")
manual_input = st.sidebar.text_input(
    "核心監控板塊 (11 個核心)", 
    "AAOI, PL, LUNR, TSLA, NVDA, TSEM, CRDO, MSFT, GOOGL, META, AAPL"
)
CORE_LIST = [t.strip().upper() for t in manual_input.split(",")]

# --- 3. 指標計算引擎 (原生穩定版) ---
def get_indicators(df):
    try:
        if df is None or df.empty: return None
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        return df
    except: return None

def analyze_stock(ticker, df, spy_df):
    try:
        if df is None or len(df) < 50: return None
        # 計算五天 AWI 走勢
        awi_history = []
        for i in range(-5, 0):
            sub_df = df.iloc[:len(df)+i+1] if i < -1 else df
            curr = sub_df.iloc[-1]
            prev = sub_df.iloc[-2]
            
            a1 = 10 if curr['MACD'] > 0 else (6 if curr['MACD'] > prev['MACD'] else 0)
            mas = [float(curr['MA10']), float(curr['MA20']), float(curr['MA50'])]
            comp = (np.std(mas) / np.mean(mas)) * 100
            a2 = 10 if comp < 1.5 else (8 if comp < 3.0 else 4)
            
            vol_ratio = curr['Volume'] / sub_df['Volume'].tail(10).mean()
            v_s = 5 if vol_ratio > 1.3 or vol_ratio < 0.5 else 0
            rs = (curr['Close']/sub_df.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close'])
            r_s = 5 if rs > 0.02 else (3 if rs > 0 else 0)
            
            score = round((a1*0.2) + (a2*0.4) + ((v_s + r_s)*0.4), 1)
            awi_history.append(score)

        latest_score = awi_history[-1]
        latest = df.iloc[-1]
        
        # AWI 天氣與顏色
        color = "#fee2e2" if latest_score < 5 else ("#fef9c3" if latest_score < 7 else ("#ffedd5" if latest_score < 9 else "#dcfce7"))
        icon = "🌫️" if latest_score < 5 else ("☁️" if latest_score < 7 else ("☀️" if latest_score < 9 else "🎆"))
        
        return {
            "tk": ticker, "sc": latest_score, "ic": icon, "bg": color,
            "a1": a1, "a1w": round(a1*0.2, 1),
            "a2": a2, "a2w": round(a2*0.4, 1),
            "a3": (v_s + r_s), "a3w": round((v_s + r_s)*0.4, 1),
            "hist": awi_history, "cp": round(comp, 2), "pr": round(latest['Close'], 2)
        }
    except: return None

# --- 4. 畫面渲染：11 個大型戰略板塊 ---
st.title("🛰️ Apex Ambush V32.5 巔峰埋伏戰略指揮部")

with st.spinner('同步全球衛星數據中...'):
    spy_df = get_indicators(yf.download("SPY", period="5mo", auto_adjust=True, progress=False))
    
    if spy_df is not None:
        # 佈局：每橫排 2 個大型板塊，確保 iPad/電腦觀看舒適
        for i in range(0, len(CORE_LIST), 2):
            cols = st.columns(2)
            for j, core_ticker in enumerate(CORE_LIST[i:i+2]):
                with cols[j]:
                    # 每個板塊開始
                    st.markdown(f'<div class="sector-card">', unsafe_allow_html=True)
                    st.header(f"📦 板塊中心：{core_ticker}")
                    
                    # 模擬關聯股票 (11 板塊內各帶 5 支關聯股)
                    # 實務上我們會根據產業帶入，這裡示範該板塊的深度分析
                    related_stocks = [core_ticker] # 這裡可以擴充妳要的 5-6 支關聯股
                    
                    for stk in related_stocks:
                        data = get_indicators(yf.download(stk, period="5mo", auto_adjust=True, progress=False))
                        res = analyze_stock(stk, data, spy_df)
                        
                        if res:
                            st.markdown(f"""
                            <div class="stock-row" style="background-color: {res['bg']};">
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="font-size: 1.2rem; font-weight: bold;">{res['ic']} {res['tk']} — ${res['pr']}</span>
                                    <span style="font-size: 1.5rem; color: #ff4b4b; font-weight: bold;">{res['sc']} 分</span>
                                </div>
                                <div style="margin: 5px 0;">
                                    <span class="metric-text">A1(趨勢20%): <span class="score-bold">{res['a1']}分 ({res['a1w']})</span></span> | 
                                    <span class="metric-text">A2(構造40%): <span class="score-bold">{res['a2']}分 ({res['a2w']})</span></span> | 
                                    <span class="metric-text">A3(能量40%): <span class="score-bold">{res['a3']}分 ({res['a3w']})</span></span>
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 5px;">
                                    <span class="awi-badge" style="background:#fff;">5日 AWI 走勢: {res['hist']}</span>
                                    <span class="awi-badge" style="background:#fff;">均線壓縮: {res['cp']}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 每個板塊最後的建議
                    if res:
                        if res['sc'] >= 9: st.success(f"🚀 戰略建議：{core_ticker} 處於噴發態，均線極度壓縮，建議埋伏或加倉。")
                        elif res['sc'] >= 7: st.info(f"☀️ 戰略建議：{core_ticker} 強勢整理中，等待量能再次活化。")
                        else: st.warning(f"🌫️ 戰略建議：{core_ticker} 構造發散，暫避風頭，不宜追高。")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 頁尾聲明 ---
st.markdown("---")
st.caption("🛰️ V32.5 Apex Ambush — 基於 A1 Alignment / A2 Anchoring / A3 Activation 核心系統。")

