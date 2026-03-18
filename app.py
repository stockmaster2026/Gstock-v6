import pandas as pd
import yfinance as yf
import ta
import streamlit as st

# 設定頁面
st.set_page_config(page_title="🛡️ 三輪過濾系統", layout="wide")

class MasterTraderSystem:
    def __init__(self):
        self.sectors = {
            "AI 晶片": "NVDA", "國防科技": "KTOS", "軟體服務": "MSFT", 
            "大型電商": "AMZN", "電動車": "TSLA", "社群媒體": "META",
            "搜尋引擎": "GOOGL", "晶圓代工": "TSM", "金融科技": "PYPL",
            "網路設備": "CSCO", "串流影音": "NFLX"
        }

    def get_data(self, ticker):
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty: return None

            # F1: 技術指標計算 (使用 ta 套件)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['MACD'] = ta.trend.macd(df['Close'])
            df['MACD_Diff'] = ta.trend.macd_diff(df['Close'])
            df['KD_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
            df['KD_D'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'])
            
            # F3: 生命線 (20MA)
            df['LifeLine'] = df['Close'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # F2: 型態判斷
            body = abs(latest['Open'] - latest['Close'])
            upper_shadow = latest['High'] - max(latest['Open'], latest['Close'])
            has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
            is_black = latest['Close'] < latest['Open']
            prev_black = prev['Close'] < prev['Open']

            return {
                "price": float(latest['Close']),
                "rsi": float(latest['RSI']),
                "macd": float(latest['MACD']),
                "macd_diff": float(latest['MACD_Diff']),
                "k": float(latest['KD_K']),
                "d": float(latest['KD_D']),
                "lifeline": float(latest['LifeLine']),
                "has_shadow": has_shadow,
                "black_k": 2 if (is_black and prev_black) else (1 if is_black else 0)
            }
        except:
            return None

    def analyze(self, d):
        # F1: MACD>0, RSI>50, MACD柱狀>0, KD金叉(K>D)
        f1 = (d['macd'] > 0 and d['rsi'] > 50 and d['macd_diff'] > 0 and d['k'] > d['d'])
        # F2: 排除長影線與連黑
        f2 = (not d['has_shadow'] and d['black_k'] < 2)
        # F3: 生命線判定
        if d['price'] > d['lifeline'] * 1.01:
            res, icon = "站穩", "☀️"
        elif d['price'] >= d['lifeline'] * 0.99:
            res, icon = "觸碰", "☁️"
        else:
            res, icon = "破位", "🌧️"
        return f1, f2, res, icon

    def get_text(self, f1, f2, f3_res, d):
        if f3_res == "破位":
            return f"【空頭排列】已跌破生命線。趨勢轉弱(RSI:{d['rsi']:.1f})，嚴禁買入。"
        if not f1:
            return "【動能背離】指標(MACD/RSI/KD)未達標或已死叉，多頭動能不足，建議觀望。"
        if not f2:
            return "【高檔派發】出現長上影線或連續黑K，賣壓沉重，小心誘多。"
        return "【多頭攻擊】三指標共振且站穩生命線，結構健康，屬於標準多頭階段。"

# --- 介面 ---
st.title("🛡️ 11 大板塊「三輪過濾」決策系統")
st.info("系統已針對 Python 3.14 環境完成相容性修正")

system = MasterTraderSystem()

if st.button("啟動 F1-F3 實時掃描"):
    results = []
    for name, ticker in system.sectors.items():
        data = system.get_data(ticker)
        if data:
            f1, f2, f3_res, f3_icon = system.analyze(data)
            stage = system.get_text(f1, f2, f3_res, data)
            results.append({
                "板塊": name, "代號": ticker, "價格": round(data['price'], 2),
                "F1/F2": f"{'OK' if f1 else 'NG'}/{'OK' if f2 else 'NG'}",
                "F3": f"{f3_icon} {f3_res}", "階段分析": stage
            })
    st.table(pd.DataFrame(results))





