
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 視覺強化 (加粗、密集對齊、點零對齊) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.38")

st.markdown("""
    <style>
    .sector-title { font-size: 1.1rem; font-weight: bold; color: #44aaff; margin: 20px 0 10px 0; border-left: 6px solid #44aaff; padding-left: 10px; }
    .sidebar-card, .main-card { border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); color: #ffffff; }
    .main-card { color: #333; min-height: 250px; }

    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ccc !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-row { display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 900; }
    .price-val { font-size: 1.25rem; font-weight: 900; text-align: center; margin: 4px 0; }
    
    /* X123 密集加粗 */
    .data-row { 
        font-size: 0.85rem; font-weight: 900; line-height: 1.4; margin-top: 5px; 
        border-top: 1px solid rgba(128,128,128,0.4); padding-top: 5px;
    }
    
    /* PS 與 SBUY 陣列：強制定標對齊 */
    .num-align {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.25);
        padding: 6px; border-radius: 4px; font-size: 0.88rem; font-weight: 900;
        color: #00ff00 !important; white-space: nowrap; margin-top: 6px; 
        letter-spacing: -0.5px;
    }
    .num-align.light { background-color: rgba(0,0,0,0.05); color: #007a00 !important; }
    .advice-txt { text-align: center; font-size: 0.88rem; font-weight: 900; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=30)
def fetch_analysis(ticker):
    if not ticker: return None
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=60d&interval=1d"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()['chart']['result'][0]
        c = pd.Series(res['indicators']['quote'][0]['close']).ffill()
        v = pd.Series(res['indicators']['quote'][0]['volume']).ffill()
        m10, m20 = c.rolling(10).mean(), c.rolling(20).mean()
        e12, e26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
        macd = e12 - e26
        delta = c.diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))

        ps_h, sbuy_h = [], []
        for i in range(-5, 0):
            x1 = (5 if macd.iloc[i] > 0 else 0) + (5 if rsi.iloc[i] > 50 else 0)
            dist = abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            
            # --- 核心修正：PS 統一小數點後一位 ---
            ps_val = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            ps_h.append(f"{ps_val:>4.1f}")
            sbuy_h.append("🔥" if (int(x2) >= 7 and c.iloc[i] > m20.iloc[i]) else "❄️")

        curr_ps = float(ps_h[-1])
        curr_sbuy = sbuy_h[-1]
        
        # 綜合判定建議邏輯
        if curr_ps >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒"
        elif curr_ps >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備蓄勢"
        elif curr_ps >= 5:
            bg = "bg-observe"
            adv = "✨ 偵測買點" if curr_sbuy == "🔥" else "☁️ 蹲下蓄力"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊"

        return {"p": f"${c.iloc[-1]:.2f}", "chg": f"({((c.iloc[-1]/c.iloc[-2])-1)*100:+.2f}%)",
                "ps": ps_h[-1], "sbuy": curr_sbuy, "x1": int(x1), "x2": int(x2), "x3": int(x3),
                "h_ps": " | ".join(ps_h), "h_sbuy": " | ".join(sbuy_h), "bg": bg, "adv": adv}
    except: return None

# --- 側邊欄偵察區 ---
with st.sidebar:
    st.header("📡 戰略偵察")
    with st.form("side_form"):
        user_input = st.text_input("輸入代碼")
        st.form_submit_button("執行偵察 🛰️")
    tkrs_side = [t.strip().upper() for t in user_input.split(",") if t.strip()]
    st.markdown("---")
    for tkr in tkrs_side:
        d = fetch_analysis(tkr)
        if d:
            p_color = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
            st.markdown(f'<div class="sidebar-card {d['bg']}"><div class="ticker-row"><span>{tkr}</span><span>SB: {d['sbuy']}</span></div><div style="font-size:0.8rem; font-weight:bold;">PS: {d['ps']}</div><div class="price-val" style="color:{p_color};">{d['p']} {d['chg']}</div><div class="data-row">X1:{d['x1']} / X2:{d['x2']} / X3:{d['x3']}</div><div class="num-align {"light" if "bg-observe" in d["bg"] else ""}">PS: {d["h_ps"]}<br>SB: {d["h_sbuy"]}</div><div class="advice-txt">{d["adv"]}</div></div>', unsafe_allow_html=True)

# --- 右側主視窗 11 板塊 ---
st.title("🛡️ 雙軌指揮中心 V32.9.38")
sectors = {"▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"], "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW"], "▋ AI 醫療與大數據": ["TEM", "PLTR", "SDGR"]}
for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, tkr in enumerate(tkrs):
        with cols[i % 2]:
            d = fetch_analysis(tkr)
            if d:
                p_color = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
                st.markdown(f'<div class="main-card {d['bg']}"><div class="ticker-row"><span>{tkr}</span><span>SB: {d['sbuy']}</span></div><div style="font-size:0.8rem; font-weight:bold;">PS: {d['ps']}</div><div class="price-val" style="color:{p_color};">{d['p']} {d['chg']}</div><div class="data-row">X1:{d['x1']} / X2:{d['x2']} / X3:{d['x3']}</div><div class="num-align {"light" if "bg-observe" in d["bg"] else ""}">PS: {d["h_ps"]}<br>SB: {d["h_sbuy"]}</div><div class="advice-txt">{d["adv"]}</div></div>', unsafe_allow_html=True)
