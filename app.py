
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (F1/F2/F3 定錨邏輯) ---
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

@st.cache_data(ttl=600)
def analyze_v101(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr, prev = df.iloc[-1], df.iloc[-2]
        p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
        vol_r = float(curr['Volume'] / df['Volume'].tail(10).mean())

        # F2 價格結構(50%) | F3 主力籌碼(30%) | F1 技術共振(20%)
        f2_s = 5 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
        f3_s = 3 if ((p > prev['Close'] and vol_r > 1.2) or (p < prev['Close'] and vol_r < 0.8)) and (rsi > 45) else 0
        f1_s = 2 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0

        total = f2_s + f3_s + f1_s
        
        # 戰略指令定錨
        if total >= 10: stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8: stat, cmd = "✅ 積極建倉", "建立 1/2 倉位 / 分批加碼"
        elif total >= 5: stat, cmd = "🟡 試探摸索", "建立 1/4 底倉 / 嚴守停損"
        elif total >= 3: stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else: stat, cmd = "❌ 全力撤退", "清倉空手 / 嚴禁買入"
            
        return {
            "p": p, "r": rsi, "s": total, "stat": stat, "cmd": cmd,
            "d1": f"F1 技術共振 (20%): {f1_s}/2",
            "d2": f"F2 價格結構 (50%): {f2_s}/5",
            "d3": f"F3 主力籌碼 (30%): {f3_s}/3",
            "ch": ((p-prev['Close'])/prev['Close'])*100
        }
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V10.1 戰略指揮中心", layout="wide")

# --- 🕹️ 側邊欄：獨立偵察艙 (所有的 Input 結果都鎖在這裡) ---
st.sidebar.title("🕹️ 戰略控制台")
custom_ticker = st.sidebar.text_input("🔍 自定義偵察 (輸入代碼)", "").upper()

if custom_ticker:
    # 這裡就是你要的：Input 下方直接輸出結果
    res = analyze_v101(custom_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {custom_ticker} 偵察報告")
        st.sidebar.divider()
        st.sidebar.subheader(f"戰略狀態：{res['stat']}")
        st.sidebar.warning(f"👉 具體建議：{res['cmd']}")
        
        # 顯示個別 F1/F2/F3 分數與權重
        st.sidebar.write(f"🏆 **總分：{res['s']} / 10 Pts**")
        st.sidebar.info(f"{res['d2']}\n\n{res['d3']}\n\n{res['d1']}")
        
        st.sidebar.metric("當前股價", f"${res['p']:.2f}", f"{res['ch']:.1f}%")
    else:
        st.sidebar.error("查無數據，請確認代碼是否正確。")

# --- 主頁面區域 (板塊晴雨表) ---
st.title("🛡️ 三維戰略指揮中心 V10.1")
st.markdown("### 📊 科學比重：F2 結構(50%) + F3 籌碼(30%) + F1 技術(20%)")
st.divider()

# --- 11 大板塊 (國防安全成員更新) ---
SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "🚀 太空經濟": ["RKLB", "ASTS", "SPIR", "BKSY"],
    "💻 核心算力": ["NVDA", "AMD", "AVGO", "TSM"],
    "🤖 機器人/AI": ["ASML", "AMAT", "LRCX", "ISRG"],
    "⚡ 能源轉型": ["VST", "CEG", "NNE", "OKLO"],
    "🧬 生物/醫療": ["TEM", "RXRX", "DNA", "MNA"],
    "☁️ 雲端軟體": ["PLTR", "SNOW", "CRM", "MSFT"],
    "🚗 電動車/傳產": ["TSLA", "RIVN", "F", "GM"],
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "LMT"], # 已更新
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v101(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:10px; text-align:center; color:white; border:1px solid #555; min-height:220px;">
                    <h3 style="margin:0; font-size:16px;">{t}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                    <hr style="margin:5px 0; opacity:0.3;">
                    <p style="font-size:10px; text-align:left;">F2 結構(50%): {res['d2'].split(': ')[1]}</p>
                    <p style="font-size:10px; text-align:left;">F3 籌碼(30%): {res['d3'].split(': ')[1]}</p>
                    <p style="font-size:10px; text-align:left;">F1 技術(20%): {res['d1'].split(': ')[1]}</p>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:14px; font-weight:bold; color:#FFD700;">{res['s']} Pts | {res['stat']}</p>
                    <p style="font-size:11px; margin-top:3px;"><b>{res['cmd']}</b></p>
                </div>
                """, unsafe_allow_html=True)
