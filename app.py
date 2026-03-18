import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.4", layout="wide")
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; color: white; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 11 大美股戰略板塊 (純美股定案版) ---
SECTORS = {
    "🌈 光通訊": ["POET", "LITE", "COHR", "FN", "ACMR", "AAOI", "INFN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE", "QCI", "ARQQ"],
    "💾 存儲板塊": ["MU", "WDC", "STX", "PSTG", "NTAP", "SNDK"],
    "🛰️ 太空經濟": ["RKLB", "PLTR", "ASTS", "LUNR", "BKSY", "SPIR"],
    "💻 核心算力": ["NVDA", "AMD", "ARM", "TSM", "AVGO", "MRVL"],
    "⚡ 能源電力": ["VST", "CEG", "OKLO", "SMR", "TLN", "GEV"],
    "❄️ 液冷散熱": ["VRT", "SMCI", "MOD", "AAON", "JCI", "NVENT"],
    "🛡️ 國防科技": ["LMT", "RTX", "NOC", "LHX", "LDOS", "BWXT"],
    "🧬 生物 AI": ["RXRX", "SDGR", "EXAI", "ISRG", "AMGN", "VRTX"],
    "🤖 機器人": ["TSLA", "PATH", "SYM", "TER", "CGNX"],
    "📈 槓桿指數": ["SOXL", "TQQQ", "BITI", "SQQQ", "UPRO", "UVXY"]
}

# --- 3. 核心運算引擎 (F1, F2, F3 完整鎖定邏輯) ---
@st.cache_data(ttl=3600)
def run_v84_hardcore_analysis(ticker):
    try:
        # 抓取 300 天數據確保 MA200 與 52週數據完整
        df = yf.download(ticker, period="300d", interval="1d", progress=False)
        if df.empty or len(df) < 250: return None
        
        # A. 基礎指標計算
        close = df['Close']
        df['MA20'] = ta.sma(close, length=20)
        df['MA50'] = ta.sma(close, length=50)
        df['MA200'] = ta.sma(close, length=200)
        df['RSI'] = ta.rsi(close, length=14)
        macd = ta.macd(close)
        df['MACD_h'] = macd['MACDH_12_26_9']
        stoch = ta.stoch(df['High'], df['Low'], close)
        df['K'], df['D'] = stoch['STOCHk_14_3_3'], stoch['STOCHd_14_3_3']
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        vol_avg10 = df['Volume'].tail(10).mean()
        high_52 = df['High'].tail(252).max()
        low_52 = df['Low'].tail(252).min()
        
        # --- [F1: 技術指標共振] ---
        # 條件：站穩 MA20(1.5%緩衝) + MACD柱狀翻紅 + KD金叉 + RSI(50-70)
        f1 = (curr['Close'] > curr['MA20'] * 1.015) and \
             (curr['MACD_h'] > 0) and \
             (curr['K'] > curr['D']) and \
             (50 <= curr['RSI'] <= 70)
        
        # --- [F2: 冠軍操盤手價格結構] ---
        # 條件：Stage 2 (20>50>200) + MA200上升 + 離52週高點25%內 + 脫離底部30% + VCP波動收縮
        ma200_slope = df['MA200'].diff(20).iloc[-1]
        std_10 = df['Close'].tail(10).std()
        std_30 = df['Close'].tail(30).std()
        
        f2 = (curr['MA20'] > curr['MA50'] > curr['MA200']) and \
             (ma200_slope > 0) and \
             (curr['Close'] > high_52 * 0.75) and \
             (curr['Close'] > low_52 * 1.3) and \
             (std_10 < std_30)
        
        # --- [F3: 成交量過濾器 - 主力足跡] ---
        # 條件：(漲>1.3x 或 跌<0.8x 或 口袋支點) 且 20日吸籌>派發
        is_up = curr['Close'] > prev['Close']
        vol_ratio = curr['Volume'] / vol_avg10
        f3_standard = (is_up and vol_ratio > 1.3) or (not is_up and vol_ratio < 0.8)
        
        # 口袋支點判定 (當日量 > 過去10天任一跌日量)
        down_days = df.tail(10)[df.tail(10)['Close'] < df.tail(10)['Open']]
        max_down_vol = down_days['Volume'].max() if not down_days.empty else 0
        is_pocket_pivot = is_up and (curr['Volume'] > max_down_vol)
        
        # 20日吸籌天數比
        recent20 = df.tail(20)
        acc = len(recent20[(recent20['Close'] > recent20['Open']) & (recent20['Volume'] > vol_avg10)])
        dist = len(recent20[(recent20['Close'] < recent20['Open']) & (recent20['Volume'] > vol_avg10)])
        
        f3 = (f3_standard or is_pocket_pivot) and (acc >= dist)
        
        score = sum([1 for f in [f1, f2, f3] if f])
        return {
            "price": float(curr['Close']), "change": float(((curr['Close']-prev['Close'])/prev['Close'])*100),
            "score": score, "f1": f1, "f2": f2, "f3": f3, "vol_ratio": vol_ratio
        }
    except: return None

# --- 4. 指揮中心 UI 介面 ---
st.title("🛡️ 三維戰略指揮中心 V8.4")
st.markdown(f"**定錨邏輯：** F1(技術共振) | F2(VCP結構) | F3(主力足跡) | **更新：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# A. 戰略晴雨表
baro_cols = st.columns(len(SECTORS))
for i, (name, tickers) in enumerate(SECTORS.items()):
    with baro_cols[i]:
        res_list = [run_v84_hardcore_analysis(t) for t in tickers[:3] if run_v84_hardcore_analysis(t)]
        avg_s = sum([r['score'] for r in res_list])/len(res_list) if res_list else 0
        weather = "☀️" if avg_s >= 2.5 else "🌤️" if avg_s >= 1.5 else "🌧️"
        st.metric(name[:4], f"{avg_s:.1f}", weather)

st.divider()

# B. 板塊偵察區 (5-6 列橫排)
for sector, tickers in SECTORS.items():
    st.subheader(f"📍 {sector}")
    cols = st.columns(6)
    for i, t in enumerate(tickers):
        res = run_v84_hardcore_analysis(t)
        if res:
            with cols[i % 6]:
                # 燈號判定
                if res['score'] == 3: bg, lbl = "#1E4620", "🔥 全力進攻"
                elif res['score'] == 2: bg, lbl = "#46461E", "⚠️ 謹慎持有"
                else: bg, lbl = "#461E1E", "🚨 全力撤退"
                
                st.markdown(f"""
                <div style="background-color:{bg}; padding:12px; border-radius:10px; border:1px solid #444; text-align:center; min-height:170px;">
                    <h4 style="margin:0; color:#FFD700;">{t}</h4>
                    <p style="font-size:22px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:12px;">{res['change']:.1f}% | 量:{res['vol_ratio']:.1f}x</p>
                    <p style="font-size:11px; margin-top:5px; opacity:0.8;">F1:{'✅' if res['f1'] else '❌'} F2:{'✅' if res['f2'] else '❌'} F3:{'✅' if res['f3'] else '❌'}</p>
                    <hr style="margin:8px 0; opacity:0.2;">
                    <p style="font-size:13px; font-weight:bold;">{lbl}</p>
                </div>
                """, unsafe_allow_html=True)
                if t in ["POET", "IONQ"] and res['score'] < 2:
                    st.caption("🆘 趨勢觀察中")

if st.sidebar.button("🔄 強制刷新全域數據"):
    st.cache_data.clear()
    st.rerun()

