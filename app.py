
import streamlit as st
import pandas as pd

# --- 1. 核心數據庫：確保 PLTR, QBTS, SANA, TEM, HIMS 全數在列 ---
if 'master_db' not in st.session_state:
    st.session_state.master_db = [
        # 1. 國防航太 ⚔️
        {"板塊": "國防航太 ⚔️", "代碼": "LMT", "價格": 452.10, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "國防航太 ⚔️", "代碼": "RTX", "價格": 98.40, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "國防航太 ⚔️", "代碼": "NOC", "價格": 465.30, "F1": 75, "F2": 72, "F3": "☁️"},
        {"板塊": "國防航太 ⚔️", "代碼": "BA", "價格": 185.20, "F1": 45, "F2": 40, "F3": "🌧️"},
        {"板塊": "國防航太 ⚔️", "代碼": "PLTR_DEF", "價格": 125.40, "F1": 98, "F2": 92, "F3": "☀️"}, # 國防AI

        # 2. 七巨頭 🏛️
        {"板塊": "七巨頭 🏛️", "代碼": "NVDA", "價格": 181.93, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "TSLA", "價格": 399.27, "F1": 88, "F2": 82, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "MSFT", "價格": 399.41, "F1": 85, "F2": 80, "F3": "☀️"},

        # 3. 雲端軟體 ☁️ (PLTR 在此)
        {"板塊": "雲端軟體 ☁️", "代碼": "PLTR", "價格": 125.40, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "雲端軟體 ☁️", "代碼": "MSTR", "價格": 1450.20, "F1": 95, "F2": 98, "F3": "☀️"},
        {"板塊": "雲端軟體 ☁️", "代碼": "SNOW", "價格": 205.10, "F1": 65, "F2": 60, "F3": "☁️"},

        # 4. AI 醫療 🧬 (TEM, SANA, HIMS)
        {"板塊": "AI 醫療 🧬", "代碼": "TEM", "價格": 50.84, "F1": 65, "F2": 72, "F3": "☀️"},
        {"板塊": "AI 醫療 🧬", "代碼": "HIMS", "價格": 25.02, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "AI 醫療 🧬", "代碼": "SANA", "價格": 14.50, "F1": 55, "F2": 60, "F3": "☁️"},
        {"板塊": "AI 醫療 🧬", "代碼": "SDGR", "價格": 32.10, "F1": 45, "F2": 50, "F3": "🌧️"},

        # 5. 矽光子 💎 (POET)
        {"板塊": "矽光子 💎", "代碼": "POET", "價格": 6.57, "F1": 75, "F2": 80, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "AVGO", "價格": 324.92, "F1": 92, "F2": 88, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "TSM", "價格": 205.84, "F1": 98, "F2": 92, "F3": "☀️"},

        # 6. 量子運算 ⚛️ (QBTS)
        {"板塊": "量子運算 ⚛️", "代碼": "IONQ", "價格": 33.34, "F1": 40, "F2": 49, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QBTS", "價格": 17.48, "F1": 35, "F2": 38, "F3": "🌧️"},
        
        # 7. 太空板塊 🚀
        {"板塊": "太空板塊 🚀", "代碼": "RKLB", "價格": 33.50, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "太空板塊 🚀", "代碼": "ASTS", "價格": 26.00, "F1": 90, "F2": 85, "F3": "☀️"},

        # 8. 光通訊 ⚡ (AAOI)
        {"板塊": "光通訊 ⚡", "代碼": "AAOI", "價格": 95.53, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "光通訊 ⚡", "代碼": "FNAR", "價格": 489.38, "F1": 85, "F2": 80, "F3": "☀️"}
    ]

# --- 2. 戰略引擎 (F3 聯動核心) ---
def get_action_report(f1, f2, f3_icon):
    score = (f1 * 0.4) + (f2 * 0.6)
    # F3 強制門檻邏輯
    if f3_icon == "☀️" and score > 75:
        return "🟢 試單 (+20%)", "核心濾網(F3)大晴天，動能趨勢強勁。", score
    elif f3_icon == "🌧️" or score < 55:
        return "⚠️ 減碼 (-30%)", "核心濾網(F3)顯示降雨或總分過低，應收縮倉位。", score
    else:
        return "⚖️ 持有觀望", "目前處於中性整理區間，等待信號。", score

# --- 3. UI 佈局設定 ---
st.set_page_config(layout="wide")
st.title("🛡️ 核心三濾網：全球戰略決策中心 v5.0")

# iOS 執行定義
st.warning("📊 **iOS 執行定義：** 『減碼 30%』係指現有持股數。數據未變則不重複賣出。")

# --- 4. ☀️ 頂層：板塊摘要晴雨表 (確保不消失) ---
st.subheader("🌡️ 11 大板塊健康度總覽")
df_master = pd.DataFrame(st.session_state.master_db)
# 計算板塊平均分數
sector_summary = df_master.groupby("板塊").agg({"F1": "mean", "F2": "mean"}).reset_index()

m_cols = st.columns(len(sector_summary))
for i, row in sector_summary.iterrows():
    avg_score = (row['F1'] * 0.4) + (row['F2'] * 0.6)
    weather = "☀️" if avg_score > 75 else "☁️" if avg_score > 55 else "🌧️"
    m_cols[i].metric(row['板塊'], f"{avg_score:.1f}", f"{weather}")

st.divider()

# --- 5. 🔍 側邊欄：搜尋診斷 (修復 PLTR 與建議消失問題) ---
with st.sidebar:
    st.header("🔍 全市場代號診斷")
    query = st.text_input("輸入代碼 (例: PLTR, TEM, QBTS)", "").upper().strip()
    if query:
        target = df_master[df_master['代碼'] == query]
        if not target.empty:
            s = target.iloc[0]
            # 重新計算建議
            action, reason, total = get_action_report(s['F1'], s['F2'], s['F3'])
            st.metric(f"{query} 當前報價", f"${s['價格']}")
            st.success(f"**戰略動作：{action}**")
            st.info(f"**分析理由：** {reason}")
            st.write(f"F3 狀態: {s['F3']} | 總分: **{total:.1f}**")
            st.progress(int(s['F1']), text=f"F1 趨勢指標: {s['F1']}%")
        else:
            st.error(f"代號 '{query}' 不在核心資料庫中。")

# --- 6. 📊 板塊深度明細 ---
st.subheader("📊 各板塊熱門指標股明細")
for sector in df_master['板塊'].unique():
    with st.expander(f"📁 {sector}", expanded=True):
        sub_df = df_master[df_master['板塊'] == sector].copy()
        
        # 批量計算戰略
        res = sub_df.apply(lambda r: get_action_report(r['F1'], r['F2'], r['F3']), axis=1, result_type='expand')
        sub_df['建議動作'] = res[0]
        sub_df['總分'] = res[2]
        
        st.data_editor(
            sub_df.drop(columns=["板塊"]),
            column_config={
                "F1": st.column_config.ProgressColumn("F1 趨勢", min_value=0, max_value=100),
                "F2": st.column_config.NumberColumn("F2 動能 🔥"),
                "價格": st.column_config.NumberColumn("3/17 價", format="$%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key=f"tab_{sector}"
        )

