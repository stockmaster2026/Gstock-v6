
import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="三維戰略指揮中心 V7.7", layout="wide")

# --- 1. 板塊資料庫擴充 ---
SECTORS = {
    "核心算力 (AI Core)": ["NVDA", "AMD", "AVGO", "MRVL", "ARM", "TSM", "SMCI", "ALAB"],
    "存儲板塊 (Storage)": ["MU", "WDC", "STX", "PSTG", "NTAP", "WRLD"],
    "太空板塊 (Space)": ["PLTR", "RKLB", "BKSY", "LUNR", "SPCE", "MAXR", "ASTS"],
    "電力能源 (Power)": ["VST", "CEG", "OKLO", "SMR", "nE"],
    "量子計算 (Quantum)": ["IONQ", "RGTI", "QUBT", "D-WAVE"]
}

# --- 2. 核心邏輯函式 ---
def fetch_stock_data(ticker):
    """抓取資料並進行防呆檢查"""
    try:
        if not ticker:
            return None
        stock = yf.Ticker(ticker)
        # 抓取 1 年數據以計算長線趨勢
        df = stock.history(period="1y")
        if df.empty or len(df) < 20:
            return None
        return df
    except Exception:
        return None

def analyze_strategy(df):
    """三維戰略判定邏輯"""
    # 計算指標
    current_price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]  # 生命線
    ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
    
    # 1. 生命線判定
    above_ma20 = current_price > ma20
    
    # 2. 短線動能 (RSI 簡化版或近期漲幅)
    momentum = df['Close'].pct_change(periods=5).iloc[-1] > 0
    
    # 3. 趨勢判定 (均線多頭排列)
    trend_up = ma20 > ma50
    
    return {
        "price": current_price,
        "ma20": ma20,
        "signals": [above_ma20, momentum, trend_up]
    }

# --- 3. 側邊欄：指揮控制 ---
st.sidebar.title("🕹️ 指揮控制")
st.sidebar.markdown("---")

custom_input = st.sidebar.text_input("📡 輸入新偵察代號 (用逗號隔開):", placeholder="例如: TSLA, AAPL")
current_sector = st.sidebar.selectbox("當前戰略板塊", list(SECTORS.keys()))

# 整合顯示清單
watchlist = SECTORS[current_sector].copy()
if custom_input:
    new_tickers = [x.strip().upper() for x in custom_input.split(',') if x.strip()]
    watchlist = new_tickers + watchlist # 優先顯示新輸入的

# --- 4. 主界面顯示 ---
st.title(f"🛡️ 三維戰略指揮中心 V7.7")
st.info(f"當前戰略模式：三維過濾器 V7.7 | 監測板塊：{current_sector}")

# 使用 Columns 顯示多個標的，增加級檔豐富度
cols = st.columns(len(watchlist) if len(watchlist) < 4 else 4)

for i, ticker in enumerate(watchlist):
    with cols[i % 4]:
        df = fetch_stock_data(ticker)
        
        if df is None:
            # 這裡就是修正第 84 行 TypeError 的關鍵：找不到資料時顯示警告而非崩潰
            st.warning(f"⚠️ {ticker} 偵訊中斷")
            continue
            
        res = analyze_strategy(df)
        
        # UI 顯示
        st.subheader(f"{ticker}")
        
        # 三維信號燈
        status = []
        labels = ["生命線", "短線動能", "趨勢"]
        for j, s in enumerate(res['signals']):
            icon = "✅" if s else "❌"
            color = "white" if s else "gray"
            status.append(f"{icon} {labels[j]}")
            st.write(f"{icon} {labels[j]}")

        # 戰略建議
        score = sum(res['signals'])
        if score == 3:
            st.success("📈 進入階段：全力進攻")
        elif score == 2:
            st.warning("🟡 觀望階段：謹慎持有")
        else:
            st.error("🚨 走跌階段：全力撤退")
            
        st.divider()

# --- 5. 系統底層檢查 ---
if not watchlist:
    st.write("目前無偵察標的，請於左側輸入代號。")


  



