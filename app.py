import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- 0. UI 精緻縮小版 (PS & SBUY 雙軌定錨) ---
st.set_page_config(layout="wide", page_title="雙軌指揮中心 V32.9.33")

st.markdown("""
    <style>
    .sidebar-card {
        border-radius: 8px; padding: 10px; margin-bottom: 8px;
        border: 1px solid rgba(0,0,0,0.1); color: #ffffff;
    }
    .bg-power-buy { background-color: #004d00 !important; } 
    .bg-accumulate { background-color: #2e7d32 !important; } 
    .bg-observe { background-color: #ffffff !important; color: #333 !important; border: 1px solid #ccc !important; } 
    .bg-retreat { background-color: #4e342e !important; } 

    .ticker-row { display: flex; justify-content: space-between; font-size: 0.95rem; font-weight: bold; }
    .ps-label { font-size: 0.75rem; font-weight: bold; opacity: 0.85; margin: 2px 0; }
    .price-val { font-size: 1.15rem; font-weight: bold; text-align: center; margin: 4px 0; }
    
    .data-row { 
        font-size: 0.72rem; line-height: 1.4; margin-top: 4px; 
        border-top: 1px solid rgba(255,255,255,0.2); padding-top: 4px;
    }
    .num-align {
        font-family: 'Courier New', monospace; background-color: rgba(0,0,0,0.25);
        padding: 5px; border-radius: 4px; font-size: 0.8rem; 
        color: #00ff00 !important; white-space: nowrap; margin-top: 4px;
    }
    .num-align.light { background-color: rgba(0,0,0,0.05); color: #007a00 !important; }
    .advice-txt { text-align: center; font-size: 0.8rem; font-weight: bold; margin-top: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 核心引擎 (PS 與 SBUY 邏輯) ---
@st.cache_data(ttl=10)
def fetch_strategic_analysis(ticker):
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

        ps_h, x2_h = [], []
        for i in range(-5, 0):
            # X123 權重 30/40/30
            x1 = (5 if macd.iloc[i] > 0 else 0) + (5 if rsi.iloc[i] > 50 else 0)
            dist = abs(m10.iloc[i] - m20.iloc[i])/m20.iloc[i]
            x2 = 10 if dist < 0.03 else (7 if dist < 0.05 else 3)
            x3 = (7 if c.iloc[i] > m20.iloc[i] else 4) + (3 if v.iloc[i] > v.rolling(10).mean().iloc[i] * 1.3 else 0)
            
            ps_val = round((x1*0.3 + x2*0.4 + x3*0.3), 1)
            ps_h.append(f"{ps_val:>4.1f}")
            x2_h.append(f"{int(x2):>2d}")

        curr_ps = float(ps_h[-1])
        # SBUY 偵測邏輯：當 X2=10 (結構定錨) 且出現量能異動時
        sbuy_trigger = "ON" if (int(x2_h[-1]) >= 7 and c.iloc[-1] > m20.iloc[-1]) else "OFF"
        
        # 買賣建議
        if curr_ps >= 9 and macd.iloc[-1] > 0: bg, adv = "bg-power-buy", "🚀 起飛衝鋒"
        elif curr_ps >= 7 and macd.iloc[-1] > 0: bg, adv = "bg-accumulate", "🌿 準備蓄勢"
        elif curr_ps >= 5: bg, adv = "bg-observe", "☁️ 蹲下蓄力"
        else: bg, adv = "bg-retreat", "🟫 快逃命啊"

        return {"p": f"${c.iloc[-1]:.2f}", "chg": f"({((c.iloc[-1]/c.iloc[-2])-1)*100:+.2f}%)",
                "ps": ps_h[-1], "sbuy": sbuy_trigger, "x1": int(x1), "x2": int(x2_h[-1]), "x3": int(x3),
                "h_ps": " | ".join(ps_h), "h_x2": " | ".join(x2_h), "bg": bg, "adv": adv}
    except: return None

# --- 2. 側邊欄：左側垂直偵察 (PS & SBUY) ---
with st.sidebar:
    st.header("📡 戰略偵察")
    user_input = st.text_input("輸入代碼", key="sbuy_input", placeholder="如: LUNR, KTOS")
    tkrs = [t.strip().upper() for t in user_input.split(",") if t.strip()]
    
    st.markdown("---")
    if tkrs:
        for tkr in tkrs:
            d = fetch_strategic_analysis(tkr)
            if d:
                p_c = "#ff4b4b" if "+" in d['chg'] else "#00ff00"
                h_style = "light" if "bg-observe" in d['bg'] else ""
                st.markdown(f"""
                <div class="sidebar-card {d['bg']}">
                    <div class="ticker-row"><span>{tkr}</span><span>SBUY: {d['sbuy']}</span></div>
                    <div class="ps-label">Primary Score (PS): {d['ps']}</div>
                    <div class="price-val" style="color:{p_c};">{d['p']} {d['chg']}</div>
                    <div class="data-row">
                        X1:{d['x1']} / X2:{d['x2']} / X3:{d['x3']}
                    </div>
                    <div class="num-align {h_style}">
                        PS: {d['h_ps']}<br>X2: {d['h_x2']}
                    </div>
                    <div class="advice-txt">{d['adv']}</div>
                </div>
                """, unsafe_allow_html=True)

# --- 3. 右側主視窗 ---
st.title("🛡️ 雙軌指揮中心 V32.9.33")
st.info("💡 定錨完成：PS (主分數) 決定顏色，SBUY (開始買入) 負責提前預警主力介入。")

