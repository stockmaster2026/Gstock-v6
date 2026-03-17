import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 數據中心：定義板塊與個股 (解決顯示不全問題) ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = [
        {"板塊": "量子運算 ⚛️", "代碼": "IONQ", "價格": 33.31, "F1": 40, "F2": 49, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "RGTI", "價格": 16.22, "F1": 40, "F2": 40, "F3": "☁️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QUAN", "價格": 0.04, "F1": 80, "F2": 47, "F3": "☀️"},
        {"板塊": "量子運算 ⚛️", "代碼": "QBTS", "價格": 0.00, "F1": 0, "F2": 0, "F3": "❓"},
        {"板塊": "數據存儲 💾", "代碼": "WDC", "價格": 313.81, "F1": 100, "F2": 57, "F3": "☀️"},
        {"板塊": "數據存儲 💾", "代碼": "STX", "價格": 421.09, "F1": 100, "F2": 49, "F3": "☁️"},
        {"板塊": "AI 診斷 🧠", "代碼": "TEM", "價格": 50.84, "F1": 65, "F2": 72, "F3": "☀️"},
        {"板塊": "AI 診斷 🧠", "代碼": "POET", "價格": 5.12, "F1": 75, "F2": 80, "F3": "☀️"}
    ]

# --- 2. 核心計算邏輯 ---
def get_strategy(f1, f2, f3):
    score = (f1 * 0.4) + (f2 * 0.6)
    if f3 == "❓": return "N/A", "數據缺失", 0
    if score > 75 and f3 == "☀️": return "🟢 試單 (+20%)", "強勢轉強", score
    if score < 55 or f3 == "🌧️": return "⚠️ 減碼 (-30%)", "動能背離", score
    return "⚖️ 持有觀望", "橫盤整理", score

# --- 3. 介面設定 ---
st.set_page_config(layout="wide")
st.title("🛡️ 核心三濾網：板塊戰略儀表板")

# 頂部警告與提醒 (解決 iOS 減碼定義)
st.warning("📊 **執行提醒：** 『減碼 30%』是指『目前持倉數量』之比例。若數據未變，執行過一次後無需重複執行。")

# --- 4. 板塊摘要區 (這是你最需要的：顯示各個板塊狀況) ---
df_all = pd.DataFrame(st.session_state.master_data)

# 計算每個板塊的平均分
sector_summary = df_all.groupby("板塊").agg({"F1": "mean", "F2": "mean"}).reset_index()

st.subheader("🌡️ 各板塊即時健康度")
cols = st.columns(len(sector_summary))
for i, row in sector_summary.iterrows():
    avg_score = (row['F1'] * 0.4) + (row['F2'] * 0.6)
    status = "☀️ 晴朗" if avg_score > 70 else "☁️ 多雲" if avg_score > 50 else "🌧️ 降雨"
    cols[i].metric(row['板塊'], f"{avg_score:.1f} 分", f"狀態: {status}")

st.divider()

# --- 5. 側邊欄：搜尋個股 (解決搜尋與建議消失問題) ---
with st.sidebar:
    st.header("🔍 個股診斷")
    search_sym = st.text_input("輸入代號", "").upper().strip()
    if search_sym:
        target = df_all[df_all['代碼'] == search_sym]
        if not target.empty:
            s = target.iloc[0]
            adv, log, _ = get_strategy(s['F1'], s['F2'], s['F3'])
            st.metric(f"{search_sym} 現價", f"${s['價格']}")
            st.success(f"戰略：{adv}")
            st.info(f"理由：{log}")
            st.progress(int(s['F1']), text=f"F1: {s['F1']}%")
            st.progress(int(s['F2']), text=f"F2: {s['F2']}%")
        else:
            st.error("找不到代碼，請確認是否已加入板塊清單。")

# --- 6. 板塊晴雨表 (個股明細) ---
st.subheader("📊 板塊個股明細 (含 F3 過濾)")

final_list = []
for _, r in df_all.iterrows():
    adv, log, score = get_strategy(r['F1'], r['F2'], r['F3'])
    final_list.append({
        "板塊": r['板塊'], "代碼": r['代碼'], "現價": r['價格'],
        "趨勢(F1)": r['F1'], "動能(F2)": r['F2'], "核心(F3)": r['F3'],
        "總分": score, "建議倉位 🎯": adv
    })

df_display = pd.DataFrame(final_list)

# 顯示分組表格
for sector in df_display['板塊'].unique():
    st.write(f"### {sector}")
    sector_df = df_display[df_display['板塊'] == sector]
    st.data_editor(
        sector_df.drop(columns=["板塊"]),
        column_config={
            "趨勢(F1)": st.column_config.ProgressColumn(min_value=0, max_value=100),
            "動能(F2)": st.column_config.NumberColumn(format="%d 🔥"),
            "總分": st.column_config.NumberColumn(format="%.1f"),
            "現價": st.column_config.NumberColumn(format="$%.2f")
        },
        hide_index=True,
        use_container_width=True,
        key=sector
    )

