
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 核心指標運算 (科學門檻定錨) ---
def get_indicators(df):
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

@st.cache_data(ttl=600)
def analyze_v87_scientific(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="300d", timeout=20)
        if df.empty or len(df) < 250: return None
        df = get_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- 數據定義 ---
        price = float(curr['Close'])
        ma20 = float(curr['MA20'])
        rsi = float(curr['RSI'])
        vol_ratio = float(curr['Volume'] / df['Volume'].tail(10).mean())
        high_52 = df['High'].tail(252).max()

        # --- F2: 價格結構 (50% - 核心門檻) ---
        # 科學邏輯：只要跌破 MA20 (生命線) 1.5%，結構直接判定失效 (0分)
        is_stage2 = (curr['MA20'] > curr['MA50'] > curr['MA200'])
        on_ma20 = price > ma20 * 0.985
        f2_score = 5 if (is_stage2 and on_ma20) else 0
        diag_f2 = "🛡️ 結構完美 (趨勢中)" if f2_score == 5 else "🧱 結構崩壞 (探底中)" if not on_ma20 else "⏳ 趨勢不明"

        # --- F3: 主力足跡 (30%) ---
        # 科學邏輯：若 RSI < 45，代表沒人在接，量縮也不算洗盤
        is_up = price > prev['Close']
        f3_valid = (is_up and vol_ratio > 1.2) or (not is_up and vol_ratio < 0.8)
        f3_score = 3 if (f3_valid and rsi > 45) else 0
        diag_f3 = "🔥 主力在場 (動能強)" if f3_score == 3 else "📉 籌碼散亂 (無人接盤)"

        # --- F1: 技術共振 (20%) ---
        # 科學邏輯：RSI < 50 為空頭區，MACD 必須翻紅
        f1_valid = (rsi >= 50) and (curr['MACD_h'] > 0) and (price > ma20)
        f1_score = 2 if f1_valid else 0
        diag_f1 = "✅ 買點浮現" if f1_valid else "📉 弱勢探底" if rsi < 50 else "⚠️ 調整等待"

        # --- 總分與解釋 ---
        total_score = f1_score + f2_score + f3_score
        
        # 白話分數解釋
        if total_score >= 8:
            meaning = "強勢進攻：地基穩、動能強、買點到。"
            action = "🔥 全力進攻"
        elif total_score >= 5:
            meaning = "多頭防守：結構還在，但短線動能不足。"
            action = "🟡 試探建倉"
        else:
            meaning = f"危險訊號：{'RSI探底' if rsi < 50 else '結構損毀'}，嚴禁入內。"
            action = "❌ 權利撤退"

        return {
            "price": price, "rsi": rsi, "score": total_score, "action": action,
            "meaning": meaning, "df1": diag_f1, "df2": diag_f2, "df3": diag_f3,
            "change": ((price-prev['Close'])/prev['Close'])*100
        }
    except: return None

# --- UI 渲染 ---
st.set_page_config(page_title="V8.7 科學定錨系統", layout="wide")
st.title("🛡️ 三維戰略指揮中心 V8.7")

# 板塊配置
SECTORS = {
    "🌈 光通訊核心": ["POET", "LITE", "COHR", "FN"],
    "🌀 量子計算": ["IONQ", "RGTI", "QUBT", "D-WAVE"],
    "🚀 太空/算力": ["RKLB", "PLTR", "NVDA", "AMD"]
}

# 1. 板塊晴雨表 (白話註解)
st.subheader("📊 板塊戰略強度指標")
st.caption("※ 分數由 F1(20%) + F2(50%) + F3(30%) 組成，RSI < 50 會觸發連動扣分。")
cols = st.columns(len(SECTORS))
for i, (name, tickers) in enumerate(SECTORS.items()):
    results = [analyze_v87_scientific(t) for t in tickers]
    valid = [r for r in results if r is not None]
    avg_score = sum([r['score'] for r in valid]) / len(valid) if valid else 0
    weather = "☀️" if avg_score >= 8 else "🌤️" if avg_score >= 5 else "🌧️"
    cols[i].metric(name, f"{avg_score:.1f} Pts", weather)

st.divider()

# 2. 個股科學診斷卡
for name, tickers in SECTORS.items():
    st.header(name)
    grid = st.columns(6)
    for j, t in enumerate(tickers):
        res = analyze_v87_scientific(t)
        with grid[j % 6]:
            if res:
                bg = "#1E4620" if res['score'] >= 8 else "#46461E" if res['score'] >= 5 else "#461E1E"
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; text-align:center; color:white; border:1px solid #555;">
                    <h3 style="margin:0; color:#FFD700;">{t}</h3>
                    <p style="font-size:24px; font-weight:bold; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:12px; color:#AAA;">RSI: {res['rsi']:.1f} | {res['change']:.1f}%</p>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:11px; text-align:left;"><b>F2 階段：</b>{res['df2']}</p>
                    <p style="font-size:11px; text-align:left;"><b>F3 階段：</b>{res['df3']}</p>
                    <p style="font-size:11px; text-align:left;"><b>F1 階段：</b>{res['df1']}</p>
                    <hr style="margin:8px 0; opacity:0.3;">
                    <p style="font-size:16px; font-weight:bold; color:#FFD700;">總分：{res['score']} Pts</p>
                    <p style="font-size:10px; font-style:italic;">{res['meaning']}</p>
                    <p style="font-size:14px; margin-top:5px;"><b>{res['action']}</b></p>
                </div>
                """, unsafe_allow_html=True)
