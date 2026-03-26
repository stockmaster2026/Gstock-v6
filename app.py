
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 極簡精緻版 (數據對齊、刪除冗字) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.27")

st.markdown("""
    <style>
    .sector-title { font-size: 1.1rem; font-weight: bold; color: #44aaff; margin: 15px 0 8px 0; border-left: 5px solid #44aaff; padding-left: 10px; }
    
    .stock-card {
        border-radius: 8px; padding: 12px; margin-bottom: 10px;
        min-height: 280px; border: 1px solid rgba(0,0,0,0.1);
    }
    
    /* 顏色定義 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ccc !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-row { display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: bold; }
    .price-val { font-size: 1.4rem; font-weight: bold; text-align: center; margin: 5px 0; }
    
    .data-row { 
        font-size: 0.78rem; line-height: 1.4; margin: 5px 0; 
        border-top: 1px solid rgba(0,0,0,0.1); padding-top: 5px;
        font-family: sans-serif; text-align: left;
    }
    
    .history-array {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.05);
        padding: 6px; border-radius: 4px; font-size: 0.75rem; color: #007a00;
        white-space: nowrap; margin-top: 8px;
    }
    .advice-txt { text-align: center; font-size: 0.85rem; font-weight: bold; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心引擎 (原生高效抓取) ---
@st.cache_data(ttl=10)
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
            x2 = 10 if abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i] < 0.03 else (7 if abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i] < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            x1_h.append(str(int(x1))); x2_h.append(str(int(x2))); x3_h.append(str(int(x3))); awi_h.append(str(awi))

        curr_awi = float(awi_h[-1])
        if curr_awi >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒"
        elif curr_awi >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備蓄勢"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 蹲下蓄力"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊"

        return {"p": f"${c.iloc[-1]:.2f}", "chg": f"({((c.iloc[-1]/c.iloc[-2])-1)*100:+.2f}%)",
                "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else "🌫️",
                "x1": x1_h[-1], "x2": x2_h[-1], "x3": x3_h[-1],
                "h_awi": " | ".join(awi_h), "h_x2": " | ".join(x2_h), "bg": bg, "adv": adv}
    except: return None

# --- 2. 側邊欄 (修正連動) ---
with st.sidebar:
    st.header("📡 戰略中心")
    with st.form("scout_form"):
        user_input = st.text_input("輸入代碼 (用逗號隔開)")
        submitted = st.form_submit_button("執行偵察 🛰️")
    
    # 確保不管有沒有點按鈕，只要 input 有值就抓
    customs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

# --- 3. 板塊地圖 ---
sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"],
    "▋ 自選觀察清單": customs,
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW"],
    "▋ AI 醫療大數據": ["TEM", "PLTR", "SDGR"]
}

# --- 4. 渲染 ---
st.title("🛡️ 雙軌指揮中心 V32.9.27")
for sec, tkrs in sectors.items():
    valid_tkrs = [t for t in tkrs if t]
    if not valid_tkrs: continue
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(2) 
    for i, tkr in enumerate(valid_tkrs):
        with cols[i % 2]:
            d = fetch_analysis(tkr)
            if d:
                p_c = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
                st.markdown(f"""
                <div class="stock-card {d['bg']}">
                    <div class="ticker-row"><span>{tkr}</span><span>{d['weather']}</span></div>
                    <div style="font-size:0.8rem; font-weight:bold;">AWI: {d['awi']}</div>
                    <div class="price-val" style="color:{p_c};">{d['p']} <span style="font-size:0.9rem;">{d['chg']}</span></div>
                    <div class="data-row">
                        X1 (技術): {d['x1']} / 10 <br>
                        X2 (冠軍): {d['x2']} / 10 <br>
                        X3 (主力): {d['x3']} / 10
                    </div>
                    <div class="history-array">
                        AWI: {d['h_awi']}<br>
                        X2 : {d['h_x2']}
                    </div>
                    <div class="advice-txt">{d['adv']}</div>
                </div>
                """, unsafe_allow_html=True)

