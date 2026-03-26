
import streamlit as st

# --- 核心：卡片渲染函數 (請直接替換妳原本 render_card 的部分) ---
def render_card_v32(ticker, df):
    # 假設 df 已經包含了過去 5 天的資料
    latest = df.iloc[-1]
    ps_score = latest['ps']
    
    # 提取軌跡 (自動從妳的實時 df 累積，嚴禁綁死)
    ps_hist = "→".join(df['ps'].astype(str).tolist())
    # SBUY 軌跡 (原本 AWI 的五日狀態)
    sbuy_hist = " ".join(["🔥" if s else "❄️" for s in df['sbuy'].tolist()])
    
    # 顏色判定邏輯 (與妳早上版本一致)
    if ps_score >= 9.0: bg, txt, label = "#1E5631", "white", "🚀 起飛衝鋒"
    elif ps_score >= 7.0: bg, txt, label = "#77DD77", "black", "🚩 趨勢啟動"
    elif ps_score >= 5.0: bg, txt, label = "#FFFFFF", "black", "✨ 完美伏擊"
    else: bg, txt, label = "#6F4E37", "white", "💀 快逃命啊"

    fire_icon = "🔥" if latest['sbuy'] else "❄️"

    # HTML 密集封裝 (修正代碼外噴問題)
    card_html = f"""
    <div style="background-color:{bg}; border-radius:10px; padding:10px; color:{txt}; border:1px solid #ddd; margin-bottom:10px; line-height:1.1; font-family: sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:16px;">{ticker}</b>
            <span style="font-size:16px;">{fire_icon}</span>
        </div>
        <div style="font-size:26px; font-weight:bold; margin:4px 0;">${latest['Price']}</div>
        
        <div style="font-size:12px; border-top:0.5px solid {txt}66; padding-top:5px; font-weight:bold;">
            PS: {ps_score} <span style="font-size:10px; font-weight:normal; opacity:0.8;">({ps_hist})</span>
        </div>
        
        <div style="display:flex; justify-content:space-between; font-size:10px; margin-top:5px;">
            <span>X1:{latest['X1']}(30%)</span>
            <span>X2:{latest['X2']}(40%)</span>
            <span>X3:{latest['X3']}(30%)</span>
        </div>

        <div style="font-size:10px; margin-top:8px; padding:4px; border-left:3px solid {txt}; background:rgba(0,0,0,0.03);">
            <b>SBUY 五日累積:</b><br>
            <span style="font-size:14px; letter-spacing:2px;">{sbuy_hist}</span>
        </div>
        
        <div style="font-size:11px; margin-top:8px; font-weight:bold; text-align:right;">
            {label}
        </div>
    </div>
    """
    # ❗ 重要：啟用 unsafe_allow_html 確保彩色顯示
    st.markdown(card_html, unsafe_allow_html=True)

# --- 佈局部分：請維持妳早上的 col_left, col_right 架構 ---
# 只需在呼叫渲染的地方使用 render_card_v32(ticker, df)
