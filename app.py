import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 設定頁面配置 ---
st.set_page_config(page_title="市場晴雨表系統", layout="wide")

# --- 2. 完整板塊清單 (包含您要求的所有領域) ---
SECTORS = {
    "量子運算板塊 (Quantum)": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "AI 醫療板塊 (AI Healthcare)": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "半導體核心": ["NVDA", "TSM", "AMD", "AVGO", "ARM", "ASML"],
    "大型科技股 (Big Tech)": ["AAPL", "MSFT", "AMZN", "GOOGL", "META"],
    "電動車與能源": ["TSLA", "RIVN", "LCID", "ENPH"],
    "市場指數參考": ["SPY", "QQQ", "IWM", "VIX"]
}

# --- 3. 核心濾網計算邏輯 (F1, F2, F3) ---
def calculate_filter_scores(ticker):
    """
    這裡定義三個 Filter 的評分邏輯。
    實際應用時，此處可串接 yfinance 獲取真實價格與指標。
    """
    # F1: 趨勢濾網 (Trend) - 基於價格高於均線的程度
    # 這裡模擬：若價格站上所有均線為 100，跌破為 0
    f1_score = np.random.randint(40, 100) 
    
    # F2: 動能濾網 (Momentum) - 基於 RSI 或 MACD 強度
    # 這裡模擬：強勢噴發為 100，超賣或疲弱為 30
    f2_score = np.random.randint(30, 100)
    
    # F3: 成交量濾網 (Volume) - 基於量價配合度 (量增價漲)
    # 這裡模擬：當前成交量 > 20日均量則高分
    f3_score = np.random.randint(20, 100)
    
    # 加權總分 (趨勢 40%, 動能 30%, 成交量 30%)
    total_score = round((f1_score * 0.4 + f2_score * 0.3 + f3_score * 0.3), 2)
    
    return f1_score, f2_score, f3_score, total_score

# --- 4. 側邊欄：單檔查詢與參數設定 ---
st.sidebar.title("🛠️ 控制面板")
user_ticker = st.sidebar.text_input("輸入個股代號查詢 (如: TSLA, IONQ):", "").upper()

# --- 5. 主畫面佈局 ---
st.title("☀️ 市場晴雨表系統 (三濾網加權評分)")
st.markdown("---")

# 處理單檔查詢
if user_ticker:
    st.subheader(f"📊 個股詳細診斷: {user_ticker}")
    f1, f2, f3, total = calculate_filter_scores(user_ticker)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("F1 趨勢得分", f"{f1}")
    col2.metric("F2 動能得分", f"{f2}")
    col3.metric("F3 量能得分", f"{f3}")
    col4.metric("🏆 加權總評分", f"{total}")
    st.markdown("---")

# 執行全板塊掃描按鈕
if st.button("🔄 執行全板塊同步掃描 (ALL)"):
    all_rows = []
    sector_weather_data = []

    for sector_name, tickers in SECTORS.items():
        sector_total = 0
        for ticker in tickers:
            f1, f2, f3, total = calculate_filter_scores(ticker)
            all_rows.append({
                "板塊": sector_name,
                "代碼": ticker,
                "趨勢(F1)": f1,
                "動能(F2)": f2,
                "量能(F3)": f3,
                "加權總分": total
            })
            sector_total += total
        
        # 計算板塊平均氣候
        avg_score = sector_total / len(tickers)
        if avg_score >= 75: 
            weather = "☀️ 大太陽"
            color = "green"
        elif avg_score >= 60: 
            weather = "🌤️ 晴時多雲"
            color = "blue"
        elif avg_score >= 45: 
            weather = "☁️ 陰天"
            color = "gray"
        else: 
            weather = "🌧️ 降雨"
            color = "red"
            
        sector_weather_data.append({
            "板塊": sector_name,
            "平均分數": round(avg_score, 2),
            "當前氣候": weather
        })

    # 顯示結果：1. 市場晴雨表
    st.header("1️⃣ 市場板塊晴雨表總覽")
    weather_df = pd.DataFrame(sector_weather_data)
    st.table(weather_df)

    # 顯示結果：2. 個股三濾網明細
    st.header("2️⃣ 個股三濾網詳細評分表 (含加權)")
    detail_df = pd.DataFrame(all_rows)
    # 按總分由高到低排序
    st.dataframe(detail_df.sort_values(by="加權總分", ascending=False), use_container_width=True)

else:
    st.info("💡 請點擊上方按鈕開始掃描所有板塊，或在左側選單輸入代號進行診斷。")






  



