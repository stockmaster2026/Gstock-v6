import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 核心數據庫：10 大板塊 x 42+ 支熱門指標股 ---
if 'master_db' not in st.session_state:
    st.session_state.master_db = [
        # 1. 七巨頭
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "NVDA", "價格": 183.22, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "MSFT", "價格": 415.50, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "AAPL", "價格": 192.30, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "AMZN", "價格": 178.40, "F1": 90, "F2": 85, "F3": "☀️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "META", "價格": 512.10, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "GOOGL", "價格": 158.20, "F1": 75, "F2": 70, "F3": "☁️"},
        {"板塊": "七巨頭 (Magnificent Seven) 🏛️", "代碼": "TSLA", "價格": 395.56, "F1": 88, "F2": 82, "F3": "☀️"},

        # 2. 矽光子
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "POET", "價格": 5.12, "F1": 75, "F2": 80, "F3": "☀️"},
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "AVGO", "價格": 324.92, "F1": 92, "F2": 88, "F3": "☀️"},
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "TSM", "價格": 205.84, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "PSTG", "價格": 54.20, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "ALTR", "價格": 88.50, "F1": 60, "F2": 55, "F3": "☁️"},
        {"板塊": "矽光子 (Silicon Photonics) 💎", "代碼": "LUX", "價格": 12.40, "F1": 50, "F2": 45, "F3": "🌧️"},

        # 3. AI 醫療 (含 TEM, SANA, HIMS)
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "TEM", "價格": 50.84, "F1": 65, "F2": 72, "F3": "☀️"},
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "HIMS", "價格": 23.84, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "SANA", "價格": 14.50, "F1": 55, "F2": 60, "F3": "☁️"},
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "SDGR", "價格": 32.10, "F1": 45, "F2": 50, "F3": "🌧️"},
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "RXRX", "價格": 11.20, "F1": 50, "F2": 45, "F3": "🌧️"},
        {"板塊": "AI 醫療 (AI Healthcare) 🧬", "代碼": "GEHC", "價格": 85.30, "F1": 75, "F2": 70, "F3": "☀️"},

        # 4. 太空板塊
        {"板塊": "太空板塊 (Space Sector) 🚀", "代碼": "RKLB", "價格": 33.50, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "太空板塊 (Space Sector) 🚀", "代碼": "ASTS", "價格": 26.00, "F1": 90, "F2": 85, "F3": "☀️"},
        {"板塊": "太空板塊 (Space Sector) 🚀", "代碼": "LUNR", "價格": 1.50, "F1": 70, "F2": 75, "F3": "☁️"},
        {"板塊": "太空板塊 (Space Sector) 🚀", "代碼": "PL", "價格": 4.70, "F1": 65, "F2": 60, "F3": "☁️"},
        {"板塊": "太空板塊 (Space Sector) 🚀", "代塊": "RDW", "價格": 1.40, "F1": 55, "F2": 50, "F3": "🌧️"},
        {"板塊": "太空板塊 (Space Sector) 🚀", "代碼": "KTOS", "價格": 15.30, "F1": 60, "F2": 55, "F3": "☁️"},

        # 5. 光通訊
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "AAOI", "價格": 95.53, "F1": 100, "F2": 95, "F3": "☀️"},
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "FNAR", "價格": 489.38, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "LITE", "價格": 558.44, "F1": 92, "F2": 88, "F3": "☀️"},
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "COHR", "價格": 235.72, "F1": 80, "F2": 75, "F3": "☁️"},
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "CIEN", "價格": 294.17, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "光通訊 (Optical Networking) ⚡", "代碼": "CSCO", "價格": 78.64, "F1": 55, "F2": 50, "F3": "🌧️"},

        # 6. 量子運算 (含 QBTS 缺失修正)
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "IONQ", "價格": 33.59, "F1": 40, "F2": 49, "F3": "☁️"},
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "RGTI", "價格": 16.60, "F1": 40, "F2": 40, "F3": "☁️"},
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "QUAN", "價格": 0.04, "F1": 80, "F2": 47, "F3": "☀️"},
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "QBTS", "價格": 19.38, "F1": 35, "F2": 38, "F3": "🌧️"},
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "ARQQ", "價格": 2.10, "F1": 30, "F2": 35, "F3": "🌧️"},
        {"板塊": "量子運算 (Quantum Computing) ⚛️", "代碼": "DWAVE", "價格": 1.25, "F1": 25, "F2": 30, "F3": "🌧️"},

        # 7. 數據存儲
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "WDC", "價格": 313.81, "F1": 100, "F2": 57, "F3": "☀️"},
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "STX", "價格": 421.09, "F1": 100, "F2": 49, "F3": "☁️"},
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "MU", "價格": 441.80, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "SNDK", "價格": 703.63, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "PSTG", "價格": 55.40, "F1": 75, "F2": 70, "F3": "☁️"},
        {"板塊": "數據存儲 (Data Storage) 💾", "代碼": "NTAP", "價格": 112.30, "F1": 70, "F2": 65, "F3": "☁️"},

        # 8. AI 算力與晶片
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "AMD", "價格": 305.79, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "ARM", "價格": 260.99, "F1": 90, "F2": 85, "F3": "☀️"},
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "INTC", "價格": 41.55, "F1": 45, "F2": 40, "F3": "🌧️"},
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "ASML", "價格": 1073.35, "F1": 70, "F2": 75, "F3": "☁️"},
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "KLAC", "價格": 712.40, "F1": 82, "F2": 78, "F3": "☀️"},
        {"板塊": "AI 算力與晶片 (AI Chips) 🧠", "代碼": "CDNS", "價格": 320.10, "F1": 88, "F2": 84, "F3": "☀️"},

        # 9. 人形機器人
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "ISRG", "價格": 482.76, "F1": 95, "F2": 90, "F3": "☀️"},
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "TER", "價格": 165.20, "F1": 85, "F2": 80, "F3": "☀️"},
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "PATH", "價格": 10.40, "F1": 40, "F2": 45, "F3": "🌧️"},
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "TRMB", "價格": 62.30, "F1": 70, "F2": 65, "F3": "☁️"},
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "BOTZ", "價格": 35.10, "F1": 75, "F2": 70, "F3": "☀️"},
        {"板塊": "人形機器人與自動化 (Robotics) 🤖", "代碼": "ROCKWELL", "價格": 285.40, "F1": 60, "F2": 55, "F3": "☁️"},

        # 10. 雲端軟體
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "PLTR", "價格": 125.40, "F1": 98, "F2": 92, "F3": "☀️"},
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "SNOW", "價格": 205.10, "F1": 65, "F2": 60, "F3": "☁️"},
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "CRM", "價格": 181.90, "F1": 55, "F2": 50, "F3": "🌧️"},
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "MSTR", "價格": 1450.20, "F1": 95, "F2": 98, "F3": "☀️"},
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "ADBE", "價格": 512.40, "F1": 50, "F2": 45, "F3": "🌧️"},
        {"板塊": "雲端軟體服務 (SaaS) ☁️", "代碼": "SHOP", "價格": 187.00, "F1": 75, "F2": 70, "F3": "☀️"}
    ]

