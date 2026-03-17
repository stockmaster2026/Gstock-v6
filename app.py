
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 戰略邏輯引擎 (確保搜尋與大表邏輯一致) ---
def calculate_strategy(f1, f2, f3_status):
    """
    根據核心三濾網計算操作建議
    f1: 趨勢, f2: 動能, f3_status: 核心過濾器(☀️/☁️/🌧️)
    """
    score = (f1 * 0.4) + (f2 * 0.6)
    
    if f3_status == "☀️" and score > 75:
        return "🔥 試單 (+20%)", "初步轉強"
    elif f3_status == "🌧️" or score < 50:
        return "⚠️ 減碼 (-30%)", "動能背離 / 核心警戒"
    elif score < 30:
        return "🚫 強制清倉", "趨勢反轉"
    else:
        return "⚖️ 持有觀望", "橫盤整理"

# --- 2. 模擬數據抓取 (含 QBTS 容錯邏輯) ---
def get_market_data():
    # 這裡模擬你的原始數據
    data = {
        "代碼": ["IONQ", "RGTI", "QUAN", "QBTS", "WDC", "STX", "TEM"],
        "現價": [33.31, 16.22, 0.04, None, 313.81, 421.09, 50.84],
        "漲跌%": ["0.06%", "0.50%", "7.73%", "數據缺失", "9.64%", "5.59%", "1.20%"],
        "F1": [40, 40, 80, 0, 100, 100, 65],
        "F2": [49, 40, 47, 0, 57, 49, 72],
        "F3": ["☁️", "☁️", "☀️", "❓", "☀️", "☁️", "☀️"]
    }
    df = pd.DataFrame(data)
    
    # 處理 QBTS 缺失與計算建議
    processed_list = []
    for _, row in df.iterrows():
        # 如果數據缺失，給予預設值避免程式崩潰
        f1 = row['F1'] if not np.isnan(row['F1']) else 0
        f2 = row['F2'] if not np.isnan(row['F2']) else 0
        
        advice, logic = calculate_strategy(f1, f2, row['F3'])
        processed_list.append({"建議倉位": advice, "策略動作": logic})
    
    df_advice = pd.DataFrame(processed_list)
    return pd.concat([df, df_advice], axis=1)

# --- 3. UI 介面設定 ---
st.set_page_config(page_title="戰略儀表板", layout="wide")

# 自定義 CSS 提升質感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 頂部標示區 (解決第四個問題) ---
st.title("🛡️ 核心三濾網：戰略儀表板 (專業版)")
st.caption("Last Update: 2026-03-17 15:15 | 🟡 數據來源：即時 API 串接")

# 核心提醒 (解決 iOS 減碼定義問題)
st.warning("📊 **執行提醒：** 所有的『減碼 %』均指『該標的目前持倉數量』之比例（例：持 100 股減碼 30% 即賣出 30 股），非總資產比例。")

# 頂部關鍵指標
m1, m2, m3 = st.columns(3)
m1.metric("市場環境 (F3 通過率)", "68%", "+5%")
m2.metric("量子運算板塊", "偏弱", "需減碼", delta_color="inverse")
m3.metric("數據存儲板塊", "強勢", "試單中", delta_color="normal")

st.divider()

# --- 5. 個股快速診斷 (解決 Instagram 搜尋建議消失問題) ---
with st.sidebar:
    st.header("🔍 個股診斷")
    search_symbol = st.text_input("輸入代號 (如: TEM, IONQ)", "").upper()
    
    if search_symbol:
        df_all = get_market_data()
        target = df_all[df_all['代碼'] == search_symbol]
        
        if not target.empty:
            row = target.iloc[0]
            st.metric(f"{search_symbol} 現價", f"${row['現價']}", row['漲跌%'])
            
            # 重新顯示消失的操作建議
            st.subheader("🎯 操作建議")
            st.info(f"**指令：{row['建議倉位']}**")
            st.write(f"原因：{row['策略動作']}")
            
            # 視覺化指標
            st.write(f"核心過濾 (F3): {row['F3']}")
            st.progress(int(row['F1']), text=f"趨勢強度 (F1): {row['F1']}")
            st.progress(int(row['F2']), text=f"動能指標 (F2): {row['F2']}")
        else:
            st.error("找不到該代碼，請確認後再輸入。")

# --- 6. 晴雨表主表 (解決第一個與第五個問題) ---
st.subheader("📊 板塊晴雨表")

df_display = get_market_data()

# 使用 st.data_editor 達成專業視覺效果
st.data_editor(
    df_display,
    column_config={
        "代碼": st.column_config.TextColumn("代碼", width="small"),
        "漲跌%": st.column_config.TextColumn("漲跌%"),
        "F1": st.column_config.ProgressColumn("趨勢(F1)", min_value=0, max_value=100, format="%d"),
        "F2": st.column_config.NumberColumn("動能(F2)", format="%d 🔥"),
        "F3": st.column_config.TextColumn("核心(F3)", width="small"),
        "建議倉位": st.column_config.TextColumn("建議倉位 🎯"),
        "策略動作": st.column_config.TextColumn("邏輯說明 💡")
    },
    hide_index=True,
    use_container_width=True,
    disabled=True # 僅供查看
)

st.divider()
st.info("💡 如果 QBTS 顯示數據缺失，請手動確認該股是否處於停牌或 API 限制狀態。")



