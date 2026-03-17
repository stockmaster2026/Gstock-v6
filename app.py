import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# --- [ 1. 頁面配置 ] ---
st.set_page_config(page_title="核心三濾網：戰略實戰系統", layout="wide")

# --- [ 2. 完整監控板塊 ] ---
WATCH_LIST = {
    "太空板塊 (Space)": ["RKLB", "LUNR", "PL", "ASTS", "SPCE"],
    "光通訊板塊 (Optical)": ["LITE", "AAOI", "FN", "COHR", "AVGO"],
    "AI 醫療板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "數據存儲板塊": ["WDC", "STX", "MU", "PSTG"],
    "半導體核心": ["NVDA", "TSM", "AMD", "ARM", "ASML"],
    "大型科技與電動車": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
}

# 提取所有代號用於批次抓取
ALL_TICKERS = [ticker for sublist in WATCH_LIST.values() for ticker in sublist]

# --- [ 3. 核心階梯式邏輯 ] ---
def get_strategy_logic(f1, f2, f3, total, chg_pct, is_dropping):
    if f1 >= 85 and f2 >= 80 and f3 >= 80 and not is_dropping and chg_pct > -1:
        return "🔥 滿倉 (100%)", "多頭共振，最強狀態"
    elif f1 >= 80 and f2 >= 70 and not is_dropping:
        return "✅ 重倉 (50%)", "趨勢穩定，動能尚可"
    elif f1 >= 75 and f2 >= 55 and not is_dropping:
        return "🧐 試單 (20%)", "初步轉強，建立觀察倉"
    elif is_dropping or f2 < 55 or chg_pct < -2:
        return "⚠️ 減碼 (-30%)", "動能背離/連跌，執行階梯保護"
    elif f1 < 60:
        return "🚨 強力減碼 (-70%)", "趨勢嚴重破位，強制撤退"
    else:
        return "❌ 觀望 (0%)", "等待趨勢對齊"

# --- [ 4. 介面渲染 ] ---
st.title("🛡️ 核心三濾網：戰略儀表板 (數據穩定版)")
st.markdown("---")

# 側邊欄查詢 (單獨抓取)
with st.sidebar:
    st.header("🎯 個股快速診斷")
    t_input = st.text_input("輸入代號 (如: AAOI):").upper().strip()
    if t_input:
        data = yf.download(t_input, period="1y", interval="1d", progress=False)
        if not data.empty:
            close = data['Close'].iloc[-1].item()
            st.metric(f"{t_input} 現價", f"{close:.2f}")

# 執行按鈕
if st.button("🔄 啟動全市場數據掃描 (批次抓取)"):
    with st.spinner('正在同步全球市場真實數據...'):
        # 關鍵修正：一次性下載所有代號，避免被封鎖
        raw_data = yf.download(ALL_TICKERS, period="1y", interval="1d", progress=False, group_by='ticker')
        
        weather_summary = []
        all_sector_tables = {}

        for sector, tickers in WATCH_LIST.items():
            sector_res = []
            sector_scores = []
            
            for t in tickers:
                try:
                    # 提取單檔數據
                    df = raw_data[t].dropna()
                    if df.empty or len(df) < 50:
                        sector_res.append({"代碼": t, "現價": "數據缺失", "建議倉位": "N/A"})
                        continue
                    
                    close = df['Close'].iloc[-1].item()
                    prev_close = df['Close'].iloc[-2].item()
                    chg_pct = ((close - prev_close) / prev_close) * 100
                    
                    ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
                    ma50 = df['Close'].rolling(50).mean().iloc[-1].item()
                    
                    # AAOI 專屬連跌邏輯
                    last_4 = df['Close'].iloc[-4:].tolist()
                    is_dropping = all(last_4[i] > last_4[i+1] for i in range(len(last_4)-1))
                    
                    f1 = 100 if close > ma20 > ma50 else 80 if close > ma20 else 65 if close > ma50 else 40
                    if is_dropping: f1 -= 30
                    
                    # F2: RSI
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rsi = 100 - (100 / (1 + (gain / loss).iloc[-1].item()))
                    f2 = int(rsi)
                    
                    # F3: 量能
                    v_now = df['Volume'].iloc[-1].item()
                    v_avg = df['Volume'].rolling(20).mean().iloc[-1].item()
                    f3 = min(int((v_now / v_avg) * 100), 100)
                    
                    total = round((f1 * 0.4 + f2 * 0.3 + f3 * 0.3), 2)
                    pos, adv = get_strategy_logic(f1, f2, f3, total, chg_pct, is_dropping)
                    
                    sector_res.append({
                        "代碼": t, "現價": round(close, 2), "漲跌%": f"{chg_pct:.2f}%",
                        "趨勢(F1)": f1, "動能(F2)": f2, "總分": total, 
                        "建議倉位": pos, "策略動作": adv
                    })
                    sector_scores.append(total)
                except:
                    sector_res.append({"代碼": t, "現價": "錯誤", "建議倉位": "N/A"})

            all_sector_tables[sector] = pd.DataFrame(sector_res)
            avg_s = np.mean(sector_scores) if sector_scores else 0
            weather = "☀️ 晴" if avg_s > 75 else "🌤️ 雲" if avg_s > 60 else "🌧️ 雨"
            weather_summary.append({"板塊": sector, "平均分": round(avg_s, 2), "氣候": weather})

        # --- A. 【置頂】顯示晴雨表 ---
        st.header("🌍 1. 市場板塊晴雨表 (總覽)")
        st.table(pd.DataFrame(weather_summary))
        st.markdown("---")

        # --- B. 【下方】顯示明細 ---
        st.header("🔍 2. 核心三濾網明細 (含現價與連跌修正)")
        for sector, df in all_sector_tables.items():
            st.subheader(f"📂 {sector}")
            st.dataframe(df.style.applymap(lambda x: 'color: red; font-weight: bold' if '減碼' in str(x) else ('color: #00FF00' if '倉' in str(x) else ''), subset=['建議倉位']), use_container_width=True)
            st.markdown("---")
else:
    st.info("💡 點擊按鈕啟動【批次數據抓取】，修正 0 數據問題。AAOI 已加入連跌修正，晴雨表置頂。")


  



