
import pandas as pd
import yfinance as yf
import ta
import streamlit as st
import time

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
        """強化版數據抓取：加入重試與偽裝機制"""
        # 嘗試最多 3 次
        for attempt in range(3):
            try:
                # 使用 yf.Ticker 物件來獲取數據，這比直接用 download 穩定
                t = yf.Ticker(ticker)
                # 抓取 1 個月的歷史數據
                df = t.history(period="1mo", interval="1d")
                
                if df is not None and len(df) >= 20:
                    # F1: 指標計算
                    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
                    df['MACD'] = ta.trend.macd(df['Close'])
                    df['MACD_Diff'] = ta.trend.macd_diff(df['Close'])
                    # F3: 生命線 (20MA)
                    df['LifeLine'] = df['Close'].rolling(window=20).mean()
                    
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    # F2: 型態判定
                    body = abs(latest['Open'] - latest['Close'])
                    upper_shadow = latest['High'] - max(latest['Open'], latest['Close'])
                    has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
                    is_black = latest['Close'] < latest['Open']
                    
                    return {
                        "price": float(latest['Close']), "rsi": float(latest['RSI']),
                        "macd": float(latest['MACD']), "macd_diff": float(latest['MACD_Diff']),
                        "lifeline": float(latest['LifeLine']), "has_shadow": has_shadow, "black_k": 1 if is_black else 0
                    }
                # 如果數據空，等 1 秒再試
                time.sleep(1)
            except:
                time.sleep(1)
                continue
        return None

    def execute_logic(self, d):
        f1 = (d['macd'] > 0 and d['rsi'] > 50 and d['macd_diff'] > 0)
        f2 = (not d['has_shadow'] and d['black_k'] == 0)
        if d['price'] > d['lifeline'] * 1.01: res, icon = "站穩", "☀️"
        elif d['price'] >= d['lifeline'] * 0.99: res, icon = "觸碰", "☁️"
        else: res, icon = "破位", "🌧️"
        return f1, f2, res, icon

    def get_text(self, f1, f2, f3_res, d):
        if f3_res == "破位": return f"【空頭排列】已跌破生命線。目前趨勢極弱(RSI:{d['rsi']:.1f})，嚴禁買入。"
        if not f1: return f"【動能背離】RSI({d['rsi']:.1f})或MACD低於分界點，多頭動能不足。"
        if not f2: return "【高檔派發】出現長上影線或黑K，高手正在撤退，小心誘多。"
        return "【多頭攻擊】三指標共振且站穩生命線。結構健康，屬於標準多頭階段。"

st.title("🛡️ 11 大板塊「三輪過濾」決策系統")
system = MasterTraderSystem()

if st.button("啟動 F1-F3 全板塊實時掃描"):
    results = []
    # 建立一個進度條
    progress_text = st.empty()
    bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(system.sectors.items()):
        progress_text.text(f"正在分析第 {i+1}/11 個板塊: {name} ({ticker})...")
        data = system.get_market_data(ticker)
        if data:
            f1, f2, f3_res, f3_icon = system.execute_logic(data)
            stage = system.get_text(f1, f2, f3_res, data)
            results.append({"板塊": name, "代號": ticker, "價格": round(data['price'], 2),
                            "F1/F2": f"{'OK' if f1 else 'NG'} / {'OK' if f2 else 'NG'}",
                            "F3": f"{f3_icon} {f3_res}", "階段判讀": stage})
        bar.progress((i + 1) / 11)
    
    progress_text.empty()
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("Yahoo Finance 伺服器目前拒絕連線。請稍候幾分鐘後，再次點擊按鈕重試。")



