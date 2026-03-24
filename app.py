
import os
import subprocess
import sys

# --- 自動安裝補丁：解決 Streamlit 環境衝突 ---
def install_requirements():
    try:
        import pandas_ta as ta
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas-ta"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])

install_requirements()

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime

# --- 1. 系統核心設定 ---
st.set_page_config(page_title="Apex Ambush V32.5", layout="wide")

# 妳的核心 11 支標的清單
WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- 2. 核心評分引擎：V26.5 巔峰埋伏邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    """
    進化點：
    A1: 趨勢(20%) | A2: 構造(40%) | A3: 能量(40%)
    特別針對 AAOI (噴發) 與 LUNR (陷阱) 進行邏輯修正
    """
    try:
        if len(df) < 50: return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # A_1: 趨勢對齊 (20%) - MACD 方向
        a1_score = 0
        macd_cols = [c for c in df.columns if 'MACD' in c and 'h' not in c and 's' not in c]
        if macd_cols:
            macd_val = latest[macd_cols[0]]
            prev_macd = prev[macd_cols[0]]
            if macd_val > 0: a1_score = 10
            elif macd_val > prev_macd: a1_score = 6
        
        # A_2: 構造錨定 (40%) - 均線壓縮 (系統的靈魂)
        ma_list = [latest['MA10'], latest['MA20'], latest['MA50']]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        
        a2_score = 0
        if compression < 1.5: a2_score = 10     # 極度壓縮
        elif compression < 3.0: a2_score = 8    # 標準壓縮
        elif compression < 5.0: a2_score = 4    
        
        # A_3: 能量活化 (40%) - 成交量 & RS 推力
        a3_score = 0
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        
        # 能量判定
        if vol_ratio > 1.3: a3_score += 5       # 攻擊量
        elif vol_ratio < 0.5: a3_score += 4     # 窒息量 (洗盤)
        
        # RS 相對強度判定 (對比 SPY)
        stock_ret = (latest['Close'] / df.iloc[-20]['Close']) - 1
        spy_ret = (spy_df.iloc[-1]['Close'] / spy_df.iloc[-20]['Close']) - 1
        rs_strength = stock_ret - spy_ret
        
        if rs_strength > 0.02: a3_score += 5    # 強於大盤 2% 以上
        elif rs_strength > 0: a3_score += 3
        
        # 總分與 AWI 天氣轉換
        total = (a1_score * 0.2) + (a2_score * 0.4) + (a3_score * 0.4)
        
        if total >= 9.0: weather, icon = "噴發態", "🎆"
        elif total >= 7.0: weather, icon = "強勢態", "☀️"
        elif total >= 5.0: weather, icon = "整理態", "☁️"
        else: weather, icon = "危險態", "🌫️"
        
        # F1 戰略過濾器 (動態放寬 Buffer)
        buffer_limit = 0.05 if a3_score >= 8 else 0.015
        dist_to_ma20 = abs(latest['Close'] - latest['MA20']) / latest['MA20']
        f1_pass = dist_to_ma20 <= buffer_limit
        
        return {
            "代碼": ticker,
            "AWI 指標": f"{icon} {weather}",
            "Apex 總分": round(total, 1),
            "F1 過濾": "✅ PASS" if f1_pass else "❌ WAIT",
            "均線壓縮度": f"{round(compression, 2)}%",
            "相對強度(RS)": f"{round(rs_strength*100, 2)}%",
            "成交量比": round(vol_ratio, 2),
            "現價": round(float(latest['Close']), 2)
        }
    except Exception as e:
        return None

# --- 3. 數據抓取與處理 ---
def get_data(ticker):
    try:
        df = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if df.empty: return None
        
        # 計算技術指標
        df['MA10'] = ta.sma(df['Close'], length=10)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        return df
    except:
        return None

# --- 4. Streamlit 介面呈現 ---
st.title("🛰️ Apex Ambush V32.5 巔峰埋伏系統")
st.markdown(f"**市場監控時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

spy_df = get_data("SPY")

if spy_df is not None:
    all_results = []
    
    # 使用進度條
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, t in enumerate(WATCH_LIST):
        progress_text.text(f"正在分析：{t}...")
        stock_df = get_data(t)
        if stock_df is not None:
            res = calculate_apex_score(t, stock_df, spy_df)
            if res:
                all_results.append(res)
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    
    progress_text.empty()
    progress_bar.empty()

    # 顯示核心看板
    if all_results:
        final_df = pd.DataFrame(all_results)
        
        def highlight_awi(val):
            if '🎆' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
            if '☀️' in str(val): return 'background-color: #ffa500; color: black; font-weight: bold'
            if '🌫️' in str(val): return 'background-color: #d3d3d3; color: #777'
            return ''

        st.subheader("📊 全域戰略監控看板")
        st.dataframe(final_df.style.applymap(highlight_awi, subset=['AWI 指標']), use_container_width=True)

    # --- 5. 側邊欄：持倉實戰建議 ---
    st.sidebar.header("🎯 核心診斷建議")
    
    # 針對 PL 的特別追蹤
    pl_data = next((item for item in all_results if item["代碼"] == "PL"), None)
    if pl_data:
        st.sidebar.markdown("### **PL 持倉現況**")
        if "☀️" in pl_data["AWI 指標"]:
            st.sidebar.success(f"目前 AWI 為 ☀️ 強勢態。\n成交量比 {pl_data['成交量比']} 顯示為洗盤，並非大戶撤退。建議守住 $31.00。")
        else:
            st.sidebar.warning(f"PL 警報：目前 AWI 為 {pl_data['AWI 指標']}，請注意支撐。")

    st.sidebar.write("---")
    st.sidebar.info("V32.5 更新日誌：\n1. 能量權重 40%\n2. RS 相對強度過濾\n3. 動態 F1 乖離機制")

