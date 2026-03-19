
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (V8.3 永久定錨) ---
def get_indicators(df):
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    return df

def calculate_v83_score(df_slice, prev_row):
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_r = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    # F2:5(結構) | F3:3(籌碼) | F1:2(指標)
    f2_s = 5 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    f3_s = 3 if ((p > prev_row['Close'] and vol_r > 1.3) or (p < prev_row['Close'] and vol_r < 0.8)) and (rsi > 45) else 0
    f1_s = 2 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    return f1_s, f2_s, f3_s

@st.cache_data(ttl=600)
def analyze_v125(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d", timeout=15)
        if df.empty or len(df) < 260: return None
        df = get_indicators(df).dropna()
        scores_h = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            f1, f2, f3 = calculate_v83_score(df.iloc[:idx+1], df.iloc[idx-1])
            scores_h.append(f1 + f2 + f3)
        l_f1, l_f2, l_f3 = calculate_v83_score(df, df.iloc[-2])
        total = scores_h[-1]
        if total >= 10: stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8: stat, cmd = "✅ 積極建倉", "1/2 倉 / 分批加碼"
        elif total >= 5: stat, cmd = "🟡 試探摸索", "1/4 倉 / 嚴守停損"
        elif total >= 3: stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else: stat, cmd = "❌ 全力撤退", "清倉空手 / 嚴禁買入"
        return {"p": df.iloc[-1]['Close'], "s": total, "stat": stat, "cmd": cmd, "f1": l_f1, "f2": l_f2, "f3": l_f3, "history": scores_h, "ch": ((df.iloc[-1]['Close']-df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100}
    except: return None

# --- 2. UI 渲染 (V12.5 橫向廊道版) ---
st.set_page_config(page_title="V12.5 橫向戰略廊道版", layout="wide")

# 🌟 全域 CSS：隱藏滾動條但保留功能，美化橫向容器
st.markdown("""
    <style>
    .horizontal-scroll-wrapper {
        display: flex;
        overflow-x: auto;
        padding: 10px 5px;
        gap: 15px;
        scroll-behavior: smooth;
        -webkit-overflow-scrolling: touch;
    }
    .horizontal-scroll-wrapper::-webkit-scrollbar {
        height: 6px;
    }
    .horizontal-scroll-wrapper::-webkit-scrollbar-thumb {
        background-color: #555;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄：獨立偵察艙 ---
st.sidebar.title("🕹️ 戰術控制台")
c_ticker = st.sidebar.text_input("🔍 偵察代碼 (如 RCAT)", "").upper()

if c_ticker:
    res = analyze_v125(c_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {c_ticker} 偵察報告")
        st.sidebar.error(f"📍 戰略狀態：{res['stat']}")
        st.sidebar.warning(f"👉 操作建議：{res['cmd']}")
        st.sidebar.info(f"🧱 **冠軍結構(F2)**: {res['f2']}/5 Pts\n\n🔥 **主力籌碼(F3)**: {res['f3']}/3 Pts\n\n✅ **技術動能(F1)**: {res['f1']}/2 Pts\n\n🏆 **今日總分**: {res['s']} Pts")
        h = res['history']
        h_str = f"{h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]}"
        st.sidebar.markdown(f'<div style="background-color:#000; padding:12px; border-radius:8px; text-align:center; color:#0f0; font-size:22px; font-weight:bold; border:1px solid #444;">{h_str}</div>', unsafe_allow_html=True)

st.title("🛡️ 三維戰略指揮中心 V12.5")
st.markdown("### 📊 橫向戰略廊道：[ T-4 | T-3 | T-2 | T-1 | 今日 ]")

SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🚀 太空經濟": ["RKLB", "ASTS", "SPIR", "BKSY"],
    "💻 核心算力": ["NVDA", "AMD", "AVGO", "TSM"],
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "CRCL"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    
    # 🌟 橫向佈局核心：開啟滾動容器
    sector_html = '<div class="horizontal-scroll-wrapper">'
    
    for t in tickers:
        res = analyze_v125(t)
        if res:
            bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
            h = res['history']
            h_str = f"{h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]}"
            
            # 構造單張卡片 (固定寬度 260px 防止折行)
            card = f'<div style="background-color:{bg}; min-width:260px; max-width:260px; padding:15px; border-radius:12px; text-align:center; color:white; border:1px solid #555; margin-bottom:5px;">'
            card += f'<h3 style="margin:0; font-size:16px;">{t}</h3>'
            card += f'<p style="font-size:22px; font-weight:bold; margin:3px 0;">${res["p"]:.2f}</p>'
            # 分項白話文區
            card += f'<div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:8px 0; font-size:11px; line-height:1.5;">'
            card += f'<div>🧱 冠軍結構(F2): <b>{res["f2"]}</b></div>'
            card += f'<div>🔥 主力籌碼(F3): <b>{res["f3"]}</b></div>'
            card += f'<div>✅ 技術動能(F1): <b>{res["f1"]}</b></div></div>'
            # 軌跡區
            card += f'<div style="background-color:#000; padding:10px 5px; border-radius:8px; margin:10px 0; border:1px solid #444; color:#0f0; font-weight:bold; font-size:16px; letter-spacing:1px;">{h_str}</div>'
            # 底部
            card += f'<hr style="margin:8px 0; opacity:0.3;">'
            card += f'<p style="font-size:14px; font-weight:bold; color:#FFD700; margin:0;">{res["s"]} Pts | {res["stat"]}</p>'
            card += f'<p style="font-size:11px; margin-top:5px; line-height:1.2; height:30px;"><b>{res["cmd"]}</b></p></div>'
            
            sector_html += card
            
    sector_html += '</div>'
    st.markdown(sector_html, unsafe_allow_html=True)
