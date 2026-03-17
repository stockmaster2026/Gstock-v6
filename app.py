
import streamlit as st
import pandas as pd
import numpy as np

# --- [ 1. 頁面初始化與核心配置 ] ---
st.set_page_config(page_title="終極核心加減碼系統", layout="wide")

# 定義核心權重 (根據我們討論的核心)
WEIGHTS = {"Trend": 0.4, "Momentum": 0.3, "Volume": 0.3}

# --- [ 2. 完整監控板塊定義 (Clubbing - 不遺漏任何板塊) ] ---
WATCH_LIST = {
    "太空板塊 (Space)": ["RKLB", "LUNR", "PL", "SPCE", "ASTS"],
    "光通訊板塊 (Optical)": ["LITE", "AAOI", "FN", "COHR", "AVGO"],
    "AI 醫療熱門板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心板塊": ["NVDA", "TSM", "AMD", "AVGO", "ARM"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"],
    "市場指數與避險": ["SPY", "QQQ", "VIX", "BITO"]
}

# --- [ 3. 核心加減碼幅度計算邏輯 ] ---
def get_position_strategy(f1, f2, f3, total):
    """
    回歸我們討論的原始邏輯：
    - 滿倉 100%: F1, F2, F3 三方共振 (均 >= 80)
    - 重倉 50%: F1 穩固 + F2 動能轉強
    - 試單 20%: F1 趨勢剛轉正 (>= 75)
    - 減碼 -50%: F1 趨勢破位 (< 60) 
    - 清倉 0%: 總分過低或全面轉弱
    """
    if f1 >= 85 and f2 >= 80 and f3 >= 80:
        return "🔥 滿倉 (100%)", "核心指令：三方共振，打滿倉位"
    elif f1 >= 80 and f2 >= 75:
        return "✅ 重倉 (50%)", "核心指令：趨勢與動能同步，加碼 30%"
    elif f1 >= 75:
        return "🧐 試單 (20%)", "核心指令：趨勢轉正，建立基本倉"
    elif f1 < 60:
        return "⚠️ 減碼 (-50%)", "核心指令：趨勢破位，立即減碼一半"
    elif total < 50:
        return "❌ 清倉 (0%)", "核心指令：全面走弱，資金離場"
    else:
        return "⚖️ 持股 (20%)", "核心指令：維持基本試單，等待共振"

def process_stock_data(ticker):
    # 此處目前為模擬計分，未來串接報價 API
    f1 = np.random.randint(40, 100) # 趨勢
    f2 = np.random.randint(40, 100) # 動能
    f3 = np.random.randint(40, 100) # 量能
    total = round((f1 * WEIGHTS["Trend"] + f2 * WEIGHTS["Momentum"] + f3 * WEIGHTS["Volume"]), 2)
    pos_size, advice = get_position_strategy(f1, f2, f3, total)
    return f1, f2, f3, total, pos_size, advice

# --- [ 4. Streamlit 介面渲染 ] ---
st.title("🛡️ 核心三濾網：個股加減碼 & 全板塊晴雨表")
st.markdown("---")

# 側邊欄：解決輸入代號無回應問題
with st.sidebar:
    st.header("🎯 單檔個股快查")
    input_ticker = st.text_input("輸入代號 (如: RKLB, TSLA):").upper().strip()
    if input_ticker:
        f1, f2, f3, total, pos, adv = process_stock_data(input_ticker)
        st.subheader(f"分析報告: {input_ticker}")
        st.metric("建議倉位幅度", pos)
        if "-" in pos or "0%" in pos:
            st.error(f"操作邏輯: {adv}")
        else:
            st.success(f"操作邏輯: {adv}")
        st.write(f"---")
        st.write(f"F1 趨勢分: {f1}")
        st.write(f"F2 動能分: {f2}")
        st.write(f"F3 量能分: {f3}")
        st.write(f"加權總分: {total}")
    st.markdown("---")

# 主畫面：執行全板塊掃描
if st.button("🔄 執行全板塊同步掃描 (ALL)"):
    weather_summary = []
    
    # 按板塊聚合 (Clubbing)，保證不凌亂
    for sector, tickers in WATCH_LIST.items():
        st.subheader(f"📂 {sector}")
        
        sector_results = []
        sector_scores = []
        
        for t in tickers:
            f1, f2, f3, total, pos, adv = process_stock_data(t)
            sector_results.append({
                "代碼": t,
                "趨勢(F1)": f1,
                "動能(F2)": f2,
                "量能(F3)": f3,
                "加權總分": total,
                "建議倉位": pos,
                "核心動作說明": adv
            })
            sector_scores.append(total)
        
        # 顯示該板塊表格
        st.table(pd.DataFrame(sector_results))
        
        # 計算晴雨表
        avg_s = np.mean(sector_scores)
        weather = "☀️ 晴" if avg_s > 75 else "🌤️ 雲" if avg_s > 60 else "🌧️ 雨"
        weather_summary.append({"板塊": sector, "平均分": round(avg_s, 2), "氣候狀態": weather})
        st.write(f"**板塊結語：** 平均 {round(avg_s, 2)} | 狀態：{weather}")
        st.markdown("---")

    # 顯示最終彙整
    st.header("🌍 全市場板塊氣候總覽")
    st.dataframe(pd.DataFrame(weather_summary), use_container_width=True)

else:
    st.info("💡 請點擊上方按鈕，系統將依照板塊（太空、光通訊、醫療等）彙整顯示所有監控標的。")







  



