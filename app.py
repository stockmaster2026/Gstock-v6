
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --- [ 1. 頁面配置 ] ---
st.set_page_config(page_title="核心加減碼實戰系統", layout="wide")

# --- [ 2. 完整監控板塊 (不遺漏太空、光通訊、AI醫療) ] ---
WATCH_LIST = {
    "太空板塊 (Space)": ["RKLB", "LUNR", "PL", "ASTS", "SPCE"],
    "光通訊板塊 (Optical)": ["LITE", "AAOI", "FN", "COHR", "AVGO"],
    "AI 醫療板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心": ["NVDA", "TSM", "AMD", "ARM", "ASML"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
}

# --- [ 3. 核心加減碼幅度計分邏輯 ] ---
def get_strategy_logic(f1, f2, f3, total):
    # 滿倉 100%: 三方共振 (均 >= 80)
    if f1 >= 85 and f2 >= 80 and f3 >= 80:
        return "🔥 滿倉 (100%)", "三方共振，全力加碼"
    # 重倉 50%: 趨勢穩、動能強
    elif f1 >= 80 and f2 >= 70:
        return "✅ 重倉 (50%)", "趨勢穩定且動能強，加碼 30%"
    # 試單 20%: 趨勢轉正
    elif f1 >= 75:
        return "🧐 試單 (20%)", "趨勢轉正，建立基本倉"
    # 減碼 -50%: 趨勢(F1) 破位 < 60
    elif f1 < 60:
        return "⚠️ 減碼 (-50%)", "趨勢破位，立即減碼一半"
    else:
        return "❌ 觀望 (0%)", "不符核心條件，離場觀望"

def calculate_real_metrics(ticker):
    try:
        # 下載真實數據
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return 0, 0, 0, 0, "無數據", "代碼錯誤"
        
        close = df['Close'].iloc[-1].item()
        ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
        ma50 = df['Close'].rolling(50).mean().iloc[-1].item()
        vol_now = df['Volume'].iloc[-1].item()
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1].item()
        
        # F1: 趨勢 (價格 vs 均線)
        if close > ma20 > ma50: f1 = 100
        elif close > ma20: f1 = 80
        elif close > ma50: f1 = 65
        else: f1 = 40
        
        # F2: 動能 (RSI 14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss).iloc[-1].item()))
        f2 = int(rsi)
        
        # F3: 量能 (量比)
        f3 = min(int((vol_now / vol_avg) * 100), 100)
        
        total = round((f1 * 0.4 + f2 * 0.3 + f3 * 0.3), 2)
        pos, adv = get_strategy_logic(f1, f2, f3, total)
        return f1, f2, f3, total, pos, adv
    except:
        return 0, 0, 0, 0, "錯誤", "系統異常"

# --- [ 4. Streamlit 網頁呈現 ] ---
st.title("🛡️ 核心三濾網：真實數據實戰系統")
st.write("數據來源：Yahoo Finance | 策略：三濾網加減碼邏輯")

# 側邊欄：單檔診斷
st.sidebar.header("🎯 個股核心快查")
t_input = st.sidebar.text_input("輸入代號 (如: NVDA, TSLA):").upper().strip()

if t_input:
    f1, f2, f3, tot, pos, adv = calculate_real_metrics(t_input)
    st.sidebar.metric(f"{t_input} 建議倉位", pos)
    st.sidebar.info(f"建議：{adv}")
    st.sidebar.write(f"趨勢: {f1} | 動能: {f2} | 量能: {f3}")

# 主畫面：全板塊按鈕
if st.button("🔄 執行全板塊真實數據掃描"):
    summary = []
    for sector, tickers in WATCH_LIST.items():
        st.subheader(f"📂 {sector}")
        res = []
        sec_scores = []
        for t in tickers:
            f1, f2, f3, tot, pos, adv = calculate_real_metrics(t)
            res.append({"代碼": t, "趨勢(F1)": f1, "動能(F2)": f2, "量能(F3)": f3, "總分": tot, "建議倉位": pos, "說明": adv})
            sec_scores.append(tot)
        
        st.table(pd.DataFrame(res))
        avg = np.mean(sec_scores)
        weather = "☀️ 晴" if avg > 75 else "🌤️ 雲" if avg > 60 else "🌧️ 雨"
        summary.append({"板塊": sector, "平均分": round(avg, 2), "氣候": weather})
    
    st.header("🌍 市場板塊晴雨表")
    st.table(pd.DataFrame(summary))
else:
    st.warning("💡 請點擊上方按鈕啟動真實資料掃描，解決轉圈圈問題。")



  



