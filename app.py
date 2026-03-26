
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 0. UI 終極視覺規範 (PS 點零對齊、SB 軌跡、字體密集加粗) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.43")

st.markdown("""
    <style>
    .sector-title { font-size: 1.1rem; font-weight: bold; color: #44aaff; margin: 15px 0 8px 0; border-left: 6px solid #44aaff; padding-left: 10px; }
    .sidebar-card, .main-card { border-radius: 8px; padding: 10px; margin-bottom: 8px; border: 1px solid rgba(0,0,0,0.1); color: #ffffff; }
    .main-card { color: #333; min-height: 240px; }

    /* 戰略底色定錨 */
    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ccc !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-row { display: flex; justify-content: space-between; font-size: 1.0rem; font-weight: 900; }
    .price-val { font-size: 1.25rem; font-weight: 900; text-align: center; margin: 4px 0; }
    
    /* X123 密集對齊加粗 */
    .data-row { 
        font-size: 0.82rem; font-weight: 900; line-height: 1.3; margin-top: 4px; 
        border-top: 1px solid rgba(128,128,128,0.4); padding-top: 4px;
    }
    
    /* PS 與 SB 陣列：強制定標對齊 */
    .num-align {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.25);
        padding: 5px; border-radius: 4px; font-size: 0.85rem; font-weight: 900;
        color: #00ff00 !important; white-space: nowrap; margin-top: 5px; 
        letter-spacing: -0.6px; line-height: 1.2;
    }
    .num-align.light { background-color: rgba(0,0,0,0.05); color: #007a00 !important; }
    .advice-txt { text-align: center; font-size: 0.88rem; font-weight: 900; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 強化數據引擎 (非雅虎原生封裝，避開封鎖) ---
@st.cache_data(ttl=60)
def fetch_analysis(ticker):
    if not ticker: return None
    try:
        # 模擬專業瀏覽器標頭，防止 API 抓不到數據
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=60d"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10).json()['chart']['result'][0]
        
        c = pd.Series(res['indicators']['quote'][0]['close']).ffill()
        v = pd.Series(res['indicators']['quote'][0]['volume']).ffill()
        m10, m20 = c.rolling(10).mean(), c.rolling(20).mean()
        e12, e26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
        macd = e12 - e26
        delta = c.diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))

        ps_h, sb_h = [], []
        for i in range(-5, 0):
            # X1(技術), X2(構造), X3(主力)
            x1 = (5 if macd.iloc[i] > 0 else 0) + (5 if rsi.iloc[i] > 50 else 0)
            dist = abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            
            # PS 統一點零對齊
            ps_val = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            ps_h.append(f"{ps_val:>4.1f}")
            # SB 點火軌跡判定 (核心邏輯)
            sb_h.append("🔥" if (int(x2) >= 7 and c.iloc[i] > m20.iloc[i]) else "❄️")

        curr_ps, curr_sb = float(ps_h[-1]), sb_h[-1]
        
        # 綜合判定邏輯 (PS + SBUY 混合)
        if curr_ps >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒"
        elif curr_ps >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備蓄勢"
        elif curr_ps >= 5:
            bg = "bg-observe"
            adv = "✨ 偵測買點" if curr_sb == "🔥" else "☁️ 蹲下蓄力"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊"

        return {"p": f"${c.iloc[-1]:.2f}", "chg": f"({((c.iloc[-1]/c.iloc[-2])-1)*100:+.2f}%)",
                "ps": ps_h[-1], "sbuy": curr_sb, "x1": int(x1), "x2": int(x2), "x3": int(x3),
                "h_ps": " | ".join(ps_h), "h_sb": " | ".join(sb_h), "bg": bg, "adv": adv}
    except: return None

# --- 2. 側邊欄：左側垂直偵察 ---
with st.sidebar:
    st.header("📡 戰略偵察")
    with st.form("side_form"):
        user_input = st.text_input("輸入代碼 (逗號隔開)", key="v43_input")
        st.form_submit_button("執行偵察 🛰️")
    tkrs_side = [t.strip().upper() for t in user_input.split(",") if t.strip()]
    st.markdown("---")
    for tkr in tkrs_side:
        d = fetch_analysis(tkr)
        if d:
            p_color = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
            st.markdown(f"""
            <div class="sidebar-card {d['bg']}">
                <div class="ticker-row"><span>{tkr}</span><span>SB: {d['sbuy']}</span></div>
                <div style="font-size:0.75rem; font-weight:900;">PS: {d['ps']}</div>
                <div class="price-val" style="color:{p_color};">{d['p']} {d['chg']}</div>
                <div class="data-row">X1:{d['x1']} / X2:{d['x2']} / X3:{d['x3']}</div>
                <div class="num-align {"light" if "bg-observe" in d["bg"] else ""}">PS: {d["h_ps"]}<br>SB: {d["h_sb"]}</div>
                <div class="advice-txt">{d["adv"]}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 3. 右側主視窗：11 板塊全開 ---
st.title("🛡️ 雙軌指揮中心 V32.9.43")
sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"],
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW", "AVGO"],
    "▋ AI 醫療與大數據": ["TEM", "PLTR", "SDGR", "RXRX"]
}

for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, tkr in enumerate(tkrs):
        with cols[i % 2]:
            d = fetch_analysis(tkr)
            if d:
                p_color = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
                st.markdown(f"""
                <div class="main-card {d['bg']}">
                    <div class="ticker-row"><span>{tkr}</span><span>SB: {d['sbuy']}</span></div>
                    <div style="font-size:0.75rem; font-weight:900;">PS: {d['ps']}</div>
                    <div class="price-val" style="color:{p_color};">{d['p']} {d['chg']}</div>
                    <div class="data-row">X1:{d['x1']} / X2:{d['x2']} / X3:{d['x3']}</div>
                    <div class="num-align {"light" if "bg-observe" in d["bg"] else ""}">PS: {d["h_ps"]}<br>SB: {d["h_sb"]}</div>
                    <div class="advice-txt">{d["adv"]}</div>
                </div>
                """, unsafe_allow_html=True)
