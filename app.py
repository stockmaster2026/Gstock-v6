
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
    # F2:5(結構50%) | F3:3(籌碼30%) | F1:2(指標20%)
    f2_s = 5 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    f3_s = 3 if ((p > prev_row['Close'] and vol_r > 1.3) or (p < prev_row['Close'] and vol_r < 0.8)) and (rsi > 45) else 0
    f1_s = 2 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    return f1_s, f2_s, f3_s

@st.cache_data(ttl=600)
def analyze_v127(ticker):
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

# --- 2. UI 渲染 (V12.7 完全體) ---
st.set_page_config(page_title="V12.7 戰略權重定錨版", layout="wide")

# CSS 樣式鎖定
st.markdown("""
    <style>
    .horizontal-scroll-wrapper { display: flex; overflow-x: auto; padding: 10px 5px; gap: 15px; scroll-behavior: smooth; }
    .horizontal-scroll-wrapper::-webkit-scrollbar { height: 6px; }
    .horizontal-scroll-wrapper::-webkit-scrollbar-thumb { background-color: #777; border-radius: 10px; }
    .stat-box { background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; margin: 8px 0; font-size: 11px; border: 1px solid rgba(255,255,255,0.1); }
    .weight-tag { color: #FFD700; font-weight: bold; margin-left: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄：偵察艙 ---
st.sidebar.title("🕹️ 戰術控制台")
c_ticker = st.sidebar.text_input("🔍 偵察代碼 (如 RCAT)", "").upper()

if c_ticker:
    res = analyze_v127(c_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {c_ticker} 報告")
        st.sidebar.error(f"📍 戰略狀態：{res['stat']}")
        st.sidebar.warning(f"👉 操作建議：{res['cmd']}")
        
        # 側邊欄權重定錨
        st.sidebar.info(f"""
        🧱 **冠軍結構 (F2-50%)**: {res['f2']}/5 Pts
        🔥 **主力籌碼 (F3-30%)**: {res['f3']}/3 Pts
        ✅ **技術指標 (F1-20%)**: {res['f1']}/2 Pts
        ---
        🏆 今日總分: **{res['s']} Pts**
        """)
        h = res['history']
        h_str = f"{h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]}"
        st.sidebar.markdown(f'<div style="background-color:#000; padding:12px; border-radius:8px; text-align:center; color:#0f0; font-size:22px; font-weight:bold; border:1px solid #444;">{h_str}</div>', unsafe_allow_html=True)

st.title("🛡️ 三維戰略指揮中心 V12.7")
st.markdown("### 📊 全域對帳：F2 結構(50%) | F3 籌碼(30%) | F1 指標(20%)")

SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🚀 太空經濟": ["RKLB", "ASTS", "SPIR", "BKSY"],
    "💻 核心算力": ["NVDA", "AMD", "AVGO", "TSM"],
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "CRCL"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    sector_html = '<div class="horizontal-scroll-wrapper">'
    for t in tickers:
        res = analyze_v127(t)
        if res:
            bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
            h = res['history']
            h_str = f"{h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]}"
            
            # 🌟 視覺核心：強制顯示百分比權重
            card = f'<div style="background-color:{bg}; min-width:270px; max-width:270px; padding:15px; border-radius:12px; text-align:center; color:white; border:1px solid #555; margin-bottom:5px;">'
            card += f'<h3 style="margin:0; font-size:16px;">{t}</h3>'
            card += f'<p style="font-size:22px; font-weight:bold; margin:3px 0;">${res["p"]:.2f}</p>'
            
            # 白話文對帳區 (加入 50/30/20 標籤)
            card += f'<div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:8px 0; font-size:11px; line-height:1.6; border:1px solid rgba(255,255,255,0.1);">'
            card += f'<div>🧱 冠軍結構<span style="color:#FFD700;">(F2-50%)</span>: <b>{res["f2"]}</b></div>'
            card += f'<div>🔥 主力籌碼<span style="color:#FFD700;">(F3-30%)</span>: <b>{res["f3"]}</b></div>'
            card += f'<div>✅ 技術指標<span style="color:#FFD700;">(F1-20%)</span>: <b>{res["f1"]}</b></div></div>'
            
            # 軌跡區
            card += f'<div style="background-color:#000; padding:10px 5px; border-radius:8px; margin:10px 0; border:1px solid #444; color:#0f0; font-weight:bold; font-size:18px; letter-spacing:2px;">{h_str}</div>'
            
            # 底部指令
            card += f'<hr style="margin:8px 0; opacity:0.3;"><p style="font-size:14px; font-weight:bold; color:#FFD700; margin:0;">{res["s"]} Pts | {res["stat"]}</p>'
            card += f'<p style="font-size:11px; margin-top:5px; line-height:1.2; height:30px;"><b>{res["cmd"]}</b></p></div>'
            
            sector_html += card
    sector_html += '</div>'
    st.markdown(sector_html, unsafe_allow_html=True)
