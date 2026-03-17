import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --- [ 1. 頁面初始化 ] ---
st.set_page_config(page_title="核心加減碼：真實數據實戰系統", layout="wide")

# --- [ 2. 完整監控板塊定義 (不遺漏任何一個) ] ---
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
    """
    遵循您要求的核心邏輯與幅度：
    - 滿倉 (100%): F1, F2, F3 三方共振
    - 加碼 (50%): 趨勢穩定 (F1高) + 動能轉強
    - 試單 (20%): 趨勢剛轉正
    - 減碼 (-50%): 趨勢(F1) 破位 < 60
    """
    if f1 >= 85 and total >= 80:
        return "🔥 滿倉 (100%)", "核心指令：三方共振，全力加碼"
    elif f1 >= 80 and f2 >= 70:
        return "✅ 重倉 (50%)", "核心指令：趨勢與動能轉強，加碼 30%"
    elif f1 >= 75:
        return "🧐 試單 (20%)", "核心指令：趨勢轉正，建立基本倉"
    elif f1 < 60:
        return "⚠️ 減碼 (-50%)", "核心指令：趨勢破位，立即縮減一半"
    elif total < 50:
        return "❌ 清倉 (0%)", "核心指令：全面走弱，退出觀望"
    else:
        return "⚖️ 持股 (20%)", "核心指令：維持基本試單，等待共振"

def calculate_real_metrics(ticker):
    """
    從 Yahoo Finance 抓取真實數據並計算指標
    """
    try:
        # 抓取最近 60 天數據
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return 0, 0, 0, 0, "無數據", "代碼錯誤"
        
        # 取得最新收盤價與指標
        close = df['Close'].iloc[-1].item()
        ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
        ma50 = df['Close'].rolling(50).mean().iloc[-1].item()
        vol_now = df['Volume'].iloc[-1].item()
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1].item()
        
        # F1: 趨勢得分 (價格相對於均線)
        if close > ma20 > ma50: f1 = 100
        elif close > ma20: f1 = 80
        elif close > ma50: f1 = 65
        else: f1 = 40
        
        # F2: 動能得分 (真實 RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1].item()))
        f2 = int(rsi)
        
        # F3: 量能得分 (量比)
        f3 = min(int((vol_now / vol_avg) * 100), 100)
        
        total = round((f1 * 0.4 + f2 * 0.3 + f3 * 0.3), 2)
        pos, adv = get_strategy_logic(f1, f2, f3, total)
        
        return f1, f2, f3, total, pos, adv
    except:
        return 0, 0, 0, 0, "錯誤", "網路異常"

# --- [ 4. Streamlit 介面 ] ---
st.title("🛡️ 核心三濾網：真實數據加減碼系統")
st.markdown("---")

# 側邊欄單檔查詢 (保證 NVDA/TSLA 顯示真實現況)
with st.sidebar:
    st.header("🎯 個股核心診斷")
    t_input = st.text_input("輸入代號 (如: NVDA, TSLA):").upper().strip()
    if t_input:
        f1, f2, f3, tot, pos, adv = calculate_real_metrics(t_input)
        st.subheader(f"分析標的: {t_input}")
        st.metric("建議倉位", pos)
        st.info(f"建議動作：{adv}")
        st.write(f"F1 趨勢: {f1} | F2 動能: {f2} | F3 量能: {f3}")

# 主畫面執行
if st.button("🔄 執行全板塊真實數據掃描 (ALL)"):
    weather_summary = []
    for sector, tickers in WATCH_LIST.items():
        st.subheader(f"📂 {sector}")
        res = []
        sec_scores = []
        for t in tickers:
            f1, f2, f3, tot, pos, adv = calculate_real_metrics(t)
            res.append({
                "代碼": t, "趨勢(F1)": f1, "動能(F2)": f2, 
                "量能(F3)": f3, "總分": tot, "建議倉位": pos, "核心說明": adv
            })
            sec_scores.append(tot)
        
        st.table(pd.DataFrame(res))
        avg = np.mean(sec_scores)
        weather = "☀️ 晴" if avg > 75 else "🌤️ 雲" if avg > 60 else "🌧️ 雨"
        weather_summary.append({"板塊": sector, "平均分": round(avg, 2), "氣候": weather})
        st.markdown("---")

    st.header("🌍 市場板塊氣候總覽")
    st.dataframe(pd.DataFrame(weather_summary), use_container_width=True)
else:
    st.warning("💡 請點擊上方按鈕啟動真實資料掃描。")







  



