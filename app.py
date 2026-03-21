
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 環境定錨 (完全保留 V26.0 原有配置) ---
st.set_page_config(page_title="V28.0 巔峰雙軌指揮中心", layout="wide")

# 保留你原本的 CSS 樣式，並微調 card-box 高度以容納新指標
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .h-wrapper { display: flex !important; overflow-x: auto !important; padding: 15px 5px !important; gap: 15px !important; -webkit-overflow-scrolling: touch !important; white-space: nowrap !important; }
    .sector-title { color: #00ffcc; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0; border-left: 6px solid #00ffcc; padding-left: 15px; }
    .card-box { display: inline-block !important; vertical-align: top !important; min-width: 300px; max-width: 300px; padding: 15px; border-radius: 12px; text-align: center; color: white; border: 1px solid #444; white-space: normal !important; flex: 0 0 auto !important; transition: transform 0.2s; }
    .card-box:hover { transform: scale(1.02); border-color: #00ffcc; }
</style>
""", unsafe_allow_html=True)

# --- 2. 舊有核心邏輯 (🥇 F2 冠軍結構 - 原封不動) ---
def calculate_v26_logic(df_slice, prev_row):
    try:
        curr = df_slice.iloc[-1]
        p = float(curr['Close'])
        rsi = float(curr['RSI']) if not pd.isna(curr['RSI']) else 50
        ma20 = float(curr['MA20'])
        vol_ratio = float(curr['Volume'] / df_slice['Volume'].tail(10).mean())
        
        f2_cond = (curr['MA20'] > curr['MA50'])
        if 'MA200' in curr and not pd.isna(curr['MA200']):
            f2_cond = f2_cond and (curr['MA50'] > curr['MA200'])
        f2_std = 10 if f2_cond and (p > ma20 * 0.985) else 0
        
        is_attack = (p > prev_row['Close'] and vol_ratio > 1.3)
        is_washout = (p < prev_row['Close'] and vol_ratio < 0.8)
        f3_std = 10 if (is_attack or is_washout) and (rsi > 45) else 0
        
        f1_std = 10 if (50 <= rsi <= 75) and (curr['MACD_h'] > 0) and (p > ma20) else 0
        
        total = (f2_std * 0.5) + (f3_std * 0.3) + (f1_std * 0.2)
        
        if f2_std == 0:
            cmd, bg = "❌ 結構破壞：撤退。", "#641E1E"
        else:
            if total >= 9.5: cmd, bg = "🔥 冠軍共振：最強進攻。", "#1E4620"
            elif total >= 6.5: cmd, bg = "💪 跡象轉強：動能現身。", "#326432"
            elif total >= 4.5: cmd, bg = "💎 鑽石洗盤：主力未走。" if is_washout else "💤 結構整理中。", "#64641E"
            else: cmd, bg = "⚠️ 觀察警戒：不宜冒進。", "#46461E"
        return int(f1_std), int(f2_std), int(f3_std), int(total), cmd, bg
    except:
        return 0, 0, 0, 0, "⚠️ 指標缺失", "#222"

# --- 3. 新增 AWI 氣象指標邏輯 (A-System 獨立計算) ---
def calculate_awi_indicator(df_slice):
    try:
        curr = df_slice.iloc[-1]
        # A1: 趨勢 (MACD 零上)
        a1_s = 10 if curr['MACD_h'] > 0 else 3
        # A2: 構造 (10/20/50MA 糾結)
        ma_list = [curr['MA10'], curr['MA20'], curr['MA50']]
        cv = np.std(ma_list) / np.mean(ma_list)
        a2_s = 10 if cv < 0.028 else (7 if cv < 0.048 else 3)
        # A3: 能量 (窒息量)
        v20_avg = df_slice['Volume'].tail(20).mean()
        a3_s = 10 if curr['Volume'] < v20_avg * 0.55 else (7 if curr['Volume'] < v20_avg * 0.85 else 4)
        
        total_awi = (a2_s * 0.4) + (a1_s * 0.3) + (a3_s * 0.3)
        icon = "🎆" if total_awi >= 9.0 else ("☀️" if total_awi >= 7.0 else ("☁️" if total_awi >= 5.0 else "🌫️"))
        return total_awi, icon
    except:
        return 0, "⚠️"

# --- 4. 數據偵察 (整合 V26.0 防禦版並擴充新指標) ---
@st.cache_data(ttl=300)
def analyze_v28(ticker):
    t_str = str(ticker).strip().upper()
    try:
        data_obj = yf.Ticker(t_str)
        df = data_obj.history(period="1y", interval="1d", timeout=12)
        if df.empty: return {"status": "error"}
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[df['Volume'] > 0].copy()
        
        # 舊指標
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean() if len(df) >= 200 else df['MA50']
        
        # 新指標擴充 (MA10 用於 AWI)
        df['MA10'] = df['Close'].rolling(10).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 0.001))))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean(); ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_h'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        
        df = df.ffill().dropna(subset=['Close', 'MA20', 'RSI'])
        
        # V26 舊累計 (5天)
        v26_h = []
        for i in range(5, -1, -1):
            h_idx = len(df) - 1 - i
            if h_idx < 1: continue
            _, _, _, t_s, _, _ = calculate_v26_logic(df.iloc[:h_idx+1], df.iloc[h_idx-1])
            v26_h.append(int(t_s))
            
        # V28 新氣象趨勢 (AWI-5)
        awi_h = []
        awi_sum = 0
        for i in range(-5, 0):
            awi_s, awi_i = calculate_awi_indicator(df.iloc[:len(df)+i+1])
            awi_h.append(awi_i)
            awi_sum += awi_s
            
        f1, f2, f3, total, cmd, bg = calculate_v26_logic(df, df.iloc[-2])
        change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        trend = "⬆️" if len(v26_h) >= 2 and v26_h[-1] > v26_h[-2] else "—"
        
        # AWI 55850 級別高分
        awi_acc_pts = int(awi_sum * 1117)
        
        return {"status": "ok", "p": df['Close'].iloc[-1], "ch": change, "s": total, "trend": trend, "cmd": cmd, "bg": bg, 
                "f1": f1, "f2": f2, "f3": f3, "v26_h": v26_h[-5:], "awi_h": awi_h, "awi_pts": awi_acc_pts}
    except:
        return {"status": "error"}

# --- 5. 渲染卡片模板 (V26 + V28 雙軌顯示) ---
def render_combined_card(t, data):
    if data["status"] == "error":
        return f'<div class="card-box" style="background-color:#222;"><h3 style="margin:0;">{t}</h3><p style="margin-top:20px;">📡 信號受干擾</p></div>'
    
    ch_color = "#00FF00" if data['ch'] > 0 else "#FF4B4B"
    awi_last_icon = data['awi_h'][-1]
    
    return f"""
    <div class="card-box" style="background-color: {data['bg']}; border: 1.5px solid #00ffcc;">
        <h3 style="margin:0; font-size:17px;">{t} {data['trend']} {awi_last_icon}</h3>
        <p style="font-size:22px; font-weight:bold; margin:5px 0;">&dollar;{data['p']:.2f} <span style="font-size:14px; color:{ch_color};">({data['ch']:+.2f}%)</span></p>
        
        <div style="text-align:left; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px; margin:10px 0; font-size:11px;">
            <div>🥇冠軍(F2): <b>{data['f2']}/10</b> | 籌碼(F3): <b>{data['f3']}/10</b></div>
            <div>✅技術(F1): <b>{data['f1']}/10</b> | V26總分: <b style="color:#00ffcc;">{data['s']} Pts</b></div>
        </div>
        
        <div style="background-color:black; color:#0f0; padding:5px; border-radius:6px; font-family:monospace; font-size:14px; margin-bottom:10px; font-weight:bold;">
            V26(h): {"|".join([str(x) for x in data['v26_h']])} <br>
            AWI(5): {" ".join(data['awi_h'])}
        </div>
        
        <hr style="margin:8px 0; opacity:0.2;">
        
        <p style="font-size:20px; font-weight:bold; color:#FFD700; margin:0;">{data['awi_pts']} AWI Pts</p>
        <p style="font-size:10px; height:32px; line-height:1.2; font-weight:bold; color:#fff; margin-top:5px;">{data['cmd']}</p>
    </div>"""

# --- 6. 主程式 (板塊與側邊欄 - 完全保留) ---
st.sidebar.title("🕹️ 雙系統控制台")
if st.sidebar.button("🧹 清除快取並刷新"):
    st.cache_data.clear()
    st.rerun()

search_ticker = st.sidebar.text_input("🔍 偵察自選代碼", "").upper()
if search_ticker:
    res = analyze_v28(search_ticker)
    st.sidebar.markdown(render_combined_card(search_ticker, res), unsafe_allow_html=True)

st.title("🛡️ 雙軌指揮中心 V28.0 (F-System + A-System)")
st.markdown("### 📊 全域對帳：🥇F2(50%) | 🔥F3(30%) | ✅F1(20%) + 🌌AWI 天氣指標")

SECTORS = {
    "🌌 量子計算": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "🌈 光通訊/關鍵組件": ["AXTI", "COHR", "LITE", "FN", "AAOI", "MRVL"],
    "🚀 太空經濟": ["PL", "RKLB", "ASTS", "LUNR", "SPIR"],
    "🛰️ 國防安全": ["RCAT", "AVAV", "KTOS", "CRCL", "BBAI"],
    "⚡ 能源電力": ["OKLO", "VST", "CEG", "NNE", "SMR"],
    "🌀 核心算力": ["NVDA", "AMD", "TSM", "ARM", "MU", "WDC"], 
    "💻 AI 軟體/雲端": ["PLTR", "MSFT", "SOUN", "SNOW", "CRM"],
    "🤖 機器人/製造": ["ASML", "AMAT", "LRCX", "ISRG", "TER"]
}

for sector, tickers in SECTORS.items():
    st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
    results = [ (t, analyze_v28(t)) for t in tickers ]
    # 這裡依照 AWI 得分排序，讓最強煙火排在前面
    results.sort(key=lambda x: (x[1].get('awi_pts', -1) if x[1]['status']=='ok' else -2), reverse=True)
    st.markdown(f'<div class="h-wrapper">{"".join([render_combined_card(t, d) for t, d in results])}</div>', unsafe_allow_html=True)

st.caption(f"數據最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | V28.0 雙強鎖定旗艦版")
