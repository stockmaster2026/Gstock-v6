
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 旗艦大寬版 (2 欄位、白話指令) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.24")

st.markdown("""
    <style>
    .sector-title { 
        font-size: 1.8rem; font-weight: bold; color: #44aaff; 
        margin: 40px 0 15px 0; border-left: 12px solid #44aaff; padding-left: 20px;
    }
    .stock-card {
        border-radius: 15px; padding: 25px; margin-bottom: 25px;
        min-height: 420px; border: 1px solid rgba(0,0,0,0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    /* 戰場色標 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 2px solid #ddd !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-id { font-size: 2rem; font-weight: bold; }
    .price-display { font-size: 3rem; font-weight: bold; text-align: center; margin: 15px 0; }
    .history-box {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.05);
        padding: 15px; border-radius: 8px; font-size: 1.1rem; line-height: 1.6; color: #007a00;
    }
    .f123-label { font-size: 1.1rem; line-height: 2; margin: 15px 0; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 10px; }
    .advice-zone { text-align: center; font-size: 1.4rem; font-weight: bold; margin-top: 20px; text-decoration: underline; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心引擎 (V8.3 永久定錨) ---
@st.cache_data(ttl=60) # 縮短緩存時間讓輸入更即時
def fetch_analysis(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=60d&interval=1d"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()['chart']['result'][0]
        c = pd.Series(res['indicators']['quote'][0]['close']).ffill()
        v = pd.Series(res['indicators']['quote'][0]['volume']).ffill()
        o = pd.Series(res['indicators']['quote'][0]['open']).ffill()

        m10, m20 = c.rolling(10).mean(), c.rolling(20).mean()
        e12, e26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
        macd = e12 - e26
        delta = c.diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))

        x1_h, x2_h, x3_h, awi_h = [], [], [], []
        for i in range(-5, 0):
            x1 = (5 if macd.iloc[i] > 0 else 0) + (5 if rsi.iloc[i] > 50 else 0)
            dist = abs(m10.iloc[i] - m20.iloc[i]) / m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            x1_h.append(str(int(x1))); x2_h.append(str(int(x2))); x3_h.append(str(int(x3))); awi_h.append(str(awi))

        curr_awi = float(awi_h[-1])
        if curr_awi >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒：全力買入！"
        elif curr_awi >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備敘勢：分批撿便宜"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 蹲下蓄力：主力買進，再等等"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊：危險訊號！"

        return {"p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
                "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else "🌫️",
                "x1_v": x1_h[-1], "x2_v": x2_h[-1], "x3_v": x3_h[-1],
                "x1_h": " | ".join(x1_h), "x2_h": " | ".join(x2_h), "x3_h": " | ".join(x3_h), "awi_h": " | ".join(awi_h),
                "advice": adv, "bg": bg}
    except: return None

# --- 2. 側邊欄：修正輸入框連結 ---
with st.sidebar:
    st.header("📡 戰略控制")
    # 這裡的 key="custom_input" 確保了輸入內容能被正確捕捉
    user_input = st.text_input("新增自選代碼 (如: KTOS, TSLA)", key="custom_input")
    customs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

# --- 3. 11 板塊復位 ---
all_sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"],
    "▋ 自選觀察清單": customs, # 妳輸入的代碼會出現在這裡
    "▋ AI 醫療與生物": ["TEM", "RXRX", "SDGR"],
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW"],
    "▋ 加密貨幣相關": ["MARA", "COIN", "MSTR"]
}

# --- 4. 渲染 (每行 2 檔) ---
st.title("🛡️ 雙軌指揮中心 V32.9.24")
for sec, tkrs in all_sectors.items():
    if not tkrs: continue # 如果該板塊沒代碼就跳過
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(2) 
    for i, tkr in enumerate(tkrs):
        with cols[i % 2]:
            d = fetch_analysis(tkr)
            if d:
                p_c = "#ff4b4b" if d['chg'] >= 0 else "#00ff00"
                st.markdown(f"""
                <div class="stock-card {d['bg']}">
                    <div style="display:flex;justify-content:space-between;">
                        <span class="ticker-id">{tkr}</span><span style="font-size:2rem;">{d['weather']}</span>
                    </div>
                    <div style="font-size:1.2rem; font-weight:bold;">AWI 戰力值: {d['awi']}</div>
                    <div class="price-display" style="color:{p_c};">${d['p']} ({d['chg']}%)</div>
                    <div class="f123-label">
                        X1 (技術指標) [30%]: {d['x1_v']} / 10 <br>
                        X2 (冠軍操盤手) [40%]: {d['x2_v']} / 10 <br>
                        X3 (主力籌碼) [30%]: {d['x3_v']} / 10
                    </div>
                    <div class="history-box">
                        五日 AWI 陣列: {d['awi_h']}<br>
                        五日 構造(X2)陣列: {d['x2_h']}
                    </div>
                    <div class="advice-zone">{d['advice']}</div>
                </div>
                """, unsafe_allow_html=True)
