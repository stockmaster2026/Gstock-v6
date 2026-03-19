
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統環境與 CSS 定錨 (針對 iPad 指揮中心優化) ---
st.set_page_config(page_title="V13.8 終極戰略指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { 
        display: flex; 
        overflow-x: auto; 
        padding: 10px 5px; 
        gap: 15px; 
        -webkit-overflow-scrolling: touch;
    }
    .h-wrapper::-webkit-scrollbar { height: 8px; }
    .h-wrapper::-webkit-scrollbar-thumb { background: #555; border-radius: 10px; }
    .sector-title { 
        color: #00ffcc; 
        font-size: 22px; 
        font-weight: bold; 
        margin: 25px 0 10px 0;
        border-left: 6px solid #00ffcc; 
        padding-left: 15px;
    }
    .card-box {
        min-width: 280px; 
        max-width: 280px; 
        padding: 15px; 
        border-radius: 12px; 
        text-align: center; 
        color: white; 
        border: 1px solid #444;
        flex-shrink: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心指標運算 (V8.3 永久定錨) ---
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

def calculate_v138_logic(df_slice, prev_row):
    """
    V13.8 核心邏輯：10分制共同分母
    公式：(F2 * 0.5) + (F3 * 0.3) + (F1 * 0.2)
    """
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    # F2: 結構 (10/10)
    f2_std = 10 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    # F3: 籌碼 (10/10) - 攻擊或洗盤
    f3_v = (p > prev_row['Close'] and vol_ratio > 1.3) or (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (f3_v and rsi > 45) else 0
    # F1: 技術指標 (10/10)
    f1_std = 10 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    
    total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
    
    # 指令系統
    if f2_std == 10:
        if total >= 9.5: cmd = "🔥 三維共振：最強攻擊，積極重倉。"
        elif total >= 7.5: cmd = "💪 主力掃貨：資金進場，回測即買點。"
        elif total >= 6.5: cmd = "⚠️ 技術虛漲：動能試探，嚴防回測。"
        else: cmd = "💤 格局休眠：結構穩固，縮量靜待噴發。"
    else:
        cmd = "❌ 嚴禁介入：結構破壞，觀望為主。"
        
    return f1_std, f2_std, f3_std, total, cmd

# --- 3. 數據分析 (含五日軌跡) ---
@st.cache_data(ttl=600)
def analyze_v138(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d")
        if df.empty or len(df) < 250: return None
        df = get_indicators(df).dropna()
        
        history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _ = calculate_v138_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history.append(t_s)
            
        f1, f2, f3, total, cmd = calculate_v138_logic(df, df.iloc[-2])
        return {"p": df.iloc[-1]['Close'], "s": total, "cmd": cmd, "f1": f1, "f2": f2, "f3": f3, "h": history}
    except:
        return None

# --- 4. 戰略版圖配置 (完整 11 板塊) ---
SECTORS = {
    "🌈 光通訊/存儲": ["SNDK", "MU", "AAOI", "LITE", "FN", "COHR"], 
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "🛰️ 國防安全": ["RCAT", "AVAV", "KTOS", "CRCL", "CRWV", "BBAI"],
    "🧬 生物醫療": ["HIMS", "SANA", "SNDX", "RXRX", "TEM", "CRSP"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "ARM", "TSM", "AVGO", "SNPS"], 
    "💻 AI 軟體/雲端": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "☁️ 網絡安全": ["CRWD", "PANW", "NET", "ZS", "FTNT"], 
    "📡 無線/邊緣": ["ONDS", "QCOM", "TMUS", "PI"],
    "🤖 機器人/製造": ["ASML", "AMAT", "LRCX", "ISRG", "TER"],
    "🚗 電動車/傳產": ["TSLA", "RIVN", "AMZN", "AAPL", "GOOGL", "META"]
}

# --- 5. UI 渲染循環 ---
st.title("🛡️ 三維戰略指揮中心 V13.8")
st.markdown("### 📊 全域對帳：F2(50%) | F3(30%) | F1(20%) [10分共同分母]")

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    
    # 建立橫向捲動容器
    container_html = '<div class="h-wrapper">'
    
    for t in tickers:
        res = analyze_v138(t)
        if res:
            # 決定卡片色調
            if res['f2'] == 0:
                bg = "#461E1E" # 紅色 (結構破壞)
                p_clr = "#FF4B4B"
            elif res['s'] >= 8:
                bg = "#1E4620" # 綠色 (強勢)
                p_clr = "#00FF00"
            else:
                bg = "#46461E" # 黃色 (盤整)
                p_clr = "#FFD700"
                
            h_line = " | ".join([f"{x:.1f}" for x in res['h']])
            
            card_html = f"""
            <div class="card-box" style="background-color: {bg};">
                <h3 style="margin:0; font-size:16px;">{t}</h3>
                <p style="font-size:20px; font-weight:bold; margin:5px 0;">${res['p']:.2f}</p>
                <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:8px 0; font-size:11px;">
                    <div>🧱 結構(F2): <b>{res['f2']}/10</b></div>
                    <div>🔥 籌碼(F3): <b>{res['f3']}/10</b></div>
                    <div>✅ 指標(F1): <b>{res['f1']}/10</b></div>
                </div>
                <div style="background-color:black; color:#0f0; padding:5px; border-radius:5px; font-family:monospace; font-size:12px; margin-bottom:10px;">
                    {h_line}
                </div>
                <hr style="margin:5px 0; opacity:0.2;">
                <p style="font-size:14px; font-weight:bold; color:{p_clr}; margin:0;">{res['s']:.1f} Pts</p>
                <p style="font-size:11px; margin-top:5px; height:35px; line-height:1.2; overflow:hidden;">{res['cmd']}</p>
            </div>
            """
            container_html += card_html
            
    container_html += '</div>'
    st.markdown(container_html, unsafe_allow_html=True)

st.divider()
st.caption(f"數據更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V13.8 終極定錨全量版")
