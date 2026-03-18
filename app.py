
import pandas as pd
import yfinance as yf
import ta
import streamlit as st
import time

# --- 1. 系統環境設定 ---
st.set_page_config(page_title="🛡️ 三輪過濾決策系統", layout="wide")

class MasterTraderSystem:
    def __init__(self):
        self.sectors = {
            "AI 晶片": "NVDA", "國防科技": "KTOS", "軟體服務": "MSFT", 
            "大型電商": "AMZN", "電動車": "TSLA", "社群媒體": "META",
            "搜尋引擎": "GOOGL", "晶圓代工": "TSM", "金融科技": "PYPL",
            "網路設備": "CSCO", "串流影音": "NFLX"
        }

    def get_market_data(self, ticker):
        """強化版數據抓取：加入重試機制"""
        for _ in range(3):
            try:
                t = yf.Ticker(ticker)
                df = t.history(period="6mo", interval="1d")
                if df is not None and len(df) >= 20:
                    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
                    df['MACD'] = ta.trend.macd(df['Close'])
                    df['MACD_Diff'] = ta.trend.macd_diff(df['Close'])
                    df['LifeLine'] = df['Close'].rolling(window=20).mean()
                    
                    latest = df.iloc[-1]
                    ope, close, high = latest['Open'], latest['Close'], latest['High']
                    body = abs(ope - close)
                    upper_shadow = high - max(ope, close)
                    has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
                    
                    return {
                        "price": float(close), "rsi": float(latest['RSI']),
                        "macd": float(latest['MACD']), "macd_diff": float(latest['MACD_Diff']),
                        "lifeline": float(latest['LifeLine']), "has_shadow": has_shadow, "black_k": 1 if close < ope else 0
                    }
                time.sleep(1)
            except:
                time.sleep(1)
                continue
        return None

    def analyze(self, d):
        f1 = (d['macd'] > 0 and d['rsi'] > 50 and d['macd_diff'] > 0)
        f2 = (not d['has_shadow'] and d['black_k'] == 0)
        if d['price'] > d['lifeline'] * 1.01: res, icon = "站穩", "☀️"
        elif d['price'] >= d['lifeline'] * 0.99: res, icon = "觸碰", "☁️"
        else: res, icon = "破位", "🌧️"
        return f1, f2, res, icon

    def get_text(self, f1, f2, f3_res, d):
        if f3_res == "破位": return f"【空頭排列】已跌破生命線。趨勢極弱(RSI:{d['rsi']:.1f})，嚴禁買入。"
        if not f1: return f"【動能背離】RSI({d['rsi']:.1f})或MACD低於分界點，多頭動能不足。"
        if not f2: return "【高檔派發】出現長上影線或黑K，高手正在撤退，小心誘多。"
        return "【多頭攻擊】三指標共振且站穩生命線。結構健康，屬於標準多頭階段。"

# --- 2. 介面呈現 ---
st.title("🛡️ 11 大板塊「三輪過濾」決策系統")

system = MasterTraderSystem()

# --- 新增：Input 手動輸入欄位 ---
st.sidebar.header("🔍 自定義查詢")
user_input = st.sidebar.text_input("輸入股票代碼 (例如: AAPL, TSLA)", "").upper()
analyze_user = st.sidebar.button("分析自選股")

if analyze_user and user_input:
    with st.spinner(f'正在分析 {user_input}...'):
        data = system.get_market_data(user_input)
        if data:
            f1, f2, f3_res, f3_icon = system.analyze(data)
            stage = system.get_text(f1, f2, f3_res, data)
            st.sidebar.success(f"**{user_input} 結果：**")
            st.sidebar.write(f"價格: {data['price']:.2f} | F3: {f3_icon}{f3_res}")
            st.sidebar.info(stage)
        else:
            st.sidebar.error("找不到該代碼數據")

# --- 原有：11 大板塊掃描 ---
if st.button("啟動 F1-F3 11 大板塊實時全掃描"):
    results = []
    progress_text = st.empty()
    bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(system.sectors.items()):
        progress_text.text(f"正在分析: {name} ({ticker})...")
        data = system.get_market_data(ticker)
        if data:
            f1, f2, f3_res, f3_icon = system.analyze(data)
            stage = system.get_text(f1, f2, f3_res, data)
            results.append({"板塊": name, "代號": ticker, "價格": round(data['price'], 2),
                            "F1/F2": f"{'OK' if f1 else 'NG'} / {'OK' if f2 else 'NG'}",
                            "F3": f"{f3_icon} {f3_res}", "階段判讀": stage})
        bar.progress((i + 1) / 11)
    
    progress_text.empty()
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("目前無法抓取數據，請稍後重試。")


