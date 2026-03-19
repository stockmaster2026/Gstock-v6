import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. 系統配置與 CSS 優化 (針對 iPad 指揮中心) ---
st.set_page_config(page_title="V13.5 終極戰略指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { 
        display: flex; 
        overflow-x: auto; 
        padding: 15px 5px; 
        gap: 15px; 
        -webkit-overflow-scrolling: touch;
    }
    .h-wrapper::-webkit-scrollbar { height: 6px; }
    .h-wrapper::-webkit-scrollbar-thumb { background: #444; border-radius: 10px; }
    .sector-title { 
        color: #00ffcc; 
        font-size: 20px; 
        font-weight: bold; 
        margin-top: 25px; 
        border-left: 5px solid #00ffcc; 
        padding-left: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心指標運算 (V8.3 永久定錨邏輯) ---
def get_indicators(df):
    # 均線系統
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    return df

def calculate_v135_logic(df_slice, prev_row):
    """
    V13.5 核心邏輯：10分制共同分母
    F2(50%) | F3(30%) | F1(20%)
    """
    curr = df_slice.iloc[-1]
    p = float(curr['Close'])
    rsi = float(curr['RSI'])
    ma20 = float(curr['MA20'])
    vol_avg = df_slice['Volume'].tail(10).mean()
    vol_ratio = float(curr['Volume'] / vol_avg)
    
    # F2: 冠軍結構 (10分制) - 目標：Stage 2
    f2_std = 10 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    
    # F3: 主力籌碼 (10分制) - 目標：攻擊或洗盤
    # 攻擊：價漲量增 (>1.3x) | 洗盤：價跌量縮 (<0.8x)
    is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
    is_shakeout = (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (is_attack or is_shakeout) and (rsi > 45) else 0
    
    # F1: 技術指標 (10分制) - 目標：短線動能
    f1_std = 10 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    
    # 加權總分 (共同分母)
    total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
    
    # 精確指令系統
    if f2_std == 10:
        if total >= 9.5: 
            cmd = "🔥 三維共振：最強攻擊型態，積極重倉。"
        elif total >= 7.5: 
            cmd = "💪 主力掃貨：資金已進場，結構轉強，回測即買點。"
        elif total >= 6.5: 
            cmd = "⚠️ 技術虛漲：動能試探(蠢蠢欲動)，防回測。"
        else: 
            cmd = "💤 格局休眠：結構穩固但縮量，靜待主力表態。"
    else:
        cmd = "❌ 嚴禁介入：不符冠軍結構(非Stage 2)，觀望為主。"
        
    return f1_std, f2_std, f3_std, total, cmd

# --- 3. 數據獲取與緩存 ---
@st.cache_data(ttl=600)
def analyze_stock(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d")
        if df.empty or len(df) < 250: return None
        df = get_indicators(df).dropna()
        
        # 計算 5 日軌跡
        history_scores = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _ = calculate_v135_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history_scores.append(t_s)
            
        # 當前狀態
        l_f1, l_f2, l_f3, total, cmd = calculate_v135_logic(df, df.iloc[-2])
        
        return {
            "p": df.iloc[-1]['Close'], 
            "s": total, "cmd": cmd, 
            "f1": l_f1, "f2": l_f2, "f3": l_f3, 
            "history": history_scores
        }
    except:
        return None

# --- 4. 戰略版圖配置 (11 個完整板塊) ---
SECTORS = {
    "🌈 光通訊/存儲": ["SNDK", "MU", "AAOI", "LITE", "FN", "COHR"], 
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "🛰️ 國防安全": ["RCAT", "AVAV", "KTOS", "CRCL", "CRWV"],
    "🧬 生物醫療": ["HIMS", "SANA", "SNDX", "RXRX", "TEM", "CRSP"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "ARM", "TSM", "AVGO", "SNPS"], 
    "💻 AI 軟體/雲端": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "☁️ 網絡安全": ["CRWD", "PANW", "NET", "ZS", "FTNT"], 
    "📡 無線/邊緣": ["ONDS", "QCOM", "TMUS", "PI"],
    "🤖 機器人/製造": ["ASML", "AMAT", "LRCX", "ISRG", "TER"],
    "🚗 龍頭/消費": ["TSLA", "AMZN", "AAPL", "GOOGL", "META"]
}

# --- 5. UI 渲染主循環 ---
st.title("🛡️ 三維戰略指揮中心 V13.5")
st.markdown("### 📊 10 分制對帳單：F2(50%) | F3(30%) | F1(20%)")

# 側邊欄：單獨偵察
st.sidebar.title("🕹️ 戰術控制台")
search_ticker = st.sidebar.text_input("🔍 偵察代碼", "").upper()
if search_ticker:
    res = analyze_stock(search_ticker)
    if res:
        st.sidebar.success(f"標的: {search_ticker}")
        st.sidebar.info(f"🧱 結構: {res['f2']}/10\n🔥 籌碼: {res['f3']}/10\n✅ 指標: {res['f1']}/10\n🏆 總分: {res['s']:.1f}")
        st.sidebar.warning(f"指令: {res['cmd']}")

# 主頁面：11 板塊顯示
for sector_name, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector_name}</div>', unsafe_allow_html=True)
    html_cards = '<div class="h-wrapper">'
    
    for t in tickers:
        data = analyze_stock(t)
        if data:
            # 根據分數決定背景顏色
            bg_color = "#1E4620" if data['s'] >= 8 else "#46461E" if data['s'] >= 5 else "#461E1E"
            h_str = " | ".join([f"{x:.1f}" for x in data['history']])
            
            card = f"""
            <div style="background-color:{bg_color}; min-width:280px; max-width:280px; padding:15px; border-radius:12px; text-align:center; color:white; border:1px solid #555; margin-bottom:5px;">
                <h3 style="margin:0; font-size:16px;">{t}</h3>
                <p style="font-size:20px; font-weight:bold; margin:5px 0;">${data['p']:.2f}</p>
                <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:8px 0; font-size:11px; line-height:1.6;">
                    <div>🧱 冠軍結構(F2): <b>{data['f2']}/10</b></div>
                    <div>🔥 主力籌碼(F3): <b>{data['f3']}/10</b></div>
                    <div>✅ 技術指標(F1): <b>{data['f1']}/10</b></div>
                </div>
                <div style="background-color:#000; padding:8px 5px; border-radius:8px; margin:10px 0; color:#0f0; font-weight:bold; font-size:14px; letter-spacing:1px;">
                    {h_str}
                </div>
                <hr style="margin:8px 0; opacity:0.3;">
                <p style="font-size:15px; font-weight:bold; color:#FFD700; margin:0;">{data['s']:.1f} Pts</p>
                <p style="font-size:12px; margin-top:5px; height:40px; color:#fff; font-weight:bold; line-height:1.3;">{data['cmd']}</p>
            </div>
            """
            html_cards += card
            
    html_cards += '</div>'
    st.markdown(html_cards, unsafe_allow_html=True)

st.divider()
st.caption(f"數據最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V13.5 終極定錨版")

