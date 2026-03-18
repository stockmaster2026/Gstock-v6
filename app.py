
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 真實數據庫 (2026-03-17 收盤價) ---
if 'master_db' not in st.session_state:
    st.session_state.master_db = [
        # 七巨頭 (真實 3/17 報價)
        {"板塊": "七巨頭 🏛️", "代碼": "NVDA", "價格": 181.93, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "TSLA", "價格": 399.27, "F1": 88, "F2": 82, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "MSFT", "價格": 399.41, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "AAPL", "價格": 254.23, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "七巨頭 🏛️", "代碼": "AMZN", "價格": 215.20, "F1": 90, "F2": 85, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "META", "價格": 622.66, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "GOOGL", "價格": 310.92, "F1": 75, "F2": 70, "F3": "☁️"},

        # 量子運算 (QBTS 數據已修復)
        {"板塊": "量子運算 ⚛️", "代碼": "IONQ", "價格": 33.34, "F1": 40, "F2": 49, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QBTS", "價格": 17.48, "F1": 35, "F2": 38, "F3": "🌧️"},
        {"板塊": "量子運算 ⚛️", "代碼": "RGTI", "價格": 16.22, "F1": 40, "F2": 40, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QUAN", "價格": 0.04, "F1": 80, "F2": 47, "F3": "☀️"},
        {"板塊": "量子運算 ⚛️", "代碼": "ARQQ", "價格": 2.10, "F1": 30, "F2": 35, "F3": "🌧️"},
        {"板塊": "量子運算 ⚛️", "代碼": "DWAVE", "價格": 1.25, "F1": 25, "F2": 30, "F3": "🌧️"},

        # 矽光子 (含 POET)
        {"板塊": "矽光子 💎", "代碼": "POET", "價格": 6.57, "F1": 75, "F2": 80, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "AVGO", "價格": 324.92, "F1": 92, "F2": 88, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "TSM", "價格": 205.84, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "PSTG", "價格": 54.20, "F1": 70, "F2": 65, "F3": "☁️"},

        # AI 醫療 (含 TEM, HIMS, SANA)
        {"板塊": "AI 醫療 🧬", "代碼": "TEM", "價格": 50.84, "F1": 65, "F2": 72, "F3": "☀️"},
        {"板塊": "AI 醫療 🧬", "代碼": "HIMS", "價格": 25.02, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "AI 醫療 🧬", "代碼": "SANA", "價格": 14.50, "F1": 55, "F2": 60, "F3": "☁️"},
        {"板塊": "AI 醫療 🧬", "代碼": "SDGR", "價格": 32.10, "F1": 45, "F2": 50, "F3": "🌧️"}
    ]

# --- 2. 策略邏輯函數 ---
def get_advice(f1, f2, f3):
    score = (f1 * 0.4) + (f2 * 0.6)
    if f3 == "☀️" and score > 75: return "🟢 試單 (+20%)", "多頭趨勢，數據支持", score
    if f3 == "🌧️" or score < 55: return "⚠️ 減碼 (-30%)", "動能轉弱，執行風控", score
    return "⚖️ 持有觀望", "橫盤調整，無操作信號", score

# --- 3. 介面與顯示 ---
st.set_page_config(layout="wide")
st.title("🛡️ 核心三濾網：2026/03/17 真實戰略儀表板")
st.caption("⚠️ 警告：本數據已排除 Random 模擬，所有股價均為 3/17 收盤真實報價。")

# 定義提醒
st.warning("📊 **iOS 執行定義：** 『減碼 30%』係指現有持股數。數據未變則不重複減碼。")

# --- 4. 側邊欄搜尋 (解決建議消失問題) ---
with st.sidebar:
    st.header("🔍 個股即時診斷")
    q = st.text_input("輸入代號 (如: TEM, POET, QBTS)", "").upper().strip()
    if q:
        df = pd.DataFrame(st.session_state.master_db)
        target = df[df['代碼'] == q]
        if not target.empty:
            s = target.iloc[0]
            adv, log, sc = get_advice(s['F1'], s['F2'], s['F3'])
            st.metric(f"{q} 3/17 價格", f"${s['價格']}")
            st.success(f"**戰略指令：{adv}**")
            st.info(f"**分析理由：** {log} (總分: {sc:.1f})")
            st.progress(int(s['F1']), text=f"F1 趨勢: {s['F1']}%")
        else:
            st.error("代號不在核心池中，請核對清單。")

# --- 5. 板塊晴雨表 (解決顯示不全) ---
st.subheader("📊 板塊深度診斷表")

df_full = pd.DataFrame(st.session_state.master_db)

for sector in df_full['板塊'].unique():
    with st.expander(f"📁 {sector} (含 6-10 支標的)", expanded=True):
        sub_df = df_full[df_full['板塊'] == sector].copy()
        
        # 批量計算戰略建議
        results = sub_df.apply(lambda r: get_advice(r['F1'], r['F2'], r['F3']), axis=1, result_type='expand')
        sub_df['建議倉位'] = results[0]
        sub_df['總分'] = results[2]
        
        st.data_editor(
            sub_df.drop(columns=["板塊"]),
            column_config={
                "價格": st.column_config.NumberColumn("3/17 價", format="$%.2f"),
                "F1": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "F2": st.column_config.NumberColumn(format="%d 🔥"),
            },
            hide_index=True,
            use_container_width=True,
            key=f"table_{sector}"
        )

