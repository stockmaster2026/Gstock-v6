import streamlit as st
import pandas as pd
import numpy as np

# --- [ 1. 頁面初始化與核心權重設定 ] ---
st.set_page_config(page_title="核心加減碼：市場晴雨表系統", layout="wide")

# 定義核心濾網權重 (趨勢 40%, 動能 30%, 量能 30%)
WEIGHTS = {"Trend": 0.4, "Momentum": 0.3, "Volume": 0.3}

# --- [ 2. 完整監控板塊定義 (Clubbing) ] ---
# 確保包含所有熱門與原有板塊，並以此順序顯示
WATCH_LIST = {
    "AI 醫療熱門板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC", "TDOC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心板塊": ["NVDA", "TSM", "AMD", "AVGO", "ARM", "ASML"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"],
    "指數與市場情緒": ["SPY", "QQQ", "VIX", "BITO"]
}

# --- [ 3. 核心加減碼操作建議邏輯 ] ---
def get_core_action(f1, f2, f3, total):
    """
    回歸討論的核心邏輯：
    - 加碼：總分強勢且趨勢(F1)領先
    - 減碼：趨勢(F1)一旦破位即發出警訊
    """
    if total >= 85 and f1 >= 85:
        return "🔥 強烈加碼 (三方共振)"
    elif total >= 70 and f1 >= 70:
        return "✅ 持有 / 分批加碼"
    elif f1 < 60:
        return "⚠️ 減碼 (趨勢轉弱)"
    elif total < 50:
        return "❌ 清倉 / 觀望"
    else:
        return "持股觀望"

def calculate_stock_data(ticker):
    """
    模擬數據抓取，此處預留串接 yfinance API。
    """
    # 產出 0-100 的隨機分數作為基礎，實際使用可接真實指標
    f1 = np.random.randint(40, 100) # 趨勢分數
    f2 = np.random.randint(40, 100) # 動能分數
    f3 = np.random.randint(40, 100) # 量能分數
    total = round((f1 * WEIGHTS["Trend"] + f2 * WEIGHTS["Momentum"] + f3 * WEIGHTS["Volume"]), 2)
    action = get_core_action(f1, f2, f3, total)
    return f1, f2, f3, total, action

# --- [ 4. Streamlit 介面佈局 ] ---
st.title("🛡️ 核心三濾網：個股加減碼 & 板塊晴雨表")
st.markdown("---")

# 側邊欄：單檔快速診斷 (修正 Input 無回應問題)
with st.sidebar:
    st.header("🎯 單檔個股查詢")
    user_ticker = st.text_input("輸入股票代號 (如: TSLA, IONQ):").upper().strip()
    if user_ticker:
        f1, f2, f3, total, action = calculate_stock_data(user_ticker)
        st.subheader(f"分析結果: {user_ticker}")
        st.metric("加權總得分", f"{total}")
        st.info(f"建議操作：{action}")
        st.write(f"- 趨勢(F1): {f1}")
        st.write(f"- 動能(F2): {f2}")
        st.write(f"- 量能(F3): {f3}")
    st.markdown("---")
    st.write("系統狀態：核心邏輯已載入")

# 主畫面：全板塊掃描與聚合顯示
if st.button("🔄 執行全板塊 Club 掃描 (ALL)"):
    weather_report = []
    
    # 按板塊「Club」起來顯示，確保不凌亂
    for sector, tickers in WATCH_LIST.items():
        st.subheader(f"📁 板塊分類：{sector}")
        
        sector_results = []
        sector_totals = []
        
        for ticker in tickers:
            f1, f2, f3, total, action = calculate_stock_data(ticker)
            sector_results.append({
                "代碼": ticker,
                "趨勢(F1)": f1,
                "動能(F2)": f2,
                "量能(F3)": f3,
                "加權總分": total,
                "加減碼建議": action
            })
            sector_totals.append(total)
        
        # 顯示該板塊細節表格
        df_sector = pd.DataFrame(sector_results)
        st.table(df_sector) # 使用 table 顯示所有欄位，確保不被隱藏
        
        # 計算板塊平均與天氣
        avg_score = round(np.mean(sector_totals), 2)
        weather = "☀️ 晴" if avg_score > 75 else "🌤️ 雲" if avg_score > 60 else "🌧️ 雨"
        weather_report.append({"板塊": sector, "平均分": avg_score, "晴雨狀態": weather})
        
        st.write(f"**板塊小結：** 平均分數 {avg_score} | 氣候：{weather}")
        st.markdown("---")

    # 在最下方顯示晴雨表總結
    st.header("🌍 市場板塊氣候總覽")
    st.dataframe(pd.DataFrame(weather_report), use_container_width=True)

else:
    st.warning("💡 點擊上方按鈕，將會依照您要求的「板塊聚合」方式顯示所有監控標的。")







  



