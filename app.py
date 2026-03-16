
import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- 頁面配置 ---
st.set_page_config(page_title="三維戰略指揮中心 V8.2", layout="wide")

# --- 1. 核心資料庫 (40檔標的，解決空虛感) ---
SECTORS = {
    "💾 存儲板塊 (Storage)": ["MU", "WDC", "STX", "PSTG", "NTAP", "WRLD", "SMCI", "ANET", "AVGO"],
    "🛰️ 太空板塊 (Space)": ["RKLB", "PLTR", "ASTS", "LUNR", "BKSY", "SPCE", "SPIR", "MAXR", "MDA"],
    "🚀 戰略黑馬 (Dark Horse)": ["POET", "SOXL", "TQQQ", "IONQ", "RGTI", "HIMS", "CLOV", "OKLO", "SMR"],
    "💻 核心算力 (AI Core)": ["NVDA", "AMD", "ARM", "TSM", "ALAB", "MRVL", "VRT", "QCOM", "DELL"],
    "⚡ 電力能源 (Power)": ["VST", "CEG", "TLN", "nE", "GEV", "CAMT"]
}

# --- 2. 數據抓取與分析核心 (修復報錯 + 加入成交量) ---
def analyze_ticker(ticker):
    try:
        # 修正：確保輸入不為空
        if not ticker or not isinstance(ticker, str): return None
        
        stock = yf.Ticker(ticker.strip().upper())
        df = stock.history(period="60d")
        
        # 修正：防呆檢查資料長度
        if df.empty or len(df) < 22: return None
        
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        
        # 成交量分析
        avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
        curr_vol = df['Volume'].iloc[-1]
        vol_ratio = curr_vol / avg_vol
        
        # 三維信號判定
        s1 = curr > ma20         # 1. 站上生命線
        s2 = curr > prev         # 2. 短線動能 (今日上漲)
        s3 = ma20 > ma50         # 3. 趨勢向上
        
        score = sum([s1, s2, s3])
        return {
            "price": curr,
            "change": ((curr - prev) / prev) * 100,
            "score": score,
            "vol_ratio": vol_ratio,
            "signals": [s1, s2, s3]
        }
    except Exception:
        return None

# --- 3. 主界面 UI ---
st.title("🛡️ 三維戰略指揮中心 V8.2")

# --- A. 戰略晴雨表 (熱門板塊掃描) ---
st.subheader("🌡️ 戰略晴雨表 (板塊熱力)")
baro_cols = st.columns(len(SECTORS))

sector_stats = {}

for i, (name, tickers) in enumerate(SECTORS.items()):
    scores = []
    # 快速掃描每個板塊前 3 檔作為晴雨表基準
    for t in tickers[:3]:
        res = analyze_ticker(t)
        if res: scores.append(res['score'])
    
    avg_score = sum(scores)/len(scores) if scores else 0
    sector_stats[name] = avg_score
    
    with baro_cols[i]:
        if avg_score >= 2.5:
            weather, color = "☀️ 大晴天", "normal"
        elif avg_score >= 1.5:
            weather, color = "🌤️ 多雲", "off"
        else:
            weather, color = "🌧️ 雷陣雨", "inverse"
        
        st.metric(name.split()[1], f"{avg_score:.1f}/3.0", weather, delta_color=color)

st.divider()

# --- B. 側邊欄：偵察控制 ---
with st.sidebar:
    st.header("🕹️ 指揮控制")
    user_input = st.text_input("📡 輸入新代號 (用逗號隔開):", placeholder="例如: RKLB, POET")
    st.divider()
    if st.button("🔄 刷新全域數據"):
        st.rerun()
    st.info("系統提示：IONQ 目前處於尋底階段，支撐位約在 $30-$32。")

# --- C. 板塊詳細偵察區 ---
# 如果有手動輸入，優先顯示
if user_input:
    st.subheader("🔍 即時偵察結果")
    custom_list = [x.strip().upper() for x in user_input.split(',') if x.strip()]
    c_cols = st.columns(5)
    for i, t in enumerate(custom_list):
        with c_cols[i % 5]:
            res = analyze_ticker(t)
            if res:
                # 這裡顯示詳細卡片
                st.write(f"**{t}**: ${res['price']:.2f} ({res['change']:.1f}%)")
                st.progress(res['score']/3)

# 依序顯示各板塊
for sector, tickers in SECTORS.items():
    st.subheader(f"📍 {sector}")
    cols = st.columns(5)
    for i, t in enumerate(tickers):
        with cols[i % 5]:
            res = analyze_ticker(t)
            if res:
                # 顏色邏輯：3綠、2黃、1紅
                if res['score'] == 3: bg, lbl = "#1E4620", "🔥 全力進攻"
                elif res['score'] == 2: bg, lbl = "#46461E", "🟡 謹慎持有"
                else: bg, lbl = "#461E1E", "🚨 全力撤退"
                
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #555; text-align:center; min-height:160px;">
                    <h3 style="margin:0; color:#FFD700;">{t}</h3>
                    <p style="font-size:22px; margin:5px 0;">${res['price']:.2f}</p>
                    <p style="font-size:12px; margin:0; color:{'#00FF00' if res['change']>0 else '#FF4B4B'};">
                        {res['change']:.2f}% | 量:{res['vol_ratio']:.1f}x
                    </p>
                    <hr style="margin:8px 0; opacity:0.2;">
                    <p style="font-size:14px; margin:0; font-weight:bold;">{lbl}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption(f"{t} 偵訊中斷")



  



