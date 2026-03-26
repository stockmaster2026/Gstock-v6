
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 精緻縮小版 (2 欄位、文字不換行、縮小字體) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.25")

st.markdown("""
    <style>
    .sector-title { font-size: 1.3rem; font-weight: bold; color: #44aaff; margin: 25px 0 10px 0; border-left: 8px solid #44aaff; padding-left: 15px; }
    
    .stock-card {
        border-radius: 10px; padding: 15px; margin-bottom: 15px;
        min-height: 380px; border: 1px solid rgba(0,0,0,0.1);
        background-color: transparent;
    }
    
    /* 戰場色標 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ddd !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    /* 縮小後的字體 */
    .ticker-id { font-size: 1.4rem; font-weight: bold; }
    .price-display { font-size: 1.8rem; font-weight: bold; text-align: center; margin: 8px 0; }
    .history-box {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.05);
        padding: 8px; border-radius: 6px; font-size: 0.85rem; line-height: 1.4; color: #007a00;
        white-space: nowrap;
    }
    .f123-label { font-size: 0.82rem; line-height: 1.5; margin: 8px 0; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 8px; }
    .advice-zone { text-align: center; font-size: 1rem; font-weight: bold; margin-top: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心引擎 (V8.3 永久定錨) ---
@st.cache_data(ttl=60)
def fetch_analysis(ticker):
    if not ticker: return None
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
        elif curr_awi >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備敘勢：佈局中"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 蹲下蓄力：再等一下"
        else: bg, adv = "bg-retreat", "🟫 危險訊號：撤退！"

        return {"p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
                "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else "🌫️",
                "x1_v": x1_h[-1], "x2_v": x2_h[-1], "x3_v": x3_h[-1],
                "x1_h": " | ".join(x1_h), "x2_h": " | ".join(x2_h), "x3_h": " | ".join(x3_h), "awi_h": " | ".join(awi_h),
                "advice": adv, "bg": bg}
    except: return None

# --- 2. 側邊欄與輸入邏輯 ---
with st.sidebar:
    st.header("📡 戰略控制")
    # 這裡加入 on_change 確保按下 Enter 後會立即刷新
    user_input = st.text_input("新增自選代碼 (Enter 確認)", key="ticker_input")
    customs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

# --- 3. 板塊地圖復位 ---
all_sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"],
    "▋ 自選觀察清單": customs,
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW"],
    "▋ AI 醫療與大數據": ["TEM", "PLTR", "SDGR"]
}

# --- 4. 渲染 (2 欄位，精緻縮小比例) ---
st.title("🛡️ 雙軌指揮中心 V32.9.25")
for sec, tkrs in all_sectors.items():
    if not any(tkrs): continue
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
                        <span class="ticker-id">{tkr}</span><span style="font-size:1.5rem;">{d['weather']}</span>
                    </div>
                    <div style="font-size:0.9rem; font-weight:bold; opacity:0.8;">AWI 戰力值: {d['awi']}</div>
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
