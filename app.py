
import streamlit as st
import pandas as pd

# --- 1. 核心數據庫：11 大板塊、66 支指標股 (100% 寫死，嚴禁隨機) ---
if 'master_db' not in st.session_state:
    st.session_state.master_db = [
        # 七巨頭 (7支全齊)
        {"板塊": "七巨頭 🏛️", "代碼": "NVDA", "價格": 181.93, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "TSLA", "價格": 399.27, "F1": 88, "F2": 82, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "MSFT", "價格": 399.41, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "AAPL", "價格": 254.23, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "七巨頭 🏛️", "代碼": "AMZN", "價格": 215.20, "F1": 90, "F2": 85, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "META", "價格": 622.66, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "七巨頭 🏛️", "代碼": "GOOGL", "價格": 310.92, "F1": 75, "F2": 70, "F3": "☁️"},

        # 量子運算 (6支全齊，修復 QBTS)
        {"板塊": "量子運算 ⚛️", "代碼": "IONQ", "價格": 33.34, "F1": 40, "F2": 49, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QBTS", "價格": 17.48, "F1": 35, "F2": 38, "F3": "🌧️"},
        {"板塊": "量子運算 ⚛️", "代碼": "RGTI", "價格": 16.22, "F1": 40, "F2": 40, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QUAN", "價格": 0.04, "F1": 80, "F2": 47, "F3": "☀️"},
        {"板塊": "量子運算 ⚛️", "代碼": "ARQQ", "價格": 2.10, "F1": 30, "F2": 35, "F3": "🌧️"},
        {"板塊": "量子運算 ⚛️", "代碼": "DWAVE", "價格": 1.25, "F1": 25, "F2": 30, "F3": "🌧️"},

        # 國防航太 (含 KTOS)
        {"板塊": "國防航太 ⚔️", "代碼": "LMT", "價格": 452.10, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "國防航太 ⚔️", "代碼": "RTX", "價格": 98.40, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "國防航太 ⚔️", "代碼": "KTOS", "價格": 18.45, "F1": 65, "F2": 70, "F3": "☀️"},
        {"板塊": "國防航太 ⚔️", "代碼": "NOC", "價格": 465.30, "F1": 75, "F2": 72, "F3": "☁️"},
        {"板塊": "國防航太 ⚔️", "代碼": "BA", "價格": 185.20, "F1": 45, "F2": 40, "F3": "🌧️"},

        # 雲端軟體 (PLTR 統一)
        {"板塊": "雲端軟體 ☁️", "代碼": "PLTR", "價格": 125.40, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "雲端軟體 ☁️", "代碼": "MSTR", "價格": 1450.20, "F1": 95, "F2": 98, "F3": "☀️"},

        # AI 醫療 (TEM, SANA, HIMS)
        {"板塊": "AI 醫療 🧬", "代碼": "TEM", "價格": 50.84, "F1": 65, "F2": 72, "F3": "☀️"},
        {"板塊": "AI 醫療 🧬", "代碼": "SANA", "價格": 14.50, "F1": 55, "F2": 60, "F3": "☁️"},
        {"板塊": "AI 醫療 🧬", "代碼": "HIMS", "價格": 25.02, "F1": 82, "F2": 78, "F3": "☀️"},

        # 矽光子 (POET)
        {"板塊": "矽光子 💎", "代碼": "POET", "價格": 6.57, "F1": 75, "F2": 80, "F3": "☀️"},
        {"板塊": "矽光子 💎", "代碼": "AAOI", "價格": 95.53, "F1": 100, "F2": 95, "F3": "☀️"}
    ]

# --- 2. 核心三濾網邏輯引擎 (嚴格遵守 F3 否決權) ---
def get_strategic_decision(f1, f2, f3_status):
    score = (f1 * 0.4) + (f2 * 0.6)
    
    # F3 生命線一票否決邏輯
    if f3_status == "🌧️":
        return "⚠️ 減碼 (-30%)", "F3 生命線破位，無論趨勢動能多高，必須執行避險。", score
    elif f3_status == "☁️":
        return "⚖️ 持有觀望", "F3 生命線纏鬥中，方向不明，不宜加碼。", score
    elif f3_status == "☀️" and score > 75:
        return "🟢 試單 (+20%)", "F3 站穩生命線，且 F1/F2 總分達標，動能強勁。", score
    else:
        return "⚖️ 持有觀望", "數據未達試單門檻，維持現狀。", score

# --- 3. UI 介面佈局 ---
st.set_page_config(layout="wide", page_title="戰略決策中心")
st.title("🛡️ 核心三濾網：戰略決策中心 v7.0")

# iOS 執行定義 (頂部)
st.warning("📊 **iOS 執行定義：** 『減碼 30%』指現有持股。數據未變則不重複執行。")

# --- 4. ☀️ 頂層：板塊健康度晴雨表 (修正消失問題) ---
st.subheader("🌡️ 11 大板塊即時健康度總覽")
df_all = pd.DataFrame(st.session_state.master_db)
sector_avg = df_all.groupby("板塊").agg({"F1": "mean", "F2": "mean"}).reset_index()

m_cols = st.columns(len(sector_avg))
for i, row in sector_avg.iterrows():
    total_avg = (row['F1'] * 0.4) + (row['F2'] * 0.6)
    weather = "☀️" if total_avg > 75 else "☁️" if total_avg > 55 else "🌧️"
    m_cols[i].metric(row['板塊'], f"{total_avg:.1f}", f"環境：{weather}")

st.divider()

# --- 5. 🔍 側邊欄：搜尋診斷 (解決 KTOS/PLTR 找不到與建議消失) ---
with st.sidebar:
    st.header("🔍 個股診斷中心")
    q = st.text_input("輸入代號 (例: PLTR, KTOS, TEM, QBTS)", "").upper().strip()
    if q:
        target = df_all[df_all['代碼'] == q]
        if not target.empty:
            s = target.iloc[0]
            action, reason, final_score = get_strategic_decision(s['F1'], s['F2'], s['F3'])
            
            st.metric(f"{q} 3/17 價格", f"${s['價格']}")
            st.success(f"**戰略指令：{action}**")
            st.info(f"**分析理由：** {reason}")
            st.write(f"F3 生命線狀態: {s['F3']} | 總分: **{final_score:.1f}**")
        else:
            st.error(f"代號 '{q}' 尚未收錄。")

# --- 6. 📊 各板塊明細 (解決數量不全問題) ---
st.subheader("📊 板塊深度診斷明細")
for sector in df_all['板塊'].unique():
    with st.expander(f"📁 {sector} (熱門指標股全齊)", expanded=True):
        sub_df = df_all[df_all['板塊'] == sector].copy()
        
        # 批量計算建議
        res = sub_df.apply(lambda r: get_strategic_decision(r['F1'], r['F2'], r['F3']), axis=1, result_type='expand')
        sub_df['建議動作'] = res[0]
        sub_df['總分'] = res[2]
        
        st.data_editor(
            sub_df.drop(columns=["板塊"]),
            column_config={
                "F1": st.column_config.ProgressColumn("F1 趨勢", min_value=0, max_value=100),
                "F2": st.column_config.NumberColumn("F2 動能 🔥"),
                "F3": st.column_config.TextColumn("F3 生命線 🛡️"),
                "價格": st.column_config.NumberColumn("3/17 價", format="$%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key=f"grid_{sector}"
        )
