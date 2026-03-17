
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --- [ 1. 頁面配置 ] ---
st.set_page_config(page_title="核心加減碼：真實數據實戰系統", layout="wide")

# --- [ 2. 完整監控板塊定義 (核心 Clubbing) ] ---
WATCH_LIST = {
    "太空板塊 (Space)": ["RKLB", "LUNR", "PL", "ASTS", "SPCE"],
    "光通訊板塊 (Optical)": ["LITE", "AAOI", "FN", "COHR", "AVGO"],
    "AI 醫療板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心": ["NVDA", "TSM", "AMD", "ARM", "ASML"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
}

# --- [ 3. 核心加減碼策略邏輯 (依據討論幅度) ] ---
def get_strategy_logic(f1, f2, f3, total):
    # 滿倉 100%: F1, F2, F3 三方共振 (均強)
    if f1 >= 85 and f2 >= 80 and f3 >= 80:
        return "🔥 滿倉 (100%)", "核心指令：三方共振，全力加碼"
    # 重倉 50%: 趨勢穩定 (F1高) + 動能轉強
    elif f1 >= 80 and f2 >= 70:
        return "✅ 重倉 (50%)", "核心指令：趨勢與動能強，加碼 30%"
    # 試單 20%: 趨勢剛轉正
    elif f1 >= 75:
        return "🧐 試單 (20%)", "核心指令：趨勢轉正，建立基本倉"
    # 減碼 -50%: 趨勢(F1) 破位 < 60
    elif f1 < 60:
        return "⚠️ 減碼 (-50%)", "核心指令：趨勢破位，立即減碼一半"
    else:
        return "❌ 觀望 (0%)", "核心指令：全面走弱，退出觀望"

# --- [ 4. 強化真實數據抓取 (解決 RKLB=0 的問題) ] ---
@st.cache_data(ttl=600)
def calculate_real_metrics(ticker):
    try:
        # 抓取最近 65 天數據以確保均線完整
        df = yf.download(ticker, period="65d", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 50: 
            return 0, 0, 0, 0, "數據不足", "代碼或數據異常"
        
        # 數據清洗：處理可能存在的 NaN
        df = df.ffill()
        
        # 取得最新收盤價與指標
        close = df['Close'].iloc[-1].item()
        ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
        ma50 = df['Close'].rolling(50).mean().iloc[-1].item()
        vol_now = df['Volume'].iloc[-1].item()
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1].item()
        
        # F1: 趨勢 (價格相對於 MA20, MA50)
        if close > ma20 > ma50: f1 = 100
        elif close > ma20: f1 = 80
        elif close > ma50: f1 = 65
        else: f1 = 40
        
        # F2: 動能 (真實 RSI 14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1].item()))
        f2 = int(rsi)
        
        # F3: 量能 (量比)
        f3 = min(int((vol_now / (vol_avg if vol_avg > 0 else 1)) * 100), 100)
        
        total = round((f1 * 0.4 + f2 * 0.3 + f3 * 0.3), 2)
        pos, adv = get_strategy_logic(f1, f2, f3, total)
        return f1, f2, f3, total, pos, adv
    except Exception as e:
        return 0, 0, 0, 0, "錯誤", str(e)

# --- [ 5. 介面渲染 ] ---
st.title("🛡️ 核心三濾網：實戰板塊晴雨表 & 加減碼系統")
st.markdown("---")

# 側邊欄：單檔快查 (修正之前輸入 TSLA 沒反應的問題)
with st.sidebar:
    st.header("🎯 個股核心快查")
    t_input = st.text_input("輸入代號 (如: RKLB, NVDA):").upper().strip()
    if t_input:
        f1, f2, f3, tot, pos, adv = calculate_real_metrics(t_input)
        st.metric(f"{t_input} 建議倉位", pos)
        st.info(f"建議動作：{adv}")
        st.write(f"趨勢: {f1} | 動能: {f2} | 量能: {f3}")

# 主功能按鈕
if st.button("🔄 執行全板塊真實數據掃描 (ALL)"):
    all_data = {}
    weather_summary = []
    
    # 執行運算
    with st.spinner('正在從市場抓取真實數據...'):
        for sector, tickers in WATCH_LIST.items():
            sector_res = []
            sector_scores = []
            for t in tickers:
                f1, f2, f3, tot, pos, adv = calculate_real_metrics(t)
                sector_res.append({"代碼": t, "趨勢(F1)": f1, "動能(F2)": f2, "量能(F3)": f3, "總分": tot, "建議倉位": pos, "策略說明": adv})
                sector_scores.append(tot)
            
            all_data[sector] = pd.DataFrame(sector_res)
            avg_s = np.mean(sector_scores)
            weather = "☀️ 晴" if avg_s > 75 else "🌤️ 雲" if avg_s > 60 else "🌧️ 雨"
            weather_summary.append({"板塊": sector, "平均分": round(avg_s, 2), "氣候": weather})

    # --- A. [置頂] 市場板塊晴雨表 ---
    st.header("🌍 1. 市場板塊晴雨表 (總覽)")
    st.table(pd.DataFrame(weather_summary))
    st.markdown("---")

    # --- B. [下方] 板塊明細 (Clubbing) ---
    st.header("🔍 2. 板塊個股三濾網明細")
    for sector, df in all_data.items():
        st.subheader(f"📂 {sector}")
        # 加入顏色高亮：減碼為紅色，滿倉/加碼為綠色
        st.dataframe(df.style.applymap(lambda x: 'color: red' if '減碼' in str(x) else ('color: #00FF00' if '倉' in str(x) else ''), subset=['建議倉位']), use_container_width=True)
        st.markdown("---")
else:
    st.warning("💡 請點擊上方按鈕啟動真實資料掃描。RKLB 數據已優化，晴雨表將置頂顯示。")



  



