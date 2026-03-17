import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --- [ 1. 頁面配置 ] ---
st.set_page_config(page_title="核心三濾網戰術儀表板", layout="wide")

# --- [ 2. 完整監控板塊 (Clubbing) ] ---
WATCH_LIST = {
    "太空板塊 (Space)": ["RKLB", "LUNR", "PL", "ASTS", "SPCE"],
    "光通訊板塊 (Optical)": ["LITE", "AAOI", "FN", "COHR", "AVGO"],
    "AI 醫療板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心": ["NVDA", "TSM", "AMD", "ARM", "ASML"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
}

# --- [ 3. 核心階梯式邏輯與連跌修正 ] ---
def get_strategy_logic(f1, f2, f3, total, chg_pct, is_dropping):
    # 滿倉 100%: 三方共振 且 當天不能是大跌 且 不能是連跌
    if f1 >= 85 and f2 >= 80 and f3 >= 80 and not is_dropping and chg_pct > -1:
        return "🔥 滿倉 (100%)", "多頭共振，最強狀態"
    # 重倉 50%: 趨勢穩 且 動能不弱
    elif f1 >= 80 and f2 >= 70:
        return "✅ 重倉 (50%)", "趨勢穩定，動能尚可"
    # 試單 20%: 趨勢轉正
    elif f1 >= 75 and f2 >= 55:
        return "🧐 試單 (20%)", "初步轉強，建立觀察倉"
    # 階梯減碼 -30%: 動能快速下滑 或 出現連跌 或 漲跌幅過低
    elif is_dropping or f2 < 55 or chg_pct < -3:
        return "⚠️ 減碼 (-30%)", "動能背離/連跌，執行階梯保護"
    # 強力減碼 -70%: 趨勢破位
    elif f1 < 60:
        return "🚨 強力減碼 (-70%)", "趨勢嚴重破位，強制撤退"
    else:
        return "❌ 觀望 (0%)", "不符核心條件"

@st.cache_data(ttl=600)
def calculate_real_metrics(ticker):
    try:
        # 下載 100 天數據，確保均線精確
        df = yf.download(ticker, period="100d", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 20: 
            return [0]*9 + ["數據不足", "請檢查"]
        
        df = df.ffill()
        close = df['Close'].iloc[-1].item()
        prev_close = df['Close'].iloc[-2].item()
        chg_pct = ((close - prev_close) / prev_close) * 100
        
        # 均線數值
        ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
        ma50 = df['Close'].rolling(50).mean().iloc[-1].item()
        
        # 檢測是否連跌 (修正 AAOI 滿分問題)
        last_4 = df['Close'].iloc[-4:].tolist()
        is_dropping = all(last_4[i] > last_4[i+1] for i in range(len(last_4)-1))
        
        # F1: 趨勢得分
        if close > ma20 > ma50: f1 = 100
        elif close > ma20: f1 = 80
        elif close > ma50: f1 = 65
        else: f1 = 40
        
        # 如果連跌，強行降級 F1
        if is_dropping: f1 -= 25
        
        # F2: 動能 (RSI 14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss).iloc[-1].item()))
        f2 = int(rsi)
        
        # F3: 量能 (量比)
        v_now = df['Volume'].iloc[-1].item()
        v_avg = df['Volume'].rolling(20).mean().iloc[-1].item()
        f3 = min(int((v_now / v_avg) * 100), 100)
        
        total = round((f1 * 0.4 + f2 * 0.3 + f3 * 0.3), 2)
        pos, adv = get_strategy_logic(f1, f2, f3, total, chg_pct, is_dropping)
        
        return close, chg_pct, ma20, ma50, f1, f2, f3, total, is_dropping, pos, adv
    except Exception as e:
        return [0]*9 + ["錯誤", str(e)]

# --- [ 4. 主介面渲染 ] ---
st.title("🛡️ 核心三濾網：實戰戰情儀表板")
st.markdown("---")

# 側邊欄查詢
with st.sidebar:
    st.header("🎯 個股核心快查")
    t_input = st.text_input("輸入代號 (如: AAOI, NVDA):").upper().strip()
    if t_input:
        res = calculate_real_metrics(t_input)
        if res[-2] != "數據不足":
            st.metric(f"{t_input} 現價", f"{res[0]:.2f}", f"{res[1]:.2f}%")
            st.metric("建議倉位", res[-2])
            st.info(f"動作：{res[-1]}")
            st.write(f"趨勢 F1: {res[4]} | 動能 F2: {res[5]}")

# 執行按鈕
if st.button("🔄 刷新全板塊戰略數據 (ALL)"):
    all_results = {}
    weather_summary = []
    
    with st.spinner('正在同步全球市場數據...'):
        for sector, tickers in WATCH_LIST.items():
            sec_data = []
            sec_scores = []
            for t in tickers:
                p, c, m20, m50, f1, f2, f3, tot, drop, pos, adv = calculate_real_metrics(t)
                sec_data.append({
                    "代碼": t, "現價": round(p, 2), "漲跌%": f"{c:.2f}%",
                    "MA20": round(m20, 2), "趨勢(F1)": f1, "動能(F2)": f2,
                    "總分": tot, "建議倉位": pos, "核心動作": adv
                })
                sec_scores.append(tot)
            
            all_results[sector] = pd.DataFrame(sec_data)
            avg = np.mean(sec_scores)
            weather = "☀️ 晴" if avg > 75 else "🌤️ 雲" if avg > 60 else "🌧️ 雨"
            weather_summary.append({"板塊名稱": sector, "平均分": round(avg, 2), "氣候": weather})

    # --- A. [置頂] 市場晴雨表 ---
    st.header("🌍 1. 市場板塊晴雨表 (總覽)")
    st.table(pd.DataFrame(weather_summary))
    st.markdown("---")

    # --- B. [下方] 明細 ---
    st.header("🔍 2. 核心三濾網明細 (含現價與連跌修正)")
    for sector, df in all_results.items():
        st.subheader(f"📂 {sector}")
        # 視覺化顏色：紅色警示
        st.dataframe(df.style.applymap(lambda x: 'color: red; font-weight: bold' if '減碼' in str(x) else ('color: #00FF00' if '倉' in str(x) else ''), subset=['建議倉位']), use_container_width=True)
        st.markdown("---")
else:
    st.warning("💡 請點擊按鈕獲取最新數據報表。已包含 AAOI 連跌修正與晴雨表置頂。")



  



