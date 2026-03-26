
import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 終極視覺對位規範 (PS/SB 絕對對齊、11板塊回歸) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.48")

st.markdown("""
    <style>
    .sector-title { font-size: 1.1rem; font-weight: bold; color: #44aaff; margin: 18px 0 8px 0; border-left: 6px solid #44aaff; padding-left: 10px; }
    .sidebar-card, .main-card { border-radius: 8px; padding: 10px; margin-bottom: 8px; border: 1px solid rgba(0,0,0,0.1); color: #ffffff; }
    .main-card { color: #333; min-height: 260px; }

    .bg-power-buy { background-color: #004d00 !important; color: white !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; color: white !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ccc !important; border: 1px solid #ccc !important; } 
    .bg-retreat { background-color: #4e342e !important; color: white !important; } 

    .ticker-row { display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 900; }
    .price-val { font-size: 1.25rem; font-weight: 900; text-align: center; margin: 4px 0; }
    
    .data-row { 
        font-size: 0.8rem; font-weight: 900; line-height: 1.4; margin-top: 5px; 
        border-top: 1px solid rgba(128,128,128,0.4); padding-top: 5px; text-align: center;
    }
    
    /* 陣列對齊核心：使用預設字體寬度與強制定寬 */
    .num-align {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.25);
        padding: 8px; border-radius: 4px; font-size: 0.9rem; font-weight: 900;
        color: #00ff00 !important; white-space: pre; margin-top: 6px; 
        line-height: 1.5; display: block; width: 100%; text-align: center;
    }
    .num-align.light { background-color: rgba(0,0,0,0.05); color: #007a00 !important; }
    .advice-txt { text-align: center; font-size: 0.88rem; font-weight: 900; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=30)
def fetch_analysis(ticker):
    if not ticker: return None
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=60d"
        headers = {'User-Agent': 'Mozilla/5.0'}
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
            x1 = (5 if macd.iloc[i] > 0 else 0) + (5 if rsi.iloc[i] > 50 else 0)
            dist = abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            
            # 精準對齊：PS 固定佔 4 格，SB 固定佔 2 格寬度感
            ps_val = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            ps_h.append(f"{ps_val:>4.1f}")
            sb_h.append("🔥" if (int(x2) >= 7 and c.iloc[i] > m20.iloc[i]) else "❄️")

        curr_ps, curr_sb = float(ps_h[-1]), sb_h[-1]
        if curr_ps >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒"
        elif curr_ps >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備蓄勢"
        elif curr_ps >= 5:
            bg = "bg-observe"; adv = "✨ 偵測買點" if curr_sb == "🔥" else "☁️ 蹲下蓄力"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊"

        return {"p": f"${c.iloc[-1]:.2f}", "chg": f"({((c.iloc[-1]/c.iloc[-2])-1)*100:+.2f}%)",
                "ps": ps_h[-1], "sb": curr_sb, "x1": int(x1), "x2": int(x2), "x3": int(x3),
                "h_ps": " | ".join(ps_h), "h_sb": " | ".join(sb_h), "bg": bg, "adv": adv}
    except: return None

def render_card(tkr, d):
    if not d: return
    p_color = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
    st.markdown(f"""
    <div class="main-card {d['bg']}">
        <div class="ticker-row"><span>{tkr}</span><span>SB: {d['sb']}</span></div>
        <div style="font-size:0.75rem; font-weight:900; opacity:0.8;">PS: {d['ps']}</div>
        <div class="price-val" style="color:{p_color};">{d['p']} {d['chg']}</div>
        <div class="data-row">技術(30%):<b>{d['x1']}</b>/冠軍(40%):<b>{d['x2']}</b>/主力(30%):<b>{d['x3']}</b></div>
        <div class="num-align {"light" if "bg-observe" in d["bg"] else ""}">PS: {d["h_ps"]}\nSB:  {d["h_sb"]}</div>
        <div class="advice-txt">{d["adv"]}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄偵察區 ---
with st.sidebar:
    st.header("📡 戰略偵察")
    with st.form("side_form"):
        user_input = st.text_input("輸入代碼")
        st.form_submit_button("執行偵察 🛰️")
    tkrs_side = [t.strip().upper() for t in user_input.split(",") if t.strip()]
    st.markdown("---")
    for tkr in tkrs_side:
        render_card(tkr, fetch_analysis(tkr))

# --- 3. 右側主視窗：11 板塊完全復位 ---
st.title("🛡️ 雙軌指揮中心 V32.9.48")
sectors = {
    "▋ 太空技術精英": ["LUNR", "PL", "ASTS", "RKLB"],
    "▋ 矽光子/光通訊": ["AAOI", "AXTI", "GLW", "AVGO"],
    "▋ AI 醫療大數據": ["TEM", "PLTR", "SDGR", "RXRX"],
    "▋ 半導體設備商": ["ASML", "NVDA", "AMD", "TSM"],
    "▋ 數據中心/電力": ["VRT", "OKLO", "SMR", "CEG"],
    "▋ 量子計算技術": ["IONQ", "QUBT", "RGTI"],
    "▋ 國防安全系統": ["KTOS", "AVAV", "LMT"],
    "▋ 數位轉型軟體": ["MSFT", "CRM", "SNOW"],
    "▋ 能源與電動車": ["TSLA", "ENPH", "FSLR"],
    "▋ 網路安全防護": ["CRWD", "PANW", "FTNT"],
    "▋ 生物基因科技": ["AMGN", "GILD", "REGN"]
}

for sec, tkrs in sectors.items():
    st.markdown(f'<div class="sector-title">{sec}</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, tkr in enumerate(tkrs):
        with cols[i % 2]:
            render_card(tkr, fetch_analysis(tkr))
