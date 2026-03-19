import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統環境與 iPad 專屬強化 CSS ---
st.set_page_config(page_title="V17.0 終極戰略指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { 
        display: flex !important; 
        flex-direction: row !important;
        overflow-x: auto !important; 
        padding: 15px 5px !important; 
        gap: 15px !important; 
        -webkit-overflow-scrolling: touch !important;
        white-space: nowrap !important;
    }
    .h-wrapper::-webkit-scrollbar { height: 8px; }
    .h-wrapper::-webkit-scrollbar-thumb { background: #555; border-radius: 10px; }
    .sector-title { 
        color: #00ffcc; 
        font-size: 24px; 
        font-weight: bold; 
        margin: 30px 0 15px 0;
        border-left: 6px solid #00ffcc; 
        padding-left: 15px;
    }
    .card-box {
        display: inline-block !important;
        vertical-align: top !important;
        min-width: 280px; 
        max-width: 280px; 
        padding: 15px; 
        border-radius: 12px; 
        text-align: center; 
        color: white; 
        border: 1px solid #444;
        white-space: normal !important;
        flex: 0 0 auto !important;
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

def calculate_v17_logic(df_slice, prev_row):
    """V17.0 核心邏輯：四階色彩與 10 分制"""
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    f2_std = 10 if (curr['MA20'] > curr['MA50'] > curr['MA200']) and (p > ma20 * 0.985) else 0
    is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
    is_shakeout = (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (is_attack or is_shakeout) and (rsi > 45) else 0
    f1_std = 10 if (rsi >= 50) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    
    total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
    
    # 指令與色彩邏輯校準
    if f2_std == 0:
        cmd, bg = "❌ 嚴禁介入：結構破壞，全速撤退。", "#641E1E" # 深紅
    else:
        if total >= 9.5: 
            cmd, bg = "🔥 三維共振：最強攻擊，積極重倉。", "#1E4620" # 深綠
        elif total >= 6.5: 
            cmd, bg = "💪 蓄勢轉強：跡象現身，回測即買點。", "#326432" # 淺綠
        elif total >= 4.5: 
            cmd, bg = "💤 極致洗盤：格局尚在，縮量待爆發。", "#64641E" # 淺紅/黃
        else:
            cmd, bg = "⚠️ 觀察警戒：動能渙散，不宜冒進。", "#46461E"
            
    return int(f1_std), int(f2_std), int(f3_std), int(total), cmd, bg

# --- 3. 數據與軌跡分析 ---
@st.cache_data(ttl=600)
def analyze_v17(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=15)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df).dropna()
        
        history = []
        for i in range(4, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _, _ = calculate_v17_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history.append(t_s)
            
        f1, f2, f3, total, cmd, bg = calculate_v17_logic(df, df.iloc[-2])
        return {"p": df.iloc[-1]['Close'], "s": total, "cmd": cmd, "bg": bg, "f1": f1, "f2": f2, "f3": f3, "h": history}
    except: return None

# --- 4. 11 個完整戰術板塊配置 (SNDK -> WDC) ---
SECTORS = {
    "🌈 光通訊/存儲": ["WDC", "MU", "AAOI", "LITE", "FN", "COHR"], 
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

# --- 5. UI 渲染：側邊欄 (音譜偵察) ---
st.sidebar.title("🕹️ 戰術控制台")
search_ticker = st.sidebar.text_input("🔍 偵察代碼 (音譜欄位)", "").upper()

if search_ticker:
    res = analyze_v17(search_ticker)
    if res:
        st.sidebar.markdown(f"""
        <div style="background-color:{res['bg']}; padding:15px; border-radius:10px; color:white; border:1px solid #555;">
            <h3 style="margin:0;">🎯 {search_ticker}</h3>
            <p style="font-size:22px; font-weight:bold;">&dollar;{res['p']:.2f}</p>
            <div style="text-align:left; font-size:12px; line-height:1.6; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0;">
                <div>🧱 格局(F2)(50%): <b>{res['f2']}/10</b></div>
                <div>🔥 主力(F3)(30%): <b>{res['f3']}/10</b></div>
                <div>✅ 指標(F1)(20%): <b>{res['f1']}/10</b></div>
            </div>
            <p style="font-size:18px; font-weight:bold; color:#FFD700; margin:0;">{res['s']} Pts</p>
            <p style="font-size:12px; font-weight:bold; margin-top:5px;">{res['cmd']}</p>
        </div>
        """, unsafe_allow_html=True)
        h_str = " | ".join([str(x) for x in res['h']])
        st.sidebar.markdown(f'<div style="background:black; color:#0f0; padding:10px; border-radius:8px; text-align:center; font-family:monospace; font-weight:bold; margin-top:10px;">{h_str}</div>', unsafe_allow_html=True)
    else:
        st.sidebar.error("⚠️ 無法獲取數據，請確認 Ticker 是否正確。")

# --- 6. UI 渲染：主版圖 (11 板塊) ---
st.title("🛡️ 三維戰略指揮中心 V17.0")
st.markdown("### 📊 全域對帳：F2(50%) | F3(30%) | F1(20%)")

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    sector_cards_html = []
    for t in tickers:
        data = analyze_v17(t)
        if data:
            h_line = " | ".join([str(x) for x in data['h']])
            card = f"""
            <div class="card-box" style="background-color: {data['bg']};">
                <h3 style="margin:0; font-size:16px;">{t}</h3>
                <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{data['p']:.2f}</p>
                <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0; font-size:12px; line-height:1.6;">
                    <div style="color:#ddd;">🧱 格局(F2)(50%): <b style="color:#fff;">{data['f2']}/10</b></div>
                    <div style="color:#ddd;">🔥 主力(F3)(30%): <b style="color:#fff;">{data['f3']}/10</b></div>
                    <div style="color:#ddd;">✅ 指標(F1)(20%): <b style="color:#fff;">{data['f1']}/10</b></div>
                </div>
                <div style="background-color:black; color:#0f0; padding:8px 5px; border-radius:8px; font-family:monospace; font-size:16px; margin-bottom:12px; font-weight:bold;">
                    {h_line}
                </div>
                <hr style="margin:8px 0; opacity:0.2; border:none; border-top:1px solid #fff;">
                <p style="font-size:18px; font-weight:bold; color:#FFD700; margin:0;">{data['s']} Pts</p>
                <p style="font-size:12px; margin-top:5px; height:45px; line-height:1.3; font-weight:bold; color:#fff;">{data['cmd']}</p>
            </div>"""
            sector_cards_html.append(card)
    st.markdown(f'<div class="h-wrapper">{" ".join(sector_cards_html)}</div>', unsafe_allow_html=True)

st.divider()
st.caption(f"偵察時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V17.0 終極色彩定錨版")

