
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. 頁面配置與進階視覺樣式 ---
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
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 6px solid #cbd5e1;
    }
    .awi-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        background-color: rgba(255,255,255,0.7);
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 左側 Sidebar (徹底真空 Input) ---
st.sidebar.header("🔍 戰略部署中心")
# 依妳要求：預設完全空白
manual_input = st.sidebar.text_input("輸入監控代號 (用逗號隔開)", value="")
WATCH_LIST = [t.strip().upper() for t in manual_input.split(",")] if manual_input else []

# --- 3. 穩定指標計算引擎 ---
def get_indicators(df):
    try:
        if df is None or df.empty: return None
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 10/20/50MA 原生計算
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        
        # MACD 原生計算
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        return df
    except: return None

# --- 4. 核心評分引擎：V26.5 深度分析 (含 5 天 AWI) ---
def analyze_stock(ticker, df, spy_df):
    try:
        if df is None or len(df) < 50: return None
        hist_scores = []
        # 回溯最近 5 個交易日
        for i in range(-4, 1):
            sub_df = df.iloc[:len(df)+i] if i < 0 else df
            curr = sub_df.iloc[-1]
            prev = sub_df.iloc[-2]
            
            # A1 趨勢 (20%)
            a1 = 10 if curr['MACD'] > 0 else (6 if curr['MACD'] > prev['MACD'] else 0)
            a1w = round(a1 * 0.2, 1)
            # A2 構造 (40%)
            mas = [float(curr['MA10']), float(curr['MA20']), float(curr['MA50'])]
            comp = (np.std(mas) / np.mean(mas)) * 100
            a2 = 10 if comp < 1.5 else (8 if comp < 3.0 else 4)
            a2w = round(a2 * 0.4, 1)
            # A3 能量 (40%)
            vol_ratio = curr['Volume'] / sub_df['Volume'].tail(10).mean()
            v_s = 5 if vol_ratio > 1.3 or vol_ratio < 0.5 else 0
            rs = (curr['Close']/sub_df.iloc[-20]['Close']) - (spy_df.iloc[-1]['Close']/spy_df.iloc[-20]['Close'])
            r_s = 5 if rs > 0.02 else (3 if rs > 0 else 0)
            a3 = v_s + r_s
            a3w = round(a3 * 0.4, 1)
            
            total = round(a1w + a2w + a3w, 1)
            hist_scores.append(total)

        latest = df.iloc[-1]
        score = hist_scores[-1]
        bg = "#dcfce7" if score >= 9 else ("#fff7ed" if score >= 7 else ("#f1f5f9" if score >= 5 else "#fee2e2"))
        icon = "🎆" if score >= 9 else ("☀️" if score >= 7 else ("☁️" if score >= 5 else "🌫️"))
        
        return {
            "tk": ticker, "sc": score, "ic": icon, "bg": bg,
            "a1": a1, "a1w": a1w, "a2": a2, "a2w": a2w, "a3": a3, "a3w": a3w,
            "hist": hist_scores, "cp": round(comp, 2), "pr": round(float(latest['Close']), 2)
        }
    except: return None

# --- 5. 畫面渲染 ---
st.title("🛰️ Apex Ambush V32.5 指揮部")

if not WATCH_LIST:
    st.info("👈 請在左側輸入框輸入股票代碼（例如: PL, LUNR）以啟動 11 板塊監控。")
else:
    # 增加快速抓取邏輯，防止超時
    with st.spinner('同步數據中...'):
        spy_raw = yf.download("SPY", period="6mo", auto_adjust=True, progress=False, threads=False)
        spy_df = get_indicators(spy_raw)
        
        if spy_df is not None:
            # 每排 2 個大型板塊
            for i in range(0, len(WATCH_LIST), 2):
                cols = st.columns(2)
                for j, ticker in enumerate(WATCH_LIST[i:i+2]):
                    with cols[j]:
                        st.markdown('<div class="sector-card">', unsafe_allow_html=True)
                        st.subheader(f"📦 板塊中心：{ticker}")
                        
                        # 加入延遲防止 Yahoo 封鎖
                        time.sleep(1) 
                        raw_data = yf.download(ticker, period="6mo", auto_adjust=True, progress=False, threads=False)
                        res = analyze_stock(ticker, get_indicators(raw_data), spy_df)
                        
                        if res:
                            st.markdown(f"""
                            <div class="stock-row" style="background-color: {res['bg']};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 1.3rem; font-weight: bold;">{res['ic']} {res['tk']} — ${res['pr']}</span>
                                    <span style="font-size: 1.8rem; color: #ff4b4b; font-weight: bold;">{res['sc']} <small style="font-size:0.8rem">分</small></span>
                                </div>
                                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #cbd5e1;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                                    <div><small>A1 趨勢(20%)</small><br><b>{res['a1']}分</b> ({res['a1w']})</div>
                                    <div><small>A2 構造(40%)</small><br><b>{res['a2']}分</b> ({res['a2w']})</div>
                                    <div><small>A3 能量(40%)</small><br><b>{res['a3']}分</b> ({res['a3w']})</div>
                                </div>
                                <div style="display: flex; gap: 15px; margin-top: 12px;">
                                    <span class="awi-badge">5日 AWI 歷史: {res['hist']}</span>
                                    <span class="awi-badge">均線壓縮: {res['cp']}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"{ticker} 數據連線超時，請點擊右下角 Reboot 或稍後再試。")
                        st.markdown('</div>', unsafe_allow_html=True)