# --- 2. 策略引擎 ---
def get_action(f1, f2, f3):
    score = (f1 * 0.4) + (f2 * 0.6)
    if f3 == "❓": return "數據缺失", "請檢查", score
    if score > 75 and f3 == "☀️": return "🟢 試單 (+20%)", "核心強勢，多頭占優", score
    if score < 55 or f3 == "🌧️": return "⚠️ 減碼 (-30%)", "動能背離，落袋為安", score
    return "⚖️ 持有觀望", "橫盤震盪，不宜動作", score

# --- 3. 介面設定 ---
st.set_page_config(layout="wide")
st.title("🛡️ 核心三濾網：十強板塊決策中心")

# iOS 定義提醒
st.warning("📊 **執行提醒：** 『減碼 30%』是指『目前該標的持股數量』之比例。若數據未變，執行一次即可，無需重複賣出。")

# --- 4. 板塊摘要統計 (解決「不顯示板塊狀況」) ---
df_all = pd.DataFrame(st.session_state.master_db)
sector_summary = df_all.groupby("板塊").agg({"F1": "mean", "F2": "mean"}).reset_index()

st.subheader("🌡️ 板塊即時健康度摘要")
cols = st.columns(5) # 分兩行顯示，第一行 5 個
for i, row in sector_summary.iterrows():
    avg_score = (row['F1'] * 0.4) + (row['F2'] * 0.6)
    weather = "☀️ 晴朗" if avg_score > 70 else "☁️ 多雲" if avg_score > 50 else "🌧️ 降雨"
    col_idx = i % 5
    with cols[col_idx]:
        st.metric(row['板塊'], f"{avg_score:.1f} 分", f"{weather}")

st.divider()

# --- 5. 側邊欄：搜尋診斷 (解決搜尋不到資料與建議消失問題) ---
with st.sidebar:
    st.header("🔍 全市場個股診斷")
    q = st.text_input("輸入代號 (如: TEM, POET, RKLB)", "").upper().strip()
    if q:
        target = df_all[df_all['代碼'] == q]
        if not target.empty:
            s = target.iloc[0]
            adv, log, _ = get_action(s['F1'], s['F2'], s['F3'])
            st.metric(f"{q} 現價", f"${s['價格']}")
            st.success(f"**戰略：{adv}**")
            st.info(f"**理由：** {log}")
            st.progress(int(s['F1']), text=f"F1: {s['F1']}%")
            st.progress(int(s['F2']), text=f"F2: {s['F2']}%")
        else:
            st.error("代號不在核心清單中。")

# --- 6. 核心顯示：板塊之下顯示個股內容 (解決只有板塊名稱的問題) ---
st.subheader("📊 各板塊個股明細 (核心十強)")

for sector in df_all['板塊'].unique():
    with st.expander(f"📁 {sector}", expanded=True):
        sub_df = df_all[df_all['板塊'] == sector].copy()
        
        # 計算每支股票的建議
        results = sub_df.apply(lambda r: get_action(r['F1'], r['F2'], r['F3']), axis=1, result_type='expand')
        sub_df['總分'] = results[2]
        sub_df['戰略建議'] = results[0]
        
        # 表格渲染
        st.data_editor(
            sub_df.drop(columns=["板塊"]),
            column_config={
                "代碼": st.column_config.TextColumn(width="small"),
                "F1": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "F2": st.column_config.NumberColumn(format="%d 🔥"),
                "總分": st.column_config.NumberColumn(format="%.1f"),
                "價格": st.column_config.NumberColumn(format="$%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key=f"tab_{sector}"
        )

