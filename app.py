import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統環境與 iPad 專屬橫向 CSS ---
st.set_page_config(page_title="V14.2 終極指揮中心", layout="wide")

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
        font-size: 24px; 
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

def calculate_v142_logic(df_slice, prev_row):
    """V14.2 核心邏輯：10分制共同分母"""
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
    
    if f2_std == 10:
        if total >= 9.5: cmd = "🔥 三維共振：最強攻擊型態，重倉持有。"
        elif total >= 7.5: cmd = "💪 主力掃貨：資金已進場，結構轉強，回測即買點。"
        elif total >= 6.5: cmd = "⚠️ 技術虛漲：動能試探(蠢蠢欲動)，防回測。"
        else: cmd = "💤 格局休眠：結構穩固，縮量靜待爆發。"
    else:
        cmd = "❌ 嚴禁介入：結構破壞(非Stage 2)，觀望為主。"
        
    return f1_std, f2_std, f3_std, total, cmd

# --- 3. 數據與軌跡分析 ---
@st.cache_data(ttl=600)
def analyze_v142(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df).dropna()
        
        history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _ = calculate_v142_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history.append(t_s)
            
        f1, f2, f3, total, cmd = calculate_v142_logic(df, df.iloc[-2])
        return {"p": df.iloc[-1]['Close'], "s": total, "cmd": cmd, "f1": f1, "f2": f2, "f3": f3, "h": history}
    except: return None

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

# --- 5. UI 渲染 (V14.2 安全機制) ---
st.title("🛡️ 三維戰略指揮中心 V14.2")
st.markdown("### 📊 全域對帳：F2(50%) | F3(30%) | F1(20%) [標準10分制]")

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    
    sector_cards = []
    for t in tickers:
        data = analyze_v142(t)
        if data:
            # 顏色邏輯
            if data['f2'] == 0:
                bg = "#461E1E"; p_clr = "#FF4B4B"
            elif data['s'] >= 8:
                bg = "#1E4620"; p_clr = "#00FF00"
            else:
                bg = "#46461E"; p_clr = "#FFD700"
                
            h_line = " | ".join([f"{x:.1f}" for x in data['h']])
            
            # 🌟 核心防禦：使用 &dollar; 避免 Markdown 解析錯誤
            card_html = f"""
            <div class="card-box" style="background-color: {bg};">
                <h3 style="margin:0; font-size:16px;">{t}</h3>
                <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{data['p']:.2f}</p>
                <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0; font-size:12px; line-height:1.6;">
                    <div>🧱 結構(F2): <b>{data['f2']}/10</b></div>
                    <div>🔥 籌碼(F3): <b>{data['f3']}/10</b></div>
                    <div>✅ 指標(F1): <b>{data['f1']}/10</b></div>
                </div>
                <div style="background-color:black; color:#0f0; padding:8px 5px; border-radius:8px; font-family:monospace; font-size:14px; margin-bottom:12px;">
                    {h_line}
                </div>
                <hr style="margin:8px 0; opacity:0.2;">
                <p style="font-size:16px; font-weight:bold; color:{p_clr}; margin:0;">{data['s']:.1f} Pts</p>
                <p style="font-size:12px; margin-top:5px; height:45px; line-height:1.3; font-weight:bold;">{data['cmd']}</p>
            </div>
            """
            sector_cards.append(card_html)
            
    # 將所有卡片拼接後一次性渲染，並確保容器標籤正確閉合
    full_row_html = f'<div class="h-wrapper">{" ".join(sector_cards)}</div>'
    st.markdown(full_row_html, unsafe_allow_html=True)

st.divider()
st.caption(f"偵察時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V14.2 終極全量修復版")

