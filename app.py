import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (嚴格遵守 V8.3 永久定錨邏輯) ---
def get_indicators(df):
    # F2: MA20 生命線 (必須站穩且具備 1.5% 緩衝)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    # F1: RSI 強勢區 & MACD 柱狀體
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    return df

def calculate_v83_score(df_slice, prev_row):
    """三維戰略核心邏輯：F2(50%) + F3(30%) + F1(20%)"""
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_r = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    # F2: 價格結構 (5分) - Stage 2 趨勢 (MA20>MA50>MA200) + 站穩 MA20 (1.5% 緩衝)
    f2_v = (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985)
    f2_s = 5 if f2_v else 0
    
    # F3: 主力籌碼 (3分) - 判定資金真偽 (攻擊量 > 1.3x / 洗盤量 < 0.8x)
    f3_v = (p > prev_row['Close'] and vol_r > 1.3) or (p < prev_row['Close'] and vol_r < 0.8)
    f3_s = 3 if (f3_v and rsi > 45) else 0
    
    # F1: 技術共振 (2分) - RSI >= 50 + MACD 翻紅 + 站上生命線
    f1_v = (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20)
    f1_s = 2 if f1_v else 0
    
    return f1_s, f2_s, f3_s

@st.cache_data(ttl=600)
def analyze_v104_full(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d", timeout=15)
        if df.empty or len(df) < 260: return None
        df = get_indicators(df).dropna()
        
        # --- 滾動五日軌跡計算 (應用於所有標的) ---
        scores_history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            current_slice = df.iloc[:idx+1]
            prev_row = df.iloc[idx-1]
            f1, f2, f3 = calculate_v83_score(current_slice, prev_row)
            scores_history.append(f1 + f2 + f3)
            
        latest_f1, latest_f2, latest_f3 = calculate_v83_score(df, df.iloc[-2])
        total = scores_history[-1]
        
        # 戰略動作定錨
        if total >= 10: stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8: stat, cmd = "✅ 積極建倉", "建立 1/2 倉位 / 分批加碼"
        elif total >= 5: stat, cmd = "🟡 試探摸索", "建立 1/4 底倉 / 嚴守停損"
        elif total >= 3: stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else: stat, cmd = "❌ 全力撤退", "清倉空手 / 嚴禁買入"
            
        return {
            "p": df.iloc[-1]['Close'], "s": total, "stat": stat, "cmd": cmd,
            "f1": latest_f1, "f2": latest_f2, "f3": latest_f3,
            "history": scores_history, 
            "ch": ((df.iloc[-1]['Close']-df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100
        }
    except: return None

# --- UI 渲染區 ---
st.set_page_config(page_title="V10.4 終極軌跡版", layout="wide")

# --- 側邊欄：獨立偵察艙 ---
st.sidebar.title("🕹️ 戰略控制台")
custom_ticker = st.sidebar.text_input("🔍 自定義偵察 (輸入代碼)", "").upper()

if custom_ticker:
    res = analyze_v104_full(custom_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {custom_ticker} 偵察報告")
        st.sidebar.divider()
        st.sidebar.subheader(f"戰略狀態：{res['stat']}")
        st.sidebar.warning(f"👉 具體建議：{res['cmd']}")
        st.sidebar.write(f"🏆 **今日總分：{res['s']} Pts**")
        st.sidebar.info(f"🧱 F2: {res['f2']}/5 | 🔥 F3: {res['f3']}/3 | ✅ F1: {res['f1']}/2")
        
        h_str = " | ".join([str(s) for s in res['history']])
        st.sidebar.code(f"滾動五日軌跡 [T-4 → 今日]：\n{h_str}", language="text")
        st.sidebar.metric("價格", f"${res['p']:.2f}", f"{res['ch']:.1f}%")
    else: st.sidebar.error("代碼錯誤")

# --- 主頁面區域 ---
st.title("🛡️ 三維戰略指揮中心 V10.4")
st.markdown("### 📊 全標的滾動式五日戰略窗格 [ T-4 | T-3 | T-2 | T-1 | 今日 ]")
st.divider()

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
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "LMT"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v104_full(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                h_str = " | ".join([str(s) for s in res['history']])
                st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:10px; text-align:center; color:white; border:1px solid #555; min-height:300px;">
                    <h3 style="margin:0; font-size:16px;">{t}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                    <div style="background-color:rgba(0,0,0,0.4); padding:6px; border-radius:5px; margin:8px 0;">
                        <p style="font-size:10px; color:#CCC; margin:0 0 4px 0;">滾動五日軌跡</p>
                        <p style="font-size:13px; font-weight:bold; color:#00FF00;">{h_str}</p>
                    </div>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:14px; font-weight:bold; color:#FFD700;">{res['s']} Pts | {res['stat']}</p>
                    <p style="font-size:10px;"><b>{res['cmd']}</b></p>
                </div>
                """, unsafe_allow_html=True)

