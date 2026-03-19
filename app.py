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
def analyze_v116(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d", timeout=15)
        if df.empty or len(df) < 260: return None
        df = get_indicators(df).dropna()
        scores_history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            f1, f2, f3 = calculate_v83_score(df.iloc[:idx+1], df.iloc[idx-1])
            scores_history.append(f1 + f2 + f3)
        l_f1, l_f2, l_f3 = calculate_v83_score(df, df.iloc[-2])
        total = scores_history[-1]
        if total >= 10: stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8: stat, cmd = "✅ 積極建倉", "1/2 倉 / 分批加碼"
        elif total >= 5: stat, cmd = "🟡 試探摸索", "1/4 倉 / 嚴守停損"
        elif total >= 3: stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else: stat, cmd = "❌ 全力撤退", "清倉空手 / 嚴禁買入"
        return {"p": df.iloc[-1]['Close'], "s": total, "stat": stat, "cmd": cmd, "f1": l_f1, "f2": l_f2, "f3": l_f3, "history": scores_history, "ch": ((df.iloc[-1]['Close']-df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100}
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V11.6 空間定錨版", layout="wide")

# --- 側邊欄：獨立偵察艙 ---
st.sidebar.title("🕹️ 戰術控制台")
c_ticker = st.sidebar.text_input("🔍 自定義偵察", "").upper()
if c_ticker:
    res = analyze_v116(c_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {c_ticker} 報告")
        st.sidebar.info(f"🧱 **冠軍操盤手 (F2)**: {res['f2']}/5\n\n🔥 **主力籌碼 (F3)**: {res['f3']}/3\n\n✅ **技術指標 (F1)**: {res['f1']}/2")
        h_str = " | ".join([str(s) for s in res['history']])
        st.sidebar.markdown(f"""<div style="background-color:rgba(0,0,0,0.5); padding:8px; border-radius:6px; text-align:center;"><p style="font-size:15px; font-weight:bold; color:#00FF00; margin:0;">{h_str}</p></div>""", unsafe_allow_html=True)

# --- 主頁面區域 ---
st.title("🛡️ 三維戰略指揮中心 V11.6")
st.markdown("### 📊 指標權重：F2 結構(50%) + F3 籌碼(30%) + F1 技術(20%)")

SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🚀 太空經濟": ["RKLB", "ASTS", "SPIR", "BKSY"],
    "💻 核心算力": ["NVDA", "AMD", "AVGO", "TSM"],
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "CRCL"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(4) 
    for j, t in enumerate(tickers):
        res = analyze_v116(t)
        with grid[j % 4]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                # 🌟 右側卡片空間重組：增加白話文與權重顯示
                traj_html = f"""<div style="display: flex; justify-content: center; align-items: center; white-space: nowrap;"><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][0]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][1]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][2]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][3]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][4]}</span></div>"""
                
                st.markdown(f"""
                <div style="background-color:{bg}; padding:12px 10px; border-radius:12px; text-align:center; color:white; border:1px solid #555; min-width:210px; margin-bottom:15px;">
                    <h3 style="margin:0; font-size:14px; opacity:0.8;">{t}</h3>
                    <p style="font-size:22px; font-weight:bold; margin:2px 0;">${res['p']:.2f}</p>
                    
                    <div style="text-align:left; background:rgba(0,0,0,0.3); padding:6px; border-radius:6px; margin:6px 0; font-size:10px; line-height:1.4;">
                        <span style="color:#AAA;">🧱 冠軍結構(F2):</span> <b style="color:white;">{res['f2']}</b><br>
                        <span style="color:#AAA;">🔥 主力籌碼(F3):</span> <b style="color:white;">{res['f3']}</b><br>
                        <span style="color:#AAA;">✅ 技術動能(F1):</span> <b style="color:white;">{res['f1']}</b>
                    </div>

                    <div style="background-color:rgba(0,0,0,0.5); padding:5px; border-radius:5px; border:1px solid rgba(255,255,255,0.1);">
                        {traj_html}
                    </div>
                    <hr style="margin:8px 0; opacity:0.2;">
                    <p style="font-size:13px; font-weight:bold; color:#FFD700; margin:0;">{res['s']} Pts | {res['stat']}</p>
                    <p style="font-size:10px; margin-top:2px; opacity:0.9;"><b>{res['cmd']}</b></p>
                </div>
                """, unsafe_allow_html=True)

