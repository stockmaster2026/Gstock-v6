
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🛡️ 三維戰略系統 V6.6", layout="wide")
st.markdown("<h1 style='text-align: center; color: #007AFF;'>🛡️ 三維戰略系統 V6.6</h1>", unsafe_allow_html=True)

# 1. 戰略參謀邏輯：判斷階段與加減碼
def analyze_strategy(df):
    close = df['Close']
    ma20 = close.rolling(window=20).mean()
    ma5 = close.rolling(window=5).mean()
    
    current_price = float(close.iloc[-1])
    last_ma20 = float(ma20.iloc[-1])
    last_ma5 = float(ma5.iloc[-1])
    prev_ma20 = float(ma20.iloc[-2])
    
    # 判斷趨勢與階段
    if current_price > last_ma20 and last_ma20 > prev_ma20:
        if current_price > last_ma5:
            stage = "🚀 主升段：火力全開"
            action = "🔥 加碼進攻：建議倉位 80-100%"
        else:
            stage = "📈 高位震盪：準備進入噴射或拉回"
            action = "💎 持股待變：不加碼，守住利潤"
    elif current_price < last_ma20:
        if last_ma20 < prev_ma20:
            stage = "📉 走跌段：空方佔優"
            action = "🏃 撤退避險：建議減碼至 10-20% 或空倉"
        else:
            stage = "⚠️ 警訊：剛跌破防守線"
            action = "⚠️ 開始減碼：先出清 50%"
    else:
        stage = "🔍 築底/盤整段：偵查期"
        action = "🛶 小量試單：20-30% 倉位"
    
    return stage, action

# 2. 監控名單
t_list = st.sidebar.text_input("📝 監控代號 (逗號隔開):", "TSM, NVDA, AAPL, POET")
tickers = [x.strip().upper() for x in t_list.split(',')]

# 3. 戰場實況看板
if st.sidebar.button("📡 發動戰略掃描"):
    for t in tickers:
        try:
            df = yf.download(t, period="100d", interval="1d")
            if not df.empty:
                stage, action = analyze_strategy(df)
                
                with st.expander(f"🚩 戰報：{t} - {stage}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("當前價格", f"${float(df['Close'].iloc[-1]):.2f}")
                    c2.subheader("🎯 戰略行動")
                    c2.info(action)
                    c3.subheader("📊 走勢簡圖")
                    c3.line_chart(df['Close'].tail(20))
        except:
            st.error(f"無法偵測 {t} 指令")


