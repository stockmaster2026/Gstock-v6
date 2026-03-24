
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- [檢查 1：系統配置與標的完整性] ---
st.set_page_config(
    page_title="Apex Ambush V32.5",
    page_icon="🛰️",
    layout="wide"
)

# 妳指定的 11 支核心監控標的
WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- [檢查 2：原生指標算法 - 確保不依賴外部套件，避免崩潰] ---
def calculate_indicators(df):
    try:
        if df is None or df.empty: return None
        df = df.copy()
        
        # 數據預處理：處理 yfinance 可能產生的 Multi-index 或非浮點數
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        # 1. 計算 SMA 均線 (10, 20, 50)
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        
        # 2. 計算 MACD (使用原生 EMA 指數移動平均)
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].rolling(window=9).mean()
        
        return df
    except Exception as e:
        return None

# --- [檢查 3：核心戰略邏輯 - V26.5 權重與過濾器整合] ---
def calculate_apex_score(ticker, df, spy_df):
    try:
        if df is None or len(df) < 50: return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- A1: 趨勢維度 (權重 20%) ---
        # 邏輯：MACD 雙線在零軸之上給滿分；若在之下但斜率向上給 6 分
        a1_score = 0
        if latest['MACD'] > 0:
            a1_score = 10
        elif latest['MACD'] > prev['MACD']:
            a1_score = 6
        
        # --- A2: 構造維度 (權重 40%) ---
        # 邏輯：均線壓縮度 (MA10/20/50 的離散程度)
        ma_list = [float(latest['MA10']), float(latest['MA20']), float(latest['MA50'])]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        
        a2_score = 0
        if compression < 1.5: a2_score = 10      # 極度壓縮 (妳的靈魂埋伏點)
        elif compression < 3.0: a2_score = 8     # 標準壓縮
        elif compression < 5.0: a2_score = 4
        
        # --- A3: 能量維度 (權重 40%) ---
        # 包含：1. 成交量活性 (20%) 2. RS 相對強度 (20%)
        
        # 1. 成交量活性判定
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        vol_score = 5 if vol_ratio > 1.3 else (4 if vol_ratio < 0.5 else 0)
        
        # 2. RS 相對強度判定 (對比大盤 SPY)
        stock_ret = (latest['Close'] / df.iloc[-20]['Close']) - 1
        spy_ret = (spy_df.iloc[-1]['Close'] / spy_df.iloc[-20]['Close']) - 1
        rs_strength = stock_ret - spy_ret
        rs_score = 5 if rs_strength > 0.02 else (3 if rs_strength > 0 else 0)
        
        a3_score_total = vol_score + rs_score
        
        # --- 最終評分與 AWI 天氣系統轉換 ---
        total_points = (a1_score * 0.2) + (a2_score * 0.4) + (a3_score_total * 0.4 * (10/10)) 
        # 註：a3 部分標準化為 10 分制進行權重計算
        final_score = round((a1_score * 0.2) + (a2_score * 0.4) + (a3_score_total * 4), 1)
        # 簡化邏輯：直接加權
        final_score = round((a1_score * 0.2) + (a2_score * 0.4) + (a3_score_total * 0.4), 1) # 修正為總分 10
        
        # AWI 圖標判定
        if final_score >= 9.0: weather, icon = "噴發態", "🎆"
        elif final_score >= 7.0: weather, icon = "強勢態", "☀️"
        elif final_score >= 5.0: weather, icon = "整理態", "☁️"
        else: weather, icon = "危險態", "🌫️"
        
        # --- F1 戰略過濾器 (動態乖離邊界修正) ---
        # 如果能量 (A3) 強，放寬邊界到 5.0%，否則嚴格執行 1.5%
        buffer_limit = 0.05 if a3_score_total >= 8 else 0.015
        dist_to_ma20 = abs(latest['Close'] - latest['MA20']) / latest['MA20']
        f1_pass = dist_to_ma20 <= buffer_limit
        
        return {
            "代碼": ticker,
            "AWI 指標": f"{icon} {weather}",
            "Apex 總分": final_score,
            "F1 過濾": "✅ PASS" if f1_pass else "❌ WAIT",
            "均線壓縮": f"{round(float(compression), 2)}%",
            "RS 強度": f"{round(float(rs_strength)*100, 2)}%",
            "成交量比": round(float(vol_ratio), 2),
            "現價": round(float(latest['Close']), 2)
        }
    except:
        return None

# --- [檢查 4：主程式流程 - 強化穩定性與顯示] ---
st.title("🛰️ V32.5 Apex Ambush 巔峰埋伏系統")
st.markdown(f"**實時掃描時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. 抓取大盤基準
spy_data = yf.download("SPY", period="4mo", auto_adjust=True, progress=False)
spy_df = calculate_indicators(spy_data)

if spy_df is not None and not spy_df.empty:
    results_list = []
    progress_bar = st.progress(0)
    
    # 2. 逐一分析標的
    for i, ticker in enumerate(WATCH_LIST):
        try:
            stock_raw = yf.download(ticker, period="4mo", auto_adjust=True, progress=False)
            if not stock_raw.empty:
                stock_df = calculate_indicators(stock_raw)
                score_data = calculate_apex_score(ticker, stock_df, spy_df)
                if score_data:
                    results_list.append(score_data)
        except:
            continue
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    
    progress_bar.empty()

    # 3. 渲染戰略看板
    if results_list:
        final_df = pd.DataFrame(results_list)
        
        # 視覺化顏色定義
        def style_awi(val):
            if '🎆' in str(val): return 'background-color: #ff4b4b; color: white'
            if '☀️' in str(val): return 'background-color: #ffa500; color: black'
            return ''

        st.subheader("📊 全域戰略監控看板")
        st.dataframe(
            final_df.style.applymap(style_awi, subset=['AWI 指標']),
            use_container_width=True
        )
    else:
        st.error("分析完成，但未獲得有效數據。請檢查網路或標的代碼。")

    # --- [檢查 5：側邊欄實戰診斷] ---
    st.sidebar.header("🎯 核心持倉診斷")
    pl_data = next((item for item in results_list if item["代碼"] == "PL"), None)
    if pl_data:
        st.sidebar.markdown(f"### **PL 持倉分析**")
        if "☀️" in pl_data["AWI 指標"]:
            st.sidebar.success(f"目前 AWI: ☀️\n診斷：量縮洗盤，RS 強度維持。建議守住 $31.00，耐心持有。")
        else:
            st.sidebar.warning(f"PL 目前狀態：{pl_data['AWI 指標']}，請注意回檔幅度。")
else:
    st.error("無法連線至數據源 (Yahoo Finance)，請稍後再試。")
