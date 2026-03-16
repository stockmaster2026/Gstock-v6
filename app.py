import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🛡️ 三維戰略 V6.6", layout="wide")

# 自定義 CSS：放大股票名稱與美化介面
st.markdown("""
    <style>
    .stock-header { font-size: 50px !important; font-weight: bold; color: #FFD700; background-color: #1E1E1E; padding: 10px; border-radius: 10px; text-align: center; }
    .action-box { font-size: 24px; padding: 20px; border-radius: 15px; margin: 10px 0px; }
    .bull-zone { background-color: #004d40; border-left: 10px solid #00c853; }
    .bear-zone { background-color: #4a148c; border-left: 10px solid #e91e63; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 三維戰略指揮中心 V6.6")

# 1. 模擬 AI 板塊掃描 (熱門板塊偵測)
st.sidebar.header("🤖 AI 板塊氣象儀")
hot_sectors = {"半導體": "🔥 沸騰", "人工智慧": "🌡️ 高溫", "電力能源": "☁️ 轉涼", "生技醫療": "❄️ 冰封"}
for sector, status in hot_sectors.items():
    st.sidebar.write(f"{sector}：{status}")

# 2. 監控輸入
t_list = st.sidebar.text_input("📝 輸入戰略代號:", "TSM, NVDA, AAPL, POET")
tickers = [x.strip().upper() for x in t_list.split(',')]

# 3. 戰略判斷大腦
def get_strategy(t):
    df = yf.download(t, period="60d", interval="1d")
    if df.empty: return None
    close = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    change = ((close - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    
    if close > ma20:
        return {"status": "多頭", "stage": "🚀 主升段", "action": "🔥 強力加碼 (倉位 80%+)", "price": close, "change": change}
    else:
        return {"status": "空頭", "stage": "📉 走跌段", "action": "🏃 立即減碼 (倉位 <10%)", "price": close, "change": change}

# 4. 戰場分類顯示
if st.sidebar.button("📡 發動全域掃描"):
    bulls, bears = [], []
    for t in tickers:
        res = get_strategy(t)
        if res:
            res['ticker'] = t
            bulls.append(res) if res['status'] == "多頭" else bears.append(res)

    col_bull, col_bear = st.columns(2)
    
    with col_bull:
        st.header("🔥 強勢進攻區 (做多)")
        for item in bulls:
            st.markdown(f"<div class='stock-header'>{item['ticker']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='action-box bull-zone'><b>階段：</b>{item['stage']}<br><b>行動：</b>{item['action']}<br><b>價格：</b>${item['price']:.2f} ({item['change']:.2f}%)</div>", unsafe_allow_html=True)

    with col_bear:
        st.header("💀 弱勢避險區 (空頭)")
        for item in bears:
            st.markdown(f"<div class='stock-header'>{item['ticker']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='action-box bear-zone'><b>階段：</b>{item['stage']}<br><b>行動：</b>{item['action']}<br><b>價格：</b>${item['price']:.2f} ({item['change']:.2f}%)</div>", unsafe_allow_html=True)



