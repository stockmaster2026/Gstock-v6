
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta

# --- 1. 頁面基本配置 ---
st.set_page_config(
    page_title="Apex Ambush V32.5",
    page_icon="🛰️",
    layout="wide"
)

# 妳的核心 11 支標的清單
WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- 2. 核心評分引擎：V26.5 巔峰埋伏邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    """
    A1: 趨勢對齊 (20%) - MACD 方向
    A2: 構造錨定 (40%) - 均線壓縮 (系統靈魂)
    A3: 能量活化 (40%) - 成交量比 + RS 相對強度
    """
    try:
        if len(df) < 50: return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- A1: 趨勢維度 (20%) ---
        a1_score = 0
        macd_cols = [c for c in df.columns if 'MACD' in c and 'h' not in c and 's' not in c]
        if macd_cols:
            macd_val = latest[macd_cols[0]]
            prev_macd = prev[macd_cols[0]]
            if macd_val > 0: a1_score = 10
            elif macd_val > prev_macd: a1_score = 6
        
        # --- A2: 構造維度 (40%) ---
        ma_list = [latest['MA10'], latest['MA20'], latest['MA50']]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        
        if compression < 1.5: a2_score = 10     # 極度壓縮 (埋伏點)
        elif compression < 3.0: a2_score = 8    # 標準壓縮
        elif compression < 5.0: a2_score = 4    # 稍嫌鬆散
        else: a2_score = 0
        
        # --- A3: 能量維度 (40%) ---
        a3_score = 0
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        
        # 能量判定 (窒息或攻擊)
        if vol_ratio > 1.3: a3_score += 5       # 攻擊量
        elif vol_ratio < 0.5: a3_score += 4     # 窒息量 (洗盤)
        
        # RS 相對強度 (對比大盤 SPY)
        stock_ret = (latest['Close'] / df.iloc[-20]['Close']) - 1
        spy_ret = (spy_df.iloc[-1]['Close'] / spy_df.iloc[-20]['Close']) - 1
        rs_strength = stock_ret - spy_ret
        
        if rs_strength > 0.02: a3_score += 5    # 強於大盤 2% 以上 (領先指標)
        elif rs_strength > 0: a3_score += 3
        
        # --- 總分計算與 AWI 天氣轉換 ---
        total_score = (a1_score * 0.2) + (a2_score * 0.4) + (a3_score * 0.4)
        
        if total_score >= 9.0: weather, icon = "噴發態", "🎆"
        elif total_score >= 7.0: weather, icon = "強勢態", "☀️"
        elif total_score >= 5.0: weather, icon = "整理態", "☁️"
        else: weather, icon = "危險態", "🌫️"
        
        # --- F1 戰略過濾器 (動態邊界) ---
        # 如果 A3 能量夠強，放寬 MA20 乖離率至 5% (確保買到 AAOI 第一根)
        buffer_limit = 0.05 if a3_score >= 8 else 0.015
        dist_to_ma20 = abs(latest['Close'] - latest['MA20']) / latest['MA20']
        f1_pass = dist_to_ma20 <= buffer_limit
        
        return {
            "代碼": ticker,
            "AWI 指標": f"{icon} {weather}",
            "Apex 總分": round(total_score, 1),
            "F1 過濾": "✅ PASS" if f1_pass else "❌ WAIT",
            "均線壓縮度": f"{round(compression, 2)}%",
            "相對強度(RS)": f"{round(rs_strength*100, 2)}%",
            "成交量比": round(vol_ratio, 2),
            "現價": round(float(latest['Close']), 2)
        }
    except Exception as e:
        st.error(f"分析 {ticker} 時出錯: {e}")
        return None

# --- 3. 數據抓取函式 ---
def get_data(ticker):
    try:
        df = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if df.empty: return None
        
        # 使用 pandas_ta 計算技術指標
        df['MA10'] = ta.sma(df['Close'], length=10)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        return df
    except Exception as e:
        return None

# --- 4. 主程式 UI 渲染 ---
st.title("🛰️ V32.5 Apex Ambush 巔峰埋伏系統")
st.markdown(f"**最後掃描時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (美股實時監控)")

# 獲取基準數據
spy_df = get_data("SPY")

if spy_df is not None:
    all_results = []
    
    # 建立橫向進度條
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, t in enumerate(WATCH_LIST):
        progress_text.text(f"正在掃描：{t}...")
        stock_df = get_data(t)
        if stock_df is not None:
            res = calculate_apex_score(t, stock_df, spy_df)
            if res:
                all_results.append(res)
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    
    progress_text.empty()
    progress_bar.empty()

    # 顯示戰略看板
    if all_results:
        final_df = pd.DataFrame(all_results)
        
        # 視覺化格式設定
        def highlight_awi(val):
            if '🎆' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
            if '☀️' in str(val): return 'background-color: #ffa500; color: black; font-weight: bold'
            if '🌫️' in str(val): return 'background-color: #d3d3d3; color: #777'
            return ''

        st.subheader("📊 全域戰略監控看板")
        st.dataframe(
            final_df.style.applymap(highlight_awi, subset=['AWI 指標']),
            use_container_width=True,
            height=450
        )

    # --- 5. 側邊欄：核心持倉診斷建議 ---
    st.sidebar.header("🎯 核心診斷建議")
    
    # PL 特別追蹤
    pl_data = next((item for item in all_results if item["代碼"] == "PL"), None)
    if pl_data:
        st.sidebar.markdown(f"### **PL 持倉現況**")
        if "☀️" in pl_data["AWI 指標"]:
            st.sidebar.success(f"AWI: ☀️ 強勢態\n分數: {pl_data['Apex 總分']}\n\n診斷：目前縮量洗盤，RS 強度仍為正數，建議守住 $31.00，不需動作。")
        elif "🎆" in pl_data["AWI 指標"]:
            st.sidebar.error("AWI: 🎆 噴發態！請注意獲利了結點。")
        else:
            st.sidebar.warning(f"PL 目前處於 {pl_data['AWI 指標']}，注意均線支撐。")

    # LUNR 警示
    lunr_data = next((item for item in all_results if item["代碼"] == "LUNR"), None)
    if lunr_data and "🌫️" in lunr_data["AWI 指標"]:
        st.sidebar.markdown("---")
        st.sidebar.error(f"⚠️ LUNR 警報：分數僅 {lunr_data['Apex 總分']}，能量與 RS 雙崩潰，建議果斷撤資。")

st.sidebar.write("---")
st.sidebar.info("V32.5 更新說明：\n1. 能量權重 40%\n2. RS 相對強度過濾\n3. 動態 F1 Buffer (1.5% -> 5%)")
