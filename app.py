
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="三維戰略 V6.6", layout="wide")
st.markdown("<h1 style='text-align: center; color: #007AFF;'>🛡️ 三維戰略系統 V6.6</h1>", unsafe_allow_html=True)

# 監控名單輸入
t_list = st.text_input("📝 請輸入監控代號 (用逗號隔開):", "TSM, NVDA, AAPL")
tickers = [x.strip().upper() for x in t_list.split(',')]

if st.button("🚀 開始分析戰略"):
    for t in tickers:
        try:
            data = yf.download(t, period="60d", interval="1d")
            if not data.empty:
                # 手動計算簡單指標 (取代 pandas_ta)
                close = data['Close']
                st.subheader(f"📊 {t} 戰報")
                col1, col2 = st.columns(2)
                col1.metric("當前價格", f"${float(close.iloc[-1]):.2f}")
                col2.write(data.tail(5))
        except:
            st.error(f"無法抓取 {t} 資料")


