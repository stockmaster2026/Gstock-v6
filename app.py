import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 戰場視覺系統 (嚴格對齊 10:47 AM 截圖與顏色定義) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.19")

st.markdown("""
    <style>
    /* 基礎排版：確保 iPad 橫屏不亂跑 */
    .sector-title { font-size: 1.5rem; font-weight: bold; color: #44aaff; margin: 20px 0; border-bottom: 2px solid #44aaff; }
    
    .stock-card { 
        border-radius: 12px; padding: 20px; margin-bottom: 15px; 
        min-height: 420px; transition: 0.3s; 
    }
    
    /* 戰場色標：根據 AWI 與 趨勢自動切換 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } /* 深綠 */
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } /* 淺綠 */
    .bg-observe { background-color: #f5f5f5 !important; color: black !important; border: 1px solid #ddd; } /* 灰白 */
    .bg-retreat { background-color: #4e342e !important; color: white !important; } /* 咖啡 */

    .ticker-header { display: flex; justify-content: space-between; align-items: flex-start; }
    .ticker-id { font-size: 1.6rem; font-weight: bold; }
    .price-display { font-size: 2.6rem; font-weight: bold; text-align: center; margin: 15px 0; white-space: nowrap; }
    
    /* 核心數據顯示 */
    .f123-label { font-size: 0.85rem; line-height: 1.8; margin-bottom: 10px; }
    
    /* 五日追溯陣列 (綠色等寬數據感) */
    .history-box {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.15);
        padding: 12px; border-radius: 6px; font-size: 0.9rem; line-height: 1.5; 
        margin-top: 10px; white-space: nowrap; overflow: hidden;
    }
    .history-box.light { background-color: rgba(255,255,255,0.4); color: #004d00; }
    
    .advice-zone { 
        text-align: center; font-size: 1.1rem; font-weight: bold; 
        margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 戰略邏輯引擎 (V8.3 永久定錨版) ---
@st.cache_data(ttl=600)
def fetch_v83_analysis(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=60d&interval=1d"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()['chart']['result'][0]
        c = pd.Series(res['indicators']['quote'][0]['close']).ffill()
        v = pd.Series(res['indicators']['quote'][0]['volume']).ffill()
        o = pd.Series(res['indicators']['quote'][0]['open']).ffill()

        # 指標預計算
        m10, m20 = c.rolling(10).mean(), c.rolling(20).mean()
        e12, e26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
        macd = e12 - e26
        delta = c.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))

        # 追溯 5 日數據
        x1_h, x2_h, x3_h, awi_h = [], [], [], []
        for i in range(-5, 0):
            # X1 (技術指標) [30%]: MACD>0 + RSI>50 共振
            x1 = 0
            if macd.iloc[i] > 0: x1 += 5
            if rsi.iloc[i] > 50: x1 += 5
            # X2 (冠軍操盤手) [40%]: 均線糾結 < 3%
            dist = abs(m10.iloc[i] - m20.iloc[i]) / m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            # X3 (主力籌碼) [30%]: 站穩 MA20 + 點火能量
            x3 = 5
            if c.iloc[i] > m20.iloc[i]: x3 += 2
            if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3: x3 += 3
            
            awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            x1_h.append(str(int(x1))); x2_h.append(str(int(x2))); x3_h.append(str(int(x3))); awi_h.append(str(awi))

        curr_awi = float(awi_h[-1])
        is_on_zero = macd.iloc[-1] > 0
        
        # 顏色戰術判定
        if curr_awi >= 9 and is_on_zero: bg, adv = "bg-power-buy", "🌲 全力買入 (強烈共振)"
        elif curr_awi >= 7 and is_on_zero: bg, adv = "bg-accumulate", "🌿 準備敘勢 (分批佈局)"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 潛伏偵測 (結構觀察)"
        else: bg, adv = "bg-retreat", "🟫 不利狀態 (撤退減碼)"

        return {
            "p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
            "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else ("🌫️" if curr_awi < 5 else "☁️"),
            "x1_v": x1_h[-1], "x2_v": x2_h[-1], "x3_v": x3_h[-1],
            "x1_h": " | ".join(x1_h), "x2_h": " | ".join(x2_h), "x3_h": " | ".join(x3_h), "awi_h": " | ".join(awi_h),
            "advice": adv, "bg": bg
        }
    except: return None

# --- 2. 側邊欄與排版佈局 ---
st.sidebar.header("📡 指揮中心")
user_input = st.sidebar.text_input("輸入代碼 (LUNR, PI, IONQ)", "LUNR, PI, IONQ")
tkrs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

st.title("🛡️ 雙軌指揮中心 V32.9.19")
cols = st.columns(4) # iPad 橫屏最佳四欄位

for i, tkr in enumerate(tkrs):
    with cols[i % 4]:
        d = fetch_v83_analysis(tkr)
        if d:
            hist_style = "light" if "bg-observe" in d['bg'] else ""
            st.markdown(f"""
            <div class="stock-card {d['bg']}">
                <div class="ticker-header">
                    <span class="ticker-id">{tkr}</span>
                    <span style="font-size:1.5rem;">{d['weather']}</span>
                </div>
                <div style="font-weight:bold; opacity:0.9;">AWI 總分: {d['awi']} / 10</div>
                <div class="price-display">${d['p']} ({d['chg']}%)</div>
                
                <div class="f123-label">
                    X1 (技術指標) [30%]: {d['x1_v']} / 10<br>
                    X2 (冠軍操盤手) [40%]: {d['x2_v']} / 10<br>
                    X3 (主力籌碼) [30%]: {d['x3_v']} / 10
                </div>
                
                <div class="history-box {hist_style}">
                    F1趨勢(h): {d['x1_h']}<br>F2構造(h): {d['x2_h']}<br>
                    F3能量(h): {d['x3_h']}<br>AWI陣列(h): {d['awi_h']}
                </div>
                <div class="advice-zone">{d['advice']}</div>
            </div>
            """, unsafe_allow_html=True)

