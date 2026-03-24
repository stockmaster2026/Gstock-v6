
import os
import subprocess
import sys

# --- 核心：強效安裝補丁 (解決所有安裝報錯) ---
def try_install(package_name):
    try:
        if package_name == "pandas-ta":
            import pandas_ta
        elif package_name == "yfinance":
            import yfinance
    except ImportError:
        # 使用最底層指令強制安裝，繞過所有版本檢查
        subprocess.call([sys.executable, "-m", "pip", "install", package_name, "--no-cache-dir"])

try_install("yfinance")
try_install("pandas-ta")

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Apex Ambush V32.5", layout="wide")

WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- 2. 核心評分引擎：V26.5 巔峰埋伏邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    try:
        if len(df) < 50: return None
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # A1: 趨勢 (20%)
        a1_score = 0
        macd_cols = [c for c in df.columns if 'MACD' in c and 'h' not in c and 's' not in c]
        if macd_cols:
            if latest[macd_cols[0]] > 0: a1_score = 10
            elif latest[macd_cols[0]] > prev[macd_cols[0]]: a1_score = 6
        
        # A2: 構造 (40%) - 均線壓縮
        ma_list = [latest['MA10'], latest['MA20'], latest['MA50']]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        a2_score = 10 if compression < 1.5 else (8 if compression < 3.0 else 4)
        
        # A3: 能量 (40%) - 成交量 & RS 推力
        a3_score = 0
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        if vol_ratio > 1.3: a3_score += 5
        elif vol_ratio < 0.5: a3_score += 4
        
        stock_ret = (latest['Close'] / df.iloc[-20]['Close']) - 1
        spy_ret = (spy_df.iloc[-1]['Close'] / spy_df.iloc[-20]['Close']) - 1
        rs_strength = stock_ret - spy_ret
        if rs_strength > 0.02: a3_score += 5
        elif rs_strength > 0: a3_score += 3
        
        total = (a1_score * 0.2) + (a2_score * 0.4) + (a3_score * 0.4)
        if total >= 9.0: weather, icon = "噴發態", "🎆"
        elif total >= 7.0: weather, icon = "強勢態", "☀️"
        elif total >= 5.0: weather, icon = "整理態", "☁️"
        else: weather, icon = "危險態", "🌫️"
        
        buffer_limit = 0.05 if a3_score >= 8 else 0.015
        dist_to_ma20 = abs(latest['Close'] - latest['MA20']) / latest['MA20']
        f1_pass = dist_to_ma20 <= buffer_limit
        
        return {
            "代碼": ticker, "AWI 指標": f"{icon} {weather}", "Apex 總分": round(total, 1),
            "F1 過濾": "✅ PASS" if f1_pass else "❌ WAIT", "均線壓縮度": f"{round(compression, 2)}%",
            "相對強度(RS)": f"{round(rs_strength*100, 2)}%", "成交量比": round(vol_ratio, 2),
            "現價": round(float(latest['Close']), 2)
        }
    except: return None

# --- 3. 數據抓取 ---
def get_data(ticker):
    try:
        df = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if df.empty: return None
        df['MA10'] = ta.sma(df['Close'], length=10)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        return df
    except: return None

# --- 4. 渲染介面 ---
st.title("🛰️ V32.5 Apex Ambush 巔峰埋伏系統")
spy_df = get_data("SPY")
if spy_df is not None:
    all_results = []
    progress_bar = st.progress(0)
    for i, t in enumerate(WATCH_LIST):
        stock_df = get_data(t)
        if stock_df is not None:
            res = calculate_apex_score(t, stock_df, spy_df)
            if res: all_results.append(res)
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    progress_bar.empty()
    if all_results:
        st.dataframe(pd.DataFrame(all_results), use_container_width=True)

    st.sidebar.header("🎯 持倉建議")
    pl_data = next((item for item in all_results if item["代碼"] == "PL"), None)
    if pl_data:
        st.sidebar.success(f"PL 目前為 {pl_data['AWI 指標']}。守住 $31.00。")
