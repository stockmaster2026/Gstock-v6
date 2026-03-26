
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 戰場視覺系統 (嚴格修正標籤外露與換行問題) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.20")

st.markdown("""
    <style>
    .stock-card { 
        border-radius: 12px; padding: 20px; margin-bottom: 15px; 
        min-height: 450px; transition: 0.3s; color: white;
    }
    .bg-power-buy { background-color: #004d00 !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; } 
    .bg-observe { background-color: #f5f5f5 !important; color: black !important; border: 1px solid #ddd; } 
    .bg-retreat { background-color: #4e342e !important; } 

    .ticker-id { font-size: 1.6rem; font-weight: bold; margin-bottom: 5px; }
    .price-display { font-size: 2.4rem; font-weight: bold; text-align: center; margin: 15px 0; }
    
    .data-label { font-size: 0.82rem; line-height: 1.6; margin: 10px 0; }
    
    .history-box {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.2);
        padding: 12px; border-radius: 6px; font-size: 0.85rem; line-height: 1.5; 
        margin-top: 15px; white-space: nowrap;
    }
    .history-box.light { background-color: rgba(0,0,0,0.05); color: #006400; }
    
    .advice-zone { 
        text-align: center; font-size: 1rem; font-weight: bold; 
        margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 戰略邏輯引擎 (V8.3 永久定錨版) ---
@st.cache_data(ttl=600)
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
            x3 = 5 + (2 if c.iloc[i] > m20.iloc[i] else 0) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            x1_h.append(str(int(x1))); x2_h.append(str(int(x2))); x3_h.append(str(int(x3))); awi_h.append(str(awi))

        curr_awi = float(awi_h[-1])
        if curr_awi >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🌲 全力買入 (強烈共振)"
        elif curr_awi >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備敘勢 (分批佈局)"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 潛伏偵測 (結構觀察)"
        else: bg, adv = "bg-retreat", "🟫 不利狀態 (減碼撤退)"

        return {
            "p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
            "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else "🌫️",
            "x1_v": x1_h[-1], "x2_v": x2_h[-1], "x3_v": x3_h[-1],
            "x1_h": " | ".join(x1_h), "x2_h": " | ".join(x2_h), "x3_h": " | ".join(x3_h), "awi_h": " | ".join(awi_h),
            "advice": adv, "bg": bg
        }
    except: return None

# --- 2. 側邊欄與渲染 ---
st.sidebar.header("📡 指揮中心")
user_input = st.sidebar.text_input("輸入代碼", "LUNR, PI, IONQ")
tkrs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

st.title("🛡️ 雙軌指揮中心 V32.9.20")
cols = st.columns(4)
for i, tkr in enumerate(tkrs):
    with cols[i % 4]:
        d = fetch_analysis(tkr)
        if d:
            hist_style = "light" if "bg-observe" in d['bg'] else ""
            # 整合 HTML 輸出，避免標籤外露
            html_content = f"""
            <div class="stock-card {d['bg']}">
                <div class="ticker-id">{tkr} {d['weather']}</div>
                <div style="font-weight:bold; opacity:0.9;">AWI 總分: {d['awi']}</div>
                <div class="price-display">${d['p']} ({d['chg']}%)</div>
                <div class="data-label">
                    X1 (技術指標) [30%]: {d['x1_v']} / 10<br>
                    X2 (冠軍操盤手) [40%]: {d['x2_v']} / 10<br>
                    X3 (主力籌碼) [30%]: {d['x3_v']} / 10
                </div>
                <div class="history-box {hist_style}">
                    F1趨勢(h): {d['x1_h']}<br>
                    F2構造(h): {d['x2_h']}<br>
                    F3能量(h): {d['x3_h']}<br>
                    AWI陣列(h): {d['awi_h']}
                </div>
                <div class="advice-zone">{d['advice']}</div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
