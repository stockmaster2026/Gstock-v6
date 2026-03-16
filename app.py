import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🛡️ 三維戰略 V6.6", layout="wide")

# 加強版 CSS：讓股票名字像招牌一樣大，並區分色塊
st.markdown("""
    <style>
    .big-font { font-size: 60px !important; font-weight: bold; color: #FFD700; text-align: center; background: #1E1E1E; border-radius: 10px; margin-bottom: 0px; }
    .status-box { padding: 15px; border-radius: 10px; color: white; text-align: center; font-size: 20px; }
    .bull { background-color: #007A33; }
    .bear { background-color: #A50021; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 三維戰略旗艦指揮所 V6.6")

# 1. 預設板塊設定 (長官可以隨時在這邊增加代號)
sectors = {
    "🍎 科技權值": ["TSM", "NVDA", "AAPL", "MSFT"],
    "🚀 戰略黑馬": ["POET", "SOXL", "TQQQ"],
    "🧪 其他追蹤": []
}

# 2. 側邊欄：手動輸入區
st.sidebar.header("🕹️ 指揮控制")
user_input = st.sidebar.text_input("輸入新代號 (用逗號隔開):", "")
if user_input:
    custom_tickers = [x.strip().upper() for x in user_input.split(',')]
    sectors["🧪 其他追蹤"] = custom_tickers

# 3. 戰略判斷引擎
def get_analysis(t):
    try:
        df = yf.download(t, period="40d", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        c = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        change = ((c - float(df['Close'].iloc[-2])) / float(df['Close'].iloc[-2])) * 100
        return {"price": c, "ma20": ma20, "change": change, "is_bull": c > ma20}
    except: return None

# 4. 戰場分頁顯示
if st.sidebar.button("📡 啟動全域掃描"):
    for sector_name, tickers in sectors.items():
        if not tickers: continue
        st.subheader(f"📍 分類板塊：{sector_name}")
        cols = st.columns(len(tickers))
        
        for i, t in enumerate(tickers):
            res = get_analysis(t)
            with cols[i]:
                if res:
                    st.markdown(f"<div class='big-font'>{t}</div>", unsafe_allow_html=True)
                    style = "bull" if res['is_bull'] else "bear"
                    action = "🔥 加碼" if res['is_bull'] else "🏃 撤退"
                    st.markdown(f"<div class='status-box {style}'><b>{action}</b><br>${res['price']:.2f} ({res['change']:.2f}%)</div>", unsafe_allow_html=True)
                else:
                    st.warning(f"{t} 無訊號")
