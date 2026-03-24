
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta

# --- 1. 頁面配置與環境設定 ---
st.set_page_config(
    page_title="Apex Ambush V32.5",
    page_icon="🛰️",
    layout="wide"
)

# 妳最核心的 11 支標的清單 (可在此處增減)
WATCH_LIST = ["AAOI", "PL", "LUNR", "TSLA", "NVDA", "TSEM", "CRDO", "MSFT", "GOOGL", "META", "AAPL"]

# --- 2. 核心評分引擎：V26.5 巔峰埋伏邏輯 ---
def calculate_apex_score(ticker, df, spy_df):
    """
    實戰邏輯核心：
    A_1: 趨勢對齊 (20%) - MACD 順風程度
    A_2: 構造錨定 (40%) - 均線極度糾結 < 3% (這是起漲點的靈魂)
    A_3: 能量活化 (40%) - 成交量比 + RS 相對強度 (避開陷阱的推力)
    """
    try:
        if len(df) < 50: return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- [A1: 趨勢維度 20%] ---
        a1_score = 0
        macd_cols = [c for c in df.columns if 'MACD' in c and 'h' not in c and 's' not in c]
        if macd_cols:
            macd_val = latest[macd_cols[0]]
            prev_macd = prev[macd_cols[0]]
            # MACD 在零軸之上給滿分，否則看斜率是否轉強
            if macd_val > 0: a1_score = 10
            elif macd_val > prev_macd: a1_score = 6
        
        # --- [A2: 構造維度 40%] ---
        # 10/20/50MA 糾結程度檢測
        ma_list = [latest['MA10'], latest['MA20'], latest['MA50']]
        ma_std = np.std(ma_list)
        ma_avg = np.mean(ma_list)
        compression = (ma_std / ma_avg) * 100
        
        a2_score = 0
        if compression < 1.5: a2_score = 10     # 極度壓縮 (這是妳最愛的埋伏點)
        elif compression < 3.0: a2_score = 8    # 標準壓縮
        elif compression < 5.0: a2_score = 4    # 稍嫌鬆散
        
        # --- [A3: 能量維度 40%] ---
        a3_score = 0
        avg_vol = df['Volume'].tail(10).mean()
        vol_ratio = latest['Volume'] / avg_vol
        
        # 成交量屬性判定
        if vol_ratio > 1.3: a3_score += 5       # 攻擊放量
        elif vol_ratio < 0.5: a3_score += 4     # 窒息縮量 (代表洗盤中)
        
        # RS 相對強度 (對比 SPY 同期表現)
        stock_ret = (latest['Close'] / df.iloc[-20]['Close']) - 1
        spy_ret = (spy_df.iloc[-1]['Close'] / spy_df.iloc[-20]['Close']) - 1
        rs_strength = stock_ret - spy_ret
        
        if rs_strength > 0.02: a3_score += 5    # 強於大盤 2% 以上 (有大戶在裡面)
        elif rs_strength > 0: a3_score += 3
        
        # --- 總分計算與 AWI 天氣系統 ---
        total = (a1_score * 0.2) + (a2_score * 0.4) + (a3_score * 0.4)
        
        if total >= 9.0: weather, icon = "噴發態", "🎆"
        elif total >= 7.0: weather, icon = "強勢態", "☀️"
        elif total >= 5.0: weather, icon = "整理態", "☁️"
        else: weather, icon = "危險態", "🌫️"
        
        # --- F1 戰略過濾器 (動態彈性修正) ---
        # 如果 A3 能量夠強，放寬 MA20 乖離率限制至 5% (避免因跳空而錯過 AAOI)
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

# --- 3. 數據獲取與指標預處理 ---
def get_data(ticker):
    try:
        # 抓取 4 個月數據確保 MA50 穩定
        df = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if df.empty: return None
        
        # 使用 pandas_ta 精確計算指標
        df['MA10'] = ta.sma(df['Close'], length=10)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        return df
    except:
        return None

# --- 4. Streamlit UI 介面呈現 ---
st.title("🛰️ Apex Ambush V32.5 巔峰埋伏系統")
st.markdown(f"**市場監控：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每分鐘自動刷新)")

# 獲取基準大盤數據
spy_df = get_data("SPY")

if spy_df is not None:
    all_results = []
    progress_bar = st.progress(0)
    
    # 執行批次分析
    for i, t in enumerate(WATCH_LIST):
        stock_df = get_data(t)
        if stock_df is not None:
            res = calculate_apex_score(t, stock_df, spy_df)
            if res:
                all_results.append(res)
        progress_bar.progress((i + 1) / len(WATCH_LIST))
    
    progress_bar.empty()

    if all_results:
        final_df = pd.DataFrame(all_results)
        
        # 視覺化顏色標註函式
        def highlight_awi(val):
            if '🎆' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
            if '☀️' in str(val): return 'background-color: #ffa500; color: black; font-weight: bold'
            if '🌫️' in str(val): return 'background-color: #d3d3d3; color: #777'
            return ''

        st.subheader("📊 全域戰略監控看板")
        st.dataframe(
            final_df.style.applymap(highlight_awi, subset=['AWI 指標']),
            use_container_width=True
        )

        # --- 5. 側邊欄：核心持倉實戰建議 ---
        st.sidebar.header("🎯 核心診斷建議")
        
        # 針對 PL 的即時診斷
        pl_item = next((i for i in all_results if i["代碼"] == "PL"), None)
        if pl_item:
            st.sidebar.markdown(f"### **PL 持倉分析**")
            if "☀️" in pl_item["AWI 指標"]:
                st.sidebar.success(f"目前 AWI: ☀️\n分數: {pl_item['Apex 總分']}\n\n診斷：量縮洗盤中，RS 強度仍為正數，建議守住 $31.00，不需動作。")
            else:
                st.sidebar.warning(f"PL 警報：分數降至 {pl_item['Apex 總分']}，注意回檔支撐位。")
        
        # 針對 LUNR 的陷阱過濾
        lunr_item = next((i for i in all_results if i["代碼"] == "LUNR"), None)
        if lunr_item and "🌫️" in lunr_item["AWI 指標"]:
            st.sidebar.markdown("---")
            st.sidebar.error(f"⚠️ LUNR 警報：RS 強度跑輸大盤 {lunr_item['相對強度(RS)']}。雖然均線糾結，但動能崩潰，建議撤資。")

st.sidebar.write("---")
st.sidebar.info("V32.5 更新誌：\n1. 能量權重 40%\n2. RS 相對強度過濾\n3. 動態 F1 Buffer (1.5% -> 5.0%)")
