import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- 1. 環境定錨 (完全保留 V26.0 樣式) ---
st.set_page_config(page_title="V28.1 巔峰雙軌指揮中心", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; -webkit-overflow-scrolling: touch !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0; border-left: 6px solid #00ffcc; padding-left: 15px; }
    .card-box { display: inline-block !important; vertical-align: top !important; min-width: 300px; max-width: 300px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; white-space: normal !important; flex: 0 0 auto !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. 舊有核心邏輯 (F1/F2/F3) ---
def calculate_v26_logic(df_slice, prev_row):
    try:
        curr = df_slice.iloc[-1]
        p = float(curr['Close'])
        rsi = float(curr['RSI']) if not pd.isna(curr['RSI']) else 50
        ma20 = float(curr['MA20'])
        vol_avg = df_slice['Volume'].tail(10).mean()
        vol_ratio = float(curr['Volume'] / vol_avg) if vol_avg > 0 else 1
        
        f2_cond = (curr['MA20'] > curr['MA50'])
        if 'MA200' in curr and not pd.isna(curr['MA200']):
            f2_cond = f2_cond and (curr['MA50'] > curr['MA200'])
        f2_std = 10 if f2_cond and (p > ma20 * 0.985) else 0
        
        is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
        is_washout = (p < prev_row['Close'] and vol_ratio < 0.8)
        f3_std = 10 if (is_attack or is_washout) and (rsi > 45) else 0
        f1_std = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) and (p > ma20) else 0
        
        total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
        
        if f2_std == 0: cmd, bg = "❌ 結構破壞：撤退。", "#641E1E"
        else:
            if total >= 9.5: cmd, bg = "🔥 冠軍共振：最強進攻。", "#1E4620"
            elif total >= 6.5: cmd, bg = "💪 跡象轉強：動能現身。", "#326432"
            elif total >= 4.5: cmd, bg = "💎 鑽石洗盤：主力未走。" if is_washout else "💤 結構整理中。", "#64641E"
            else: cmd, bg = "⚠️ 觀察警戒：不宜冒進。", "#46461E"
        return int(f1_std), int(f2_std), int(f3_std), int(total), cmd, bg
    except:
        return 0, 0, 0, 0, "⚠️ 指標缺失", "#222"

# --- 3. 新增 AWI 氣象邏輯 ---
def calculate_awi_indicator(df_slice):
    try:
        curr = df_slice.iloc[-1]
        # A2: 構造糾結 (40%)
        ma_list = [curr['MA10'], curr['MA20'], curr['MA50']]
        cv = np.std(ma_list) / np.mean(ma_list)
        a2_s = 10 if cv < 0.03 else (7 if cv < 0.05 else 3)
        # A3: 能量窒息 (30%)
        v20 = df_slice['Volume'].tail(20).mean()
        a3_s = 10 if curr['Volume'] < v20 * 0.55 else (7 if curr['Volume'] < v20 * 0.85 else 4)
        # A1: 趨勢對齊 (30%)
        a1_s = 10 if curr['MACD_h'] > 0 else 3
        
        total_awi = (a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3)
        icon = "🎆" if total_awi >= 9.0 else ("☀️" if total_awi >= 7.0 else ("☁️" if total_awi >= 5.0 else "🌫️"))
        return total_awi, icon
    except:
        return 0, "⚠️"

# --- 4. 數據偵察 (穩定性增強版) ---
@st.cache_data(ttl=600)
def analyze_v28(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, timeout=15)
        if df.empty or len(df) < 60: return {"status": "error"}
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[df['Volume'] > 0].copy()

        # 技術指標計算
        df['MA10'] = df['Close'].rolling(10).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean() if len(df) >= 200 else df['MA50']
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-6))))
        
        ema12 = df['Close'].ewm(span=12, adjust=False).mean(); ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        df = df.dropna(subset=['MA50', 'RSI', 'MACD_h'])

        # 趨勢與氣象累積
        v26_h, awi_h, awi_sum = [], [], 0
        for i in range(5, 0, -1):
            idx = len(df) - i
            if idx < 1: continue
            _, _, _, t_s, _, _ = calculate_v26_logic(df.iloc[:idx+1], df.iloc[idx-1])
            v26_h.append(int(t_s))
            ascore, aicon = calculate_awi_indicator(df.iloc[:idx+1])
            awi_h.append(aicon); awi_sum += ascore
            
        f1, f2, f3, total, cmd, bg = calculate_v26_logic(df, df.iloc[-2])
        change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        awi_pts = int(awi_sum * 1117)
        
        return {"status": "ok", "p": float(df['Close'].iloc[-1]), "ch": float(change), "s": total, "cmd": cmd, "bg": bg, 
                "f1": f1, "f2": f2, "f3": f3, "v26_h": v26_h, "awi_h": awi_h, "awi_pts": awi_pts}
    except:
        return {"status": "error"}

# --- 5. 渲染卡片 ---
def render_combined_card(t, data):
    if data["status"] == "error":
        return f'<div class="card-box" style="background-color:#222;"><h3>{t}</h3><p>📡 數據抓取失敗</p></div>'
    
    ch_color = "#00FF00" if data['ch'] > 0 else "#FF4B4B"
    return f"""
    <div class="card-box" style="background-color: {data['bg']}; border: 1.5px solid #00ffcc;">
        <h3 style="margin:0;">{t} {data['awi_h'][-1]}</h3>
        <p style="font-size:22px; font-weight:bold;">&dollar;{data['p']:.2f} <span style="font-size:14px; color:{ch_color};">({data['ch']:+.2f}%)</span></p>
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; font-size:11px;">
            <div>F2結構: <b>{data['f2']}</b> | F3籌碼: <b>{data['f3']}</b> | F1技術: <b>{data['f1']}</b></div>
        </div>
        <div style="background-color:black; color:#0f0; padding:5px; border-radius:6px; font-family:monospace; font-size:13px; margin:10px 0;">
            V26: {"|".join(map(str, data['v26_h']))} <br> AWI: {" ".join(data['awi_h'])}
        </div>
        <p style="font-size:20px; font-weight:bold; color:#FFD700; margin:0;">{data['awi_pts']} AWI Pts</p>
        <p style="font-size:10px; font-weight:bold; color:#fff; height:35px;">{data['cmd']}</p>
    </div>"""

# --- 6. 主程式板塊 ---
st.sidebar.title("🕹️ 控制中心")
if st.sidebar.button("🧹 刷新數據"):
    st.cache_data.clear()
    st.rerun()

SECTORS = {
    "🌈 光通訊": ["AXTI", "COHR", "LITE", "MRVL"],
    "🌀 核心算力": ["NVDA", "AMD", "TSM", "ARM"],
    "🌌 量子計算": ["IONQ", "RGTI", "QBTS"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "SMR"]
}

st.title("🛡️ 雙軌指揮中心 V28.1")

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    cols_data = []
    for t in tickers:
        res = analyze_v28(t)
        cols_data.append((t, res))
    
    # 依 AWI 分數排序
    cols_data.sort(key=lambda x: (x[1].get('awi_pts', -1) if x[1]['status']=='ok' else -2), reverse=True)
    st.markdown(f'<div class="h-wrapper">{"".join([render_card(t, d) for t, d in cols_data])}</div>', unsafe_allow_html=True)

