
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="🛡️ 三維戰略 V7.6", layout="wide")

# CSS 強化
st.markdown("""
    <style>
    .stock-id { font-size: 50px !important; font-weight: bold; color: #FFD700; margin-bottom: -5px; }
    .filter-text { font-size: 16px; color: #CCCCCC; margin-bottom: 2px; line-height: 1.2; }
    .status-badge { padding: 8px; border-radius: 8px; font-size: 18px; font-weight: bold; margin: 10px 0px; text-align: center; }
    .action-buy { background-color: #007A33; color: white; border: 2px solid #00FF00; }
    .action-sell { background-color: #A50021; color: white; border: 2px solid #FF3333; }
    </style>
    """, unsafe_allow_html=True)

# 1. 核心板塊配置
SECTORS = {
    "核心算力 (AI Core)": ["NVDA", "AVGO", "AMD", "ARM"],
    "矽光子 (Optical)": ["POET", "LUKE", "ALTR", "MARV"],
    "量子計算 (Quantum)": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "AI 醫療 (Bio-Tech)": ["HIMS", "RXRA", "GEHC"],
    "太空探索 (Space)": ["RKLB", "LUNR", "PLTR"]
}

# 2. 三維過濾器邏輯
def get_analysis_3d(t):
    try:
        df = yf.download(t, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        
        c = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        ma5 = float(df['Close'].rolling(5).mean().iloc[-1])
        prev_ma20 = float(df['Close'].rolling(20).mean().iloc[-2])
        
        # 三維 Filter 判斷
        f1 = "✅ 站上生命線" if c > ma20 else "❌ 跌破生命線"
        f2 = "✅ 短線動能強" if c > ma5 else "❌ 短線動能弱"
        f3 = "✅ 趨勢向上" if ma20 > prev_ma20 else "❌ 趨勢下彎"
        
        # 最終行動
        is_bull = (c > ma20) and (ma20 > prev_ma20)
        return {"price": c, "is_bull": is_bull, "filters": [f1, f2, f3], "change": ((c-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100}
    except: return None

# 3. 側邊欄：Input 偵察按鈕
with st.sidebar:
    st.header("🕹️ 指揮控制")
    # 這就是您要的 Input 框
    user_input = st.text_input("📡 輸入新偵察代號 (用逗號隔開):", "")
    if user_input:
        new_list = [x.strip().upper() for x in user_input.split(',')]
        SECTORS["🔍 臨時偵察戰區 (Input)"] = new_list
    
    st.divider()
    st.write("當前戰略模式：三維過濾器 V7.6")

# 主畫面
st.title("🛡️ 三維戰略指揮中心 V7.6")

# 4. 戰場全景顯示
for s_name, t_list in SECTORS.items():
    with st.expander(f"📍 戰場詳情：{s_name}", expanded=True):
        # 確保每行 4 檔，整齊排隊
        cols = st.columns(4)
        for i, t in enumerate(t_list):
            res = get_analysis_3d(t)
            with cols[i % 4]:
                if res:
                    st.markdown(f"<div class='stock-id'>{t}</div>", unsafe_allow_html=True)
                    
                    # 顯示三個 Filter
                    for f in res['filters']:
                        st.markdown(f"<div class='filter-text'>{f}</div>", unsafe_allow_html=True)
                    
                    if res['is_bull']:
                        st.markdown("<div class='status-badge action-buy'>🚀 主升階段<br>🔥 加碼進攻</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='status-badge action-sell'>📉 走跌階段<br>🏃 全力撤退</div>", unsafe_allow_html=True)
                    
                    st.write(f"**價格:** ${res['price']:.2f} ({res['change']:+.2f}%)")
                else:
                    st.error(f"無法讀取 {t}")

  



