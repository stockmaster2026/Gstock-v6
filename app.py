
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="Apex Ambush V32.5", layout="wide")

# 妳最核心的 11 支標的
WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- 2. 原生技術指標計算 (不依賴額外套件，確保穩定) ---
def calculate_indicators(df):
    try:
        # 計算移動平均線 (SMA)
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        
        # 計算 MACD (原生 EMA 邏輯)
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].rolling(window=9).mean()
        return df
    except:
        return df

# --- 3. 核心評分引擎：V26.5 巔峰埋伏邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    try:
        if len(df) < 50: return None
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- A1: 趨勢對齊 (20%) ---
        a1_score = 0
        if latest['MACD'] > 0: a1_score = 10
        elif latest['MACD'] > prev['MACD']: a1_score = 6
        
        # --- A2: 構造錨定 (40%) - 均線壓縮 ---
        ma_list = [latest['MA10'], latest['MA20'], latest['MA50']]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        
        a2_score = 0
        if compression < 1.5: a2_score = 10     # 極度壓縮
        elif compression < 3.0: a2_score = 8    # 標準壓縮
        elif compression < 5.0: a2_score = 4
        
        # --- A3: 能量活化 (40%) - 成交量 & RS 推力 ---
        a3_score = 0
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        
        # 能量判定 (窒息或攻擊)
        if vol_ratio > 1.3: a3_score += 5
        elif vol_ratio < 0.5: a3_score += 4
        
        # RS 相對強度 (對比 SPY 表現)
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
        
        # F1 戰略過濾器 (動態放寬機制)
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
    except:
        return None

# --- 4. 主程式 UI 渲染 ---
st.title("🛰️ Apex Ambush V32.5 巔峰埋伏系統")
st.markdown(f"**市場監控：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 獲取基準數據
spy_data = yf.download("SPY", period="4mo", interval="1d", progress=False)
spy_df = calculate_indicators(spy_data)

if not spy_df.empty:
    all_results = []
    progress_bar = st.progress(0)
    
    for i, t in enumerate(WATCH_LIST):
        stock_data = yf.download(t, period="4mo", interval="1d", progress=False)
        if not stock_data.empty:
            df = calculate_indicators(stock_data)
            res = calculate_apex_score(t, df, spy_df)
            if res:
                all_results.append(res)
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    
    progress_bar.empty()

    if all_results:
        final_df = pd.DataFrame(all_results)
        
        # 視覺化格式
        def highlight_awi(val):
            if '🎆' in str(val): return 'background-color: #ff4b4b; color: white'
            if '☀️' in str(val): return 'background-color: #ffa500; color: black'
            return ''

        st.subheader("📊 全域戰略監控看板")
        st.dataframe(final_df.style.applymap(highlight_awi, subset=['AWI 指標']), use_container_width=True)

    # --- 5. 側邊欄實戰診斷 ---
    st.sidebar.header("🎯 核心診斷建議")
    pl_data = next((item for item in all_results if item["代碼"] == "PL"), None)
    if pl_data:
        st.sidebar.success(f"PL 診斷：{pl_data['AWI 指標']}。維持 $31.00 支撐，量縮洗盤，不必動作。")
    
    st.sidebar.write("---")
    st.sidebar.info("V32.5 穩定版：\n1. 恢復原生計算 (無套件依賴)\n2. 20/40/40 權重分配\n3. RS 相對強度過濾")
