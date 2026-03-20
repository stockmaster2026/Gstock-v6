
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 環境定錨 ---
st.set_page_config(page_title="V22.0 冠軍指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; -webkit-overflow-scrolling: touch !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0; border-left: 6px solid #00ffcc; padding-left: 15px; }
    .card-box { display: inline-block !important; vertical-align: top !important; min-width: 280px; max-width: 280px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; white-space: normal !important; flex: 0 0 auto !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心邏輯 (🥇 F2 定錨) ---
def calculate_v22_logic(df_slice, prev_row):
    try:
        curr = df_slice.iloc[-1]
        p, rsi, ma20 = float(curr['Close']), float(curr['RSI']), float(curr['MA20'])
        vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
        
        # F2: 🥇 冠軍結構 (Stage 2 + 1.5% Buffer)
        f2_cond = (curr['MA20'] > curr['MA50'])
        if 'MA200' in curr and not pd.isna(curr['MA200']):
            f2_cond = f2_cond and (curr['MA50'] > curr['MA200'])
        f2_std = 10 if f2_cond and (p > ma20 * 0.985) else 0
        
        # F3: 🔥 主力籌碼
        is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
        is_washout = (p < prev_row['Close'] and vol_ratio < 0.8)
        f3_std = 10 if (is_attack or is_washout) and (rsi > 45) else 0
        
        # F1: ✅ 技術指標 (RSI 50-75)
        f1_std = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) and (p > ma20) else 0
        
        total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
        
        if f2_std == 0:
            cmd, bg = "❌ 結構破壞：非第二階段，全速撤退。", "#641E1E"
        else:
            if total >= 9.5: cmd, bg = "🔥 冠軍共振：VCP突破，最強進攻。", "#1E4620"
            elif total >= 6.5: cmd, bg = "💪 跡象轉強：結構穩固，動能現身。", "#326432"
            elif total >= 4.5: cmd, bg = "💎 鑽石洗盤：縮量待發。" if is_washout else "💤 結構整理：等待主力。", "#64641E"
            else: cmd, bg = "⚠️ 觀察警戒：動能渙散，不宜冒進。", "#46461E"
        return int(f1_std), int(f2_std), int(f3_std), int(total), cmd, bg
    except:
        return 0, 0, 0, 0, "⚠️ 數據計算異常", "#222"

# --- 3. 數據偵察 (強化穩定性) ---
@st.cache_data(ttl=600)
def analyze_v22(ticker):
    try:
        t_str = str(ticker).strip().upper()
        t_obj = yf.Ticker(t_str)
        # 縮短為 1.5y，平衡 MA200 需求與載入速度
        df = t_obj.history(period="1.5y", timeout=10)
        if df.empty or len(df) < 50: return {"status": "error"}
        
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean() if len(df) >= 200 else df['MA50']
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean(); ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        
        df_clean = df.dropna()
        if len(df_clean) < 5: return {"status": "error"}
        
        history = []
        for i in range(5, -1, -1):
            idx = len(df_clean) - 1 - i
            _, _, _, t_s, _, _ = calculate_v22_logic(df_clean.iloc[:idx+1], df_clean.iloc[idx-1])
            history.append(int(t_s))
            
        f1, f2, f3, total, cmd, bg = calculate_v22_logic(df_clean, df_clean.iloc[-2])
        change = ((df_clean.iloc[-1]['Close'] - df_clean.iloc[-2]['Close']) / df_clean.iloc[-2]['Close']) * 100
        trend = "⬆️" if history[-1] > history[-2] else "⬇️" if history[-1] < history[-2] else "—"
        
        return {"status": "ok", "p": df_clean.iloc[-1]['Close'], "ch": change, "s": total, "trend": trend, "cmd": cmd, "bg": bg, "f1": f1, "f2": f2, "f3": f3, "h": history[1:]}
    except:
        return {"status": "error"}

# --- 4. 渲染模板 ---
def render_card(t, data):
    if data["status"] == "error":
        return f'<div class="card-box" style="background-color:#222; opacity:0.6;"><h3 style="margin:0;">{t}</h3><p style="margin-top:20px;">📡 偵察信號中斷</p></div>'
    
    ch_color = "#00FF00" if data['ch'] > 0 else "#FF4B4B"
    return f"""
    <div class="card-box" style="background-color: {data['bg']};">
        <h3 style="margin:0; font-size:16px;">{t} {data['trend']}</h3>
        <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{data['p']:.2f} <span style="font-size:14px; color:{ch_color};">({data['ch']:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0; font-size:11px; line-height:1.6;">
            <div>🥇 冠軍結構(F2)(50%): <b>{data['f2']}/10</b></div>
            <div>🔥 主力籌碼(F3)(30%): <b>{data['f3']}/10</b></div>
            <div>✅ 技術指標(F1)(20%): <b>{data['f1']}/10</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:5px; border-radius:6px; font-family:monospace; font-size:15px; margin-bottom:10px; font-weight:bold;">{" | ".join([str(x) for x in data['h']])}</div>
        <hr style="margin:8px 0; opacity:0.2; border-top:1px solid #fff;">
        <p style="font-size:20px; font-weight:bold; color:#FFD700; margin:0;">{data['s']} Pts</p>
        <p style="font-size:11px; margin-top:5px; height:40px; line-height:1.2; font-weight:bold; color:#fff;">{data['cmd']}</p>
    </div>"""

# --- 5. 主程式 ---
st.sidebar.title("🕹️ 戰術控制台")
search_ticker = st.sidebar.text_input("🔍 偵察代碼 (如 IONQ)", "").upper()
if search_ticker:
    res = analyze_v22(search_ticker)
    st.sidebar.markdown(render_card(search_ticker, res), unsafe_allow_html=True)

st.title("🛡️ 三維戰略指揮中心 V22.0")
st.markdown("### 📊 全域對帳：F2(50%) | F3(30%) | F1(20%)")

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
    st.subheader(sector) # 使用標準 subheader 確保板塊標題一定會出現
    results = []
    for t in tickers:
        d = analyze_v22(t)
        results.append((t, d))
    
    # 安全排序：確保 error 狀態排在最後，不干擾顯示
    results.sort(key=lambda x: (x[1].get('s', -1) if x[1]['status']=='ok' else -2), reverse=True)
    
    cards_html = "".join([render_card(t, d) for t, d in results])
    st.markdown(f'<div class="h-wrapper">{cards_html}</div>', unsafe_allow_html=True)

st.caption(f"數據更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V22.0 穩定版")
