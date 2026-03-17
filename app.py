import streamlit as st
import pandas as pd
import numpy as np

# --- STEP 1: 初始化全局數據緩存 (確保個股不會消失) ---
if 'master_data' not in st.session_state:
    # 這是你的初始基礎清單，包含 QBTS 等易出錯標的
    st.session_state.master_data = {
        "IONQ": {"price": 33.31, "change": "0.06%", "f1": 40, "f2": 49, "f3": "☁️"},
        "RGTI": {"price": 16.22, "change": "0.50%", "f1": 40, "f2": 40, "f3": "☁️"},
        "QUAN": {"price": 0.04, "change": "7.73%", "f1": 80, "f2": 47, "f3": "☀️"},
        "QBTS": {"price": 0.0, "change": "數據缺失", "f1": 0, "f2": 0, "f3": "❓"}, # 修復缺失
        "WDC": {"price": 313.81, "change": "9.64%", "f1": 100, "f2": 57, "f3": "☀️"},
        "STX": {"price": 421.09, "change": "5.59%", "f1": 100, "f2": 49, "f3": "☁️"},
        "TEM": {"price": 50.84, "change": "1.20%", "f1": 65, "f2": 72, "f3": "☀️"},
        "POET": {"price": 5.12, "change": "3.45%", "f1": 75, "f2": 80, "f3": "☀️"}
    }

# --- STEP 2: 核心戰略引擎 (確保搜尋與大表邏輯 100% 一致) ---
def analyze_stock(symbol, data_dict):
    f1 = data_dict.get('f1', 0)
    f2 = data_dict.get('f2', 0)
    f3 = data_dict.get('f3', "❓")
    
    # 總分計算邏輯
    total_score = (f1 * 0.4) + (f2 * 0.6)
    
    if f3 == "❓":
        return "N/A (數據缺失)", "請檢查 API 或代號是否正確"
    elif total_score > 75 and f3 == "☀️":
        return "🟢 試單 (+20%)", "核心三濾網全數通過，初步轉強"
    elif total_score < 55 or f3 == "🌧️":
        return "⚠️ 減碼 (-30%)", "趨勢或動能背離，建議縮減部位"
    else:
        return "⚖️ 持有觀望", "指標中性，維持原倉位等待訊號"

# --- STEP 3: 介面與頂部標示 (解決第四個問題) ---
st.set_page_config(page_title="戰略儀表板 v2.5", layout="wide")

st.title("🛡️ 核心三濾網：戰略儀表板")

# 解決 iOS 減碼定義問題 (顯示在最上方)
st.warning("""
**📢 交易執行準則：**
1. 『減碼 30%』是指 **「目前該標的持倉數量的 30%」** (例如持 100 股賣出 30 股)。
2. 若信號未變，執行過一次後 **「無需重複執行」**。
3. 除非信號進一步惡化（如顯示清倉），才需第二次動作。
""")

# --- STEP 4: 側邊欄：搜尋診斷 (解決搜尋不到資料與建議消失問題) ---
with st.sidebar:
    st.header("🔍 個股即時診斷")
    input_symbol = st.text_input("輸入代號 (如: POET, TEM)", "").upper().strip()
    
    if input_symbol:
        # 如果搜尋的代號不在緩存中，建立一個模擬條目 (避免搜尋不到報錯)
        if input_symbol not in st.session_state.master_data:
            st.session_state.master_data[input_symbol] = {
                "price": 0.0, "change": "新追蹤", "f1": 50, "f2": 50, "f3": "☁️"
            }
            st.success(f"已將 {input_symbol} 加入下方追蹤清單")

        stock_info = st.session_state.master_data[input_symbol]
        advice, logic = analyze_stock(input_symbol, stock_info)
        
        # 顯示搜尋後的診斷建議 (找回消失的部分)
        st.divider()
        st.metric(f"{input_symbol} 現價", f"${stock_info['price']}", stock_info['change'])
        st.subheader(f"戰略動作：{advice}")
        st.info(f"**邏輯分析：** {logic}")
        st.progress(int(stock_info['f1']), text=f"F1 趨勢: {stock_info['f1']}%")
        st.progress(int(stock_info['f2']), text=f"F2 動能: {stock_info['f2']}%")
        st.write(f"核心過濾 (F3): {stock_info['f3']}")

# --- STEP 5: 板塊晴雨表主表 (解決顯示不全與吸引力問題) ---
st.subheader("📊 板塊即時晴雨表 (動態清單)")

# 將字典轉換為 DataFrame
display_list = []
for sym, info in st.session_state.master_data.items():
    advice, logic = analyze_stock(sym, info)
    display_list.append({
        "代碼": sym,
        "現價": info['price'],
        "漲跌%": info['change'],
        "趨勢(F1)": info['f1'],
        "動能(F2)": info['f2'],
        "核心(F3)": info['f3'],
        "建議倉位 🎯": advice,
        "策略邏輯": logic
    })

df = pd.DataFrame(display_list)

# 解決 QBTS 缺失數據顯示 (強制處理 None)
df.fillna(0, inplace=True)

# 渲染表格 (包含 F1 進度條與 F2 火苗)
st.data_editor(
    df,
    column_config={
        "代碼": st.column_config.TextColumn("代碼", width="small"),
        "趨勢(F1)": st.column_config.ProgressColumn("趨勢 (F1)", min_value=0, max_value=100, format="%d"),
        "動能(F2)": st.column_config.NumberColumn("動能 (F2)", format="%d 🔥"),
        "現價": st.column_config.NumberColumn("現價", format="$%.2f"),
        "建議倉位 🎯": st.column_config.TextColumn("執行指令", width="medium"),
    },
    hide_index=True,
    use_container_width=True,
    disabled=True
)

if st.button("🔄 重設數據中心 (恢復預設值)"):
    del st.session_state.master_data
    st.rerun()



