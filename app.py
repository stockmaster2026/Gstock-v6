import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統配置與針對 iPad 的 CSS 定錨 ---
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
    權重公式：(F2*0.5) + (F3*0.3) + (F1*0.2)
    """
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    # F2: 結構 (10/10) - Stage 2 冠軍格局判定
    f2_std = 10 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    # F3: 籌碼 (10/10) - 攻擊或洗盤判定
    f3_v = (p > prev_row['Close'] and vol_ratio > 1.3) or (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (f3_v and rsi > 45) else 0
    # F1: 技術指標 (10/10) - 短線動能判定
    f1_std = 10 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    
    # 共同分母總分計算
    total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
    
    # 精確指令系統
    if f2_std == 10:
        if total >= 9.5: cmd = "🔥 三維共振：最強攻擊型態，積極重倉。"
        elif total >= 7.5: cmd = "💪 主力掃貨：資金已進場，結構轉強，回測即買點。"
        elif total >= 6.5: cmd = "⚠️ 技術虛漲：動能試探(蠢蠢欲動)，但缺彈藥，防回測。"
        else: cmd = "💤 格局休眠：結構穩固但縮量，靜待主力表態。"
    else:
        cmd = "❌ 嚴禁介入：不符冠軍結構(非Stage 2)，觀望為主。"
        
    return f1_std, f2_std, f3_std, total, cmd

# --- 3. 數據分析與五日軌跡 (V13.8 校準) ---
@st.cache_data(ttl=600)
def analyze_stock_v138(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="350d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df).dropna()
        
        # 計算 5 日戰略軌跡
        history_scores = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _ = calculate_v138_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history_scores.append(t_s)
            
        # 獲取最新狀態
        f1, f2, f3, total, cmd = calculate_v138_logic(df, df.iloc[-2])
        
        return {
            "p": df.iloc[-1]['Close'], 
            "s": total, "cmd": cmd, 
            "f1": f1, "f2": f2, "f3": f3, 
            "h": history_scores
        }
    except:
        return None

# --- 4. 11 個全戰術板塊部署 (含關注標的與智慧補強) ---
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

# --- 5. UI 渲染主循環 ---
st.title("🛡️ 三維戰略指揮中心 V13.8")
st.markdown("### 📊 10 分制對帳單：F2(50%) | F3(30%) | F1(20%)")

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    
    # 建立橫向捲動容器 HTML
    row_html = '<div class="h-wrapper">'
    
    for t in tickers:
        data = analyze_stock_v138(t)
        if data:
            # 根據得分定色
            if data['f2'] == 0:
                bg_color = "#461E1E" # 紅色 (結構破壞)
                pts_color = "#FF4B4B"
            elif data['s'] >= 8:
                bg_color = "#1E4620" # 綠色 (強勢進攻)
                pts_color = "#00FF00"
            else:
                bg_color = "#46461E" # 黃色 (盤整蓄勢)
                pts_color = "#FFD700"
                
            h_str = " | ".join([f"{x:.1f}" for x in data['h']])
            
            # 生成單張卡片 HTML
            card_html = f"""
            <div style="background-color:{bg_color}; min-width:280px; max-width:280px; padding:15px; border-radius:12px; text-align:center; color:white; border:1px solid #555; margin-bottom:5px; flex-shrink:0;">
                <h3 style="margin:0; font-size:16px;">{t}</h3>
                <p style="font-size:20px; font-weight:bold; margin:5px 0;">${data['p']:.2f}</p>
                <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:8px 0; font-size:11px; line-height:1.6;">
                    <div>🧱 格局(F2): <b>{data['f2']}/10</b></div>
                    <div>🔥 主力(F3): <b>{data['f3']}/10</b></div>
                    <div>✅ 指標(F1): <b>{data['f1']}/10</b></div>
                </div>
                <div style="background-color:black; padding:10px 5px; border-radius:8px; margin:10px 0; color:#0f0; font-weight:bold; font-size:18px; letter-spacing:2px; font-family:monospace;">
                    {h_str}
                </div>
                <hr style="margin:8px 0; opacity:0.3;">
                <p style="font-size:15px; font-weight:bold; color:{pts_color}; margin:0;">{data['s']:.1f} Pts</p>
                <p style="font-size:12px; margin-top:5px; height:45px; color:#fff; font-weight:bold; line-height:1.3; overflow:hidden;">{data['cmd']}</p>
            </div>
            """
            row_html += card_html
            
    row_html += '</div>'
    
    # 🌟 核心修復：使用單一個 markdown 渲染整個板塊，防止代碼溢出
    st.markdown(row_html, unsafe_allow_html=True)

st.divider()
st.caption(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V13.8 終極定錨全量版")

