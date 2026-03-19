import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (V8.3 永久定錨邏輯，不簡化) ---
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
    """嚴格執行三維戰略核心邏輯"""
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_r = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    # F2: 價格結構 (50%) - 冠軍操盤手 Stage 2 趨勢 + 站穩生命線
    f2_v = (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985)
    f2_s = 5 if f2_v else 0
    
    # F3: 主力籌碼 (30%) - 攻擊量 > 1.3x 或 洗盤量 < 0.8x
    f3_v = (p > prev_row['Close'] and vol_r > 1.3) or (p < prev_row['Close'] and vol_r < 0.8)
    f3_s = 3 if (f3_v and rsi > 45) else 0
    
    # F1: 技術共振 (20%) - RSI>50 + MACD翻紅
    f1_v = (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20)
    f1_s = 2 if f1_v else 0
    
    return f1_s, f2_s, f3_s

@st.cache_data(ttl=600)
def analyze_v114(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d", timeout=15)
        if df.empty or len(df) < 260: return None
        df = get_indicators(df).dropna()
        
        scores_history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            current_slice = df.iloc[:idx+1]
            prev_row = df.iloc[idx-1]
            f1, f2, f3 = calculate_v83_score(current_slice, prev_row)
            scores_history.append(f1 + f2 + f3)
            
        latest_f1, latest_f2, latest_f3 = calculate_v83_score(df, df.iloc[-2])
        total = scores_history[-1]
        
        # 指令定錨 (文字修正版)
        if total >= 10: stat, cmd = "🔥 全力進攻", "重倉持有 / 積極加碼"
        elif total >= 8: stat, cmd = "✅ 積極建倉", "1/2 倉 / 分批加碼"
        elif total >= 5: stat, cmd = "🟡 試探摸索", "1/4 倉 / 嚴守停損"
        elif total >= 3: stat, cmd = "⚠️ 減碼警戒", "減倉 1/2 / 獲利了結"
        else: stat, cmd = "❌ 全力撤退", "清倉空手 / 嚴禁買入"
            
        return {
            "p": df.iloc[-1]['Close'], "s": total, "stat": stat, "cmd": cmd,
            "f1": latest_f1, "f2": latest_f2, "f3": latest_f3,
            "history": scores_history, 
            "ch": ((df.iloc[-1]['Close']-df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100
        }
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V11.4 戰略認知版", layout="wide")

# --- 🕹️ 側邊欄：獨立偵察艙 (所有的結果鎖定在 Input 下方) ---
st.sidebar.title("🕹️ 戰術控制台")
custom_ticker = st.sidebar.text_input("🔍 自定義偵察 (輸入代碼)", "").upper()

if custom_ticker:
    res = analyze_v114(custom_ticker)
    if res:
        st.sidebar.markdown(f"## 🎯 {custom_ticker} 偵察報告")
        st.sidebar.divider()
        st.sidebar.subheader(f"戰略狀態：{res['stat']}")
        st.sidebar.warning(f"👉 建議：{res['cmd']}") 
        
        # 🌟 視覺修正：左側偵察艙深度解碼 (增加比重與白話文)
        st.sidebar.info(f"""
        🧱 **冠軍操盤手 (F2 結構 50%)**: {res['f2']}/5 Pts
        \n🔥 **主力籌碼 (F3 成交量 30%)**: {res['f3']}/3 Pts
        \n✅ **技術指標 (F1 動能 20%)**: {res['f1']}/2 Pts
        \n🏆 今日總分: **{res['s']} Pts**
        """)
        
        # 側邊欄軌跡強制不換行
        h_str = " | ".join([str(s) for s in res['history']])
        st.sidebar.markdown(f"""
        <div style="background-color:rgba(0,0,0,0.5); padding:8px; border-radius:6px; border:1px solid rgba(255,255,255,0.2); text-align:center;">
            <p style="font-size:11px; color:#CCC; margin:0 0 5px 0;">滾動五日軌跡 (舊→新)</p>
            <p style="font-size:15px; font-weight:bold; color:#00FF00; letter-spacing:2px; white-space:nowrap;">{h_str}</p>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.metric("當前價格", f"${res['p']:.2f}", f"{res['ch']:.1f}%")
    else: st.sidebar.error("查無數據")

# --- 主頁面區域 (板塊晴雨表) ---
st.title("🛡️ 三維戰略指揮中心 V11.4")
st.markdown("### 📊 滾動五日軌跡：F2 結構(50%) + F3 籌碼(30%) + F1 技術(20%)")
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
    "🛰️ 國防安全": ["KTOS", "BBAI", "RCAT", "CRCL"],
    "📡 無線通訊": ["ONDS", "QCOM", "TMUS"]
}

for name, tickers in SECTORS.items():
    st.subheader(f"📍 {name}")
    grid = st.columns(4) 
    for j, t in enumerate(tickers):
        res = analyze_v114(t)
        with grid[j % 4]:
            if res:
                bg = "#1E4620" if res['s'] >= 8 else "#46461E" if res['s'] >= 5 else "#461E1E"
                h_str = " | ".join([str(s) for s in res['history']])
                
                # 主頁面卡片 HTML (維持清爽，防折斷)
                traj_html = f"""<div style="display: flex; justify-content: center; align-items: center; white-space: nowrap;"><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][0]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][1]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][2]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][3]}</span><span style="color: #666; font-size: 10px; margin: 0 4px;">|</span><span style="font-size: 14px; font-weight: bold; color: #00FF00;">{res['history'][4]}</span></div>"""
                
                st.markdown(f"""
                <div style="background-color:{bg}; padding:10px; border-radius:10px; text-align:center; color:white; border:1px solid #555; min-width:210px; margin-bottom:10px;">
                    <h3 style="margin:0; font-size:16px;">{t}</h3>
                    <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                    <div style="font-size:11px; color:#DDD; margin-bottom:5px;">
                        🧱 F2:{res['f2']} | 🔥 F3:{res['f3']} | ✅ F1:{res['f1']}
                    </div>
                    <div style="background-color:rgba(0,0,0,0.5); padding:5px; border-radius:5px; margin:5px 0; border:1px solid rgba(255,255,255,0.1);">
                        <p style="font-size:9px; color:#CCC; margin:0 0 4px 0;">五日軌跡 [舊→新]</p>
                        {traj_html}
                    </div>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:14px; font-weight:bold; color:#FFD700; margin:0;">{res['s']} Pts | {res['stat']}</p>
                    <p style="font-size:11px; margin-top:3px;"><b>{res['cmd']}</b></p>
                </div>
                """, unsafe_allow_html=True)


