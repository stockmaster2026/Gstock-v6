
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 精確排版 (強制不換行、復刻截圖佈局) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.13")

st.markdown("""
    <style>
    /* 基礎字體與背景歸零 */
    html, body, [data-testid="stAppViewContainer"] { font-family: sans-serif; }
    
    .sector-title { 
        font-size: 1.4rem; font-weight: bold; color: #44aaff; 
        margin: 20px 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid #44aaff;
    }
    
    /* 每個股票框框的精確容器 */
    .stock-card {
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
        min-height: 240px; /* 固定高度確保對齊 */
        background-color: transparent;
    }
    
    /* 頂部：Ticker 與 天氣 */
    .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .ticker-id { font-size: 1.3rem; font-weight: bold; white-space: nowrap; }
    .weather-icon { font-size: 1.4rem; }
    
    /* AWI 分數標籤 */
    .awi-tag { font-size: 0.95rem; font-weight: bold; color: #b8860b; margin-bottom: 8px; }
    
    /* 價格大字：強制居中且不換行 */
    .price-display { 
        font-size: 2.2rem; font-weight: bold; text-align: center; 
        margin: 10px 0; white-space: nowrap; 
    }
    
    /* F123 與 歷史陣列：核心是不換行 */
    .data-text { 
        font-size: 0.82rem; color: #555; 
        margin-bottom: 4px; white-space: nowrap; overflow: hidden;
    }
    
    .history-box {
        font-family: 'Courier New', monospace;
        background-color: rgba(0,0,0,0.03);
        padding: 8px;
        border-radius: 4px;
        color: #007a00; /* 經典數據綠 */
        font-size: 0.88rem;
        line-height: 1.4;
        white-space: nowrap; /* 強制 V26(h) 與 AWI(h) 不換行 */
        overflow: hidden;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 數據抓取 (原生高效爬蟲) ---
@st.cache_data(ttl=600)
def get_analysis(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers).json()
        res = resp['chart']['result'][0]
        c = pd.Series(res['indicators']['quote'][0]['close']).ffill()
        v = pd.Series(res['indicators']['quote'][0]['volume']).ffill()
        o = pd.Series(res['indicators']['quote'][0]['open']).ffill()

        m10, m20 = c.rolling(10).mean(), c.rolling(20).mean()
        dist = abs(m10.iloc[-1] - m20.iloc[-1]) / m20.iloc[-1]
        x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
        e12, e26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
        macd = e12 - e26
        x1 = 10 if macd.iloc[-1] > 0 else (6 if macd.iloc[-1] > macd.iloc[-2] else 0)
        v_avg = v.rolling(10).mean().iloc[-1]
        x3 = 10 if v.iloc[-1] > v_avg * 1.3 and c.iloc[-1] > o.iloc[-1] else 5
        
        awi = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
        weather = "☀️" if awi >= 7 else ("☁️" if awi >= 5 else "🌫️")
        icons = ("⚓" if x2==10 else "") + ("🔥" if x3==10 else "")
        return {"p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
                "awi": awi, "x1": x1, "x2": x2, "x3": x3, "weather": weather, "icons": icons}
    except: return None

# --- 2. 側邊欄 ---
st.sidebar.header("📡 戰略控制")
user_input = st.sidebar.text_input("輸入自選代碼", "LUNR, IONQ, PI")
customs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

# --- 3. 渲染板塊 (確保每行 4 檔以對應 iPad 寬度) ---
sectors = {"太空技術": ["LUNR", "PL", "ASTS", "RKLB"], "自選追蹤": customs}

st.title("🛡️ 雙軌指揮中心 V32.9.13")

for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(4) # 強制四列佈局
    for i, tkr in enumerate(tkrs):
        with cols[i % 4]:
            d = get_analysis(tkr)
            if d:
                p_color = "#ff4b4b" if d['chg'] >= 0 else "#00ff00"
                st.markdown(f"""
                <div class="stock-card">
                    <div class="card-top">
                        <div class="ticker-id">{tkr} {d['icons']}</div>
                        <div class="weather-icon">{d['weather']}</div>
                    </div>
                    <div class="awi-tag">AWI 分數: {d['awi']}</div>
                    <div class="price-display" style="color:{p_color};">${d['p']}</div>
                    <div class="data-text">X1趨勢: {d['x1']} | X2構造: {d['x2']} | X3能量: {d['x3']}</div>
                    <div class="history-box">
                        V26(h): {d['x2']} | {d['x2']} | {d['x2']} | {d['x2']}<br>
                        AWI(h): {d['awi']} | {d['awi']} | {d['awi']} | {d['awi']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
