import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 旗艦佈局 (復刻 11 板塊、寬版卡片) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.22")

st.markdown("""
    <style>
    .sector-title { 
        font-size: 1.6rem; font-weight: bold; color: #44aaff; 
        margin: 35px 0 15px 0; border-left: 10px solid #44aaff; padding-left: 15px;
    }
    
    /* 調整卡片寬度：不再細長，增加內距與寬度感 */
    .stock-card {
        border-radius: 12px; padding: 22px; margin-bottom: 20px;
        min-height: 400px; border: 1px solid rgba(0,0,0,0.1);
    }
    
    /* 戰場色標 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #f8f9fa !important; color: black !important; border: 1px solid #ddd !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-id { font-size: 1.7rem; font-weight: bold; }
    .price-display { font-size: 2.6rem; font-weight: bold; text-align: center; margin: 15px 0; }
    
    /* 五日歷史追溯 (綠色數據感) */
    .history-box {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.1);
        padding: 12px; border-radius: 6px; font-size: 0.95rem; line-height: 1.6; 
        margin-top: 15px; white-space: nowrap;
    }
    .history-box.light { background-color: rgba(0,0,0,0.05); color: #006400; }
    
    .f123-label { font-size: 0.9rem; line-height: 1.8; margin: 10px 0; }
    .advice-zone { text-align: center; font-size: 1.1rem; font-weight: bold; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心引擎 (V8.3 永久定錨) ---
@st.cache_data(ttl=600)
def fetch_v83_data(ticker):
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
        if curr_awi >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🌲 全力買入 (強烈共振)"
        elif curr_awi >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備敘勢 (分批佈局)"
        elif curr_awi >= 5: bg, adv = "bg-observe", "☁️ 潛伏偵測 (結構觀察)"
        else: bg, adv = "bg-retreat", "🟫 不利狀態 (撤退減碼)"

        return {"p": round(float(c.iloc[-1]), 2), "chg": round(((c.iloc[-1]/c.iloc[-2])-1)*100, 2),
                "awi": curr_awi, "weather": "☀️" if curr_awi >= 7 else "🌫️",
                "x1_v": x1_h[-1], "x2_v": x2_h[-1], "x3_v": x3_h[-1],
                "x1_h": " | ".join(x1_h), "x2_h": " | ".join(x2_h), "x3_h": " | ".join(x3_h), "awi_h": " | ".join(awi_h),
                "advice": adv, "bg": bg}
    except: return None

# --- 2. 側邊欄：戰略控制 ---
with st.sidebar:
    st.header("📡 戰略中心")
    user_input = st.text_input("新增自選代碼", "LUNR, IONQ, PI")
    customs = [t.strip().upper() for t in user_input.split(",") if t.strip()]

# --- 3. 11 板塊復位 ---
all_sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB", "KTOS"],
    "▋ AI 醫療與生物": ["TEM", "RXRX", "SDGR"],
    "▋ 自選觀察清單": customs,
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW", "AVGO", "LITE"],
    "▋ 半導體設備": ["NVDA", "ASML", "AMD", "TSM"],
    "▋ 數據中心/電力": ["VRT", "OKLO", "SMR"],
    "▋ 軟體/大數據": ["PLTR", "MSFT", "SNOW"],
    "▋ 特斯拉與電動車": ["TSLA", "RIVN"],
    "▋ 金融科技": ["SOFI", "HOOD", "PYPL"],
    "▋ 加密貨幣相關": ["MARA", "COIN", "MSTR"],
    "▋ 防禦/防衛系統": ["LMT", "GD", "NOC"]
}

# --- 4. 渲染 (每行 3 檔，讓卡片變寬) ---
st.title("🛡️ 雙軌指揮中心 V32.9.22")
for sec, tkrs in all_sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(3) # 每行改為 3 檔，卡片會變寬 25%，視覺比例更好
    for i, tkr in enumerate(tkrs):
        with cols[i % 3]:
            d = fetch_v83_data(tkr)
            if d:
                hist_s = "light" if "bg-observe" in d['bg'] else ""
                st.markdown(f"""
                <div class="stock-card {d['bg']}">
                    <div style="display:flex;justify-content:space-between;">
                        <span class="ticker-id">{tkr}</span><span style="font-size:1.8rem;">{d['weather']}</span>
                    </div>
                    <div style="font-weight:bold;">AWI 總分: {d['awi']}</div>
                    <div class="price-display">${d['p']} ({d['chg']}%)</div>
                    <div class="f123-label">
                        X1 (技術指標) [30%]: {d['x1_v']} / 10<br>
                        X2 (冠軍操盤手) [40%]: {d['x2_v']} / 10<br>
                        X3 (主力籌碼) [30%]: {d['x3_v']} / 10
                    </div>
                    <div class="history-box {hist_s}">
                        F1趨勢(h): {d['x1_h']}<br>F2構造(h): {d['x2_h']}<br>
                        F3能量(h): {d['x3_h']}<br>AWI陣列(h): {d['awi_h']}
                    </div>
                    <div class="advice-zone">{d['advice']}</div>
                </div>
                """, unsafe_allow_html=True)

