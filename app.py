
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 系統環境與 iPad 專屬強化 CSS ---
st.set_page_config(page_title="V20.0 冠軍指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { 
        display: flex !important; flex-direction: row !important;
        overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; 
        -webkit-overflow-scrolling: touch !important; white-space: nowrap !important;
    }
    .h-wrapper::-webkit-scrollbar { height: 8px; }
    .h-wrapper::-webkit-scrollbar-thumb { background: #555; border-radius: 10px; }
    .sector-title { 
        color: #00ffcc; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0;
        border-left: 6px solid #00ffcc; padding-left: 15px;
    }
    .card-box {
        display: inline-block !important; vertical-align: top !important;
        min-width: 280px; max-width: 280px; padding: 15px; border-radius: 12px; 
        text-align: center; color: white; border: 1px solid #444;
        white-space: normal !important; flex: 0 0 auto !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心指標運算 (V20.0 冠軍定錨) ---
def calculate_v20_logic(df_slice, prev_row):
    curr = df_slice.iloc[-1]
    p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
    vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
    
    # 🥇 F2: 冠軍結構 (50%) - Stage 2 & VCP
    f2_cond = (curr['MA20'] > curr['MA50'])
    if 'MA200' in curr and not pd.isna(curr['MA200']):
        f2_cond = f2_cond and (curr['MA50'] > curr['MA200'])
    
    # 加入 1.5% 緩衝位判定
    f2_std = 10 if f2_cond and (p > ma20 * 0.985) else 0
    
    # 🔥 F3: 主力籌碼 (30%)
    is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
    is_washout = (p < prev_row['Close'] and vol_ratio < 0.8)
    f3_std = 10 if (is_attack or is_washout) and (rsi > 45) else 0
    
    # ✅ F1: 技術指標 (20%) - RSI 50-75
    f1_std = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) and (p > ma20) else 0
    
    total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
    
    if f2_std == 0:
        cmd, bg = "❌ 結構破壞：非第二階段，全速撤退。", "#641E1E"
    else:
        if total >= 9.5: cmd, bg = "🔥 冠軍共振：VCP突破，最強進攻。", "#1E4620"
        elif total >= 6.5: cmd, bg = "💪 跡象轉強：結構穩固，動能現身。", "#326432"
        elif total >= 4.5: cmd, bg = "💎 鑽石洗盤：主力蓄勢，縮量待發。" if is_washout else "💤 結構整理：等待主力表態。", "#64641E"
        else: cmd, bg = "⚠️ 觀察警戒：結構尚可，但不宜冒進。", "#46461E"
            
    return int(f1_std), int(f2_std), int(f3_std), int(total), cmd, bg

# --- 3. 數據分析函數 ---
@st.cache_data(ttl=600)
def analyze_v20(ticker):
    try:
        t_obj = yf.Ticker(ticker.strip().upper())
        df = t_obj.history(period="1y", timeout=15)
        if df.empty or len(df) < 50: return None
        
        # 簡易指標計算
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean() if len(df) >= 200 else df['MA50']
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        df = df.dropna()
        
        history = []
        for i in range(5, -1, -1):
            idx = len(df) - 1 - i
            _, _, _, t_s, _, _ = calculate_v20_logic(df.iloc[:idx+1], df.iloc[idx-1])
            history.append(int(t_s))
            
        f1, f2, f3, total, cmd, bg = calculate_v20_logic(df, df.iloc[-2])
        change = ((df.iloc[-1]['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
        trend = "⬆️" if history[-1] > history[-2] else "⬇️" if history[-1] < history[-2] else "—"
        
        return {"p": df.iloc[-1]['Close'], "ch": change, "s": total, "trend": trend, "cmd": cmd, "bg": bg, "f1": f1, "f2": f2, "f3": f3, "h": history[1:]}
    except: return None

# --- 4. 卡片模板 (關鍵字校準) ---
def render_card(t, data):
    ch_color = "#00FF00" if data['ch'] > 0 else "#FF4B4B"
    return f"""
    <div class="card-box" style="background-color: {data['bg']};">
        <h3 style="margin:0; font-size:16px;">{t} {data['trend']}</h3>
        <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{data['p']:.2f} <span style="font-size:14px; color:{ch_color};">({data['ch']:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0; font-size:12px; line-height:1.6;">
            <div>🥇 冠軍結構(F2)(50%): <b>{data['f2']}/10</b></div>
            <div>🔥 主力籌碼(F3)(30%): <b>{data['f3']}/10</b></div>
            <div>✅ 技術指標(F1)(20%): <b>{data['f1']}/10</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:8px 5px; border-radius:8px; font-family:monospace; font-size:16px; margin-bottom:12px; font-weight:bold;">
            {" | ".join([str(x) for x in data['h']])}
        </div>
        <hr style="margin:8px 0; opacity:0.2; border:none; border-top:1px solid #fff;">
        <p style="font-size:20px; font-weight:bold; color:#FFD700; margin:0;">{data['s']} Pts</p>
        <p style="font-size:12px; margin-top:5px; height:45px; line-height:1.3; font-weight:bold;">{data['cmd']}</p>
    </div>"""

# --- 5. UI 渲染：側邊欄與主版圖 ---
st.sidebar.title("🕹️ 戰術控制台")
search_ticker = st.sidebar.text_input("🔍 偵察代碼 (音譜欄位)", "").upper()
if search_ticker:
    res = analyze_v20(search_ticker)
    if res: st.sidebar.markdown(render_card(search_ticker, res), unsafe_allow_html=True)

st.title("🛡️ 三維戰略指揮中心 V20.0")
st.markdown("### 📊 全域對帳：F2(50%) | F3(30%) | F1(20%) [冠軍定錨版]")

SECTORS = {
    "🌌 量子計算": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "🌈 光通訊": ["AAOI", "LITE", "FN", "COHR", "AVGO"],
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "🛰️ 國防安全": ["RCAT", "AVAV", "KTOS", "CRCL", "BBAI"],
    "🧬 生物醫療": ["HIMS", "SANA", "SNDX", "RXRX", "TEM"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "TSM", "ARM", "MU", "WDC"], 
    "💻 AI 軟體/雲端": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "☁️ 網絡安全": ["CRWD", "PANW", "NET", "ZS", "FTNT"], 
    "🤖 機器人/製造": ["ASML", "AMAT", "LRCX", "ISRG", "TER"],
    "🚗 電動車/傳產": ["TSLA", "RIVN", "AMZN", "AAPL", "GOOGL", "META"]
}

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    results = []
    for t in tickers:
        d = analyze_v20(t)
        if d: results.append((t, d))
    results.sort(key=lambda x: x[1]['s'], reverse=True)
    cards_html = "".join([render_card(t, d) for t, d in results])
    st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)

st.divider()
st.caption(f"數據最後偵察: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V20.0 冠軍操盤手定錨版")
