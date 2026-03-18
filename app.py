
import pandas as pd
import yfinance as yf
import ta  # 更換為高相容性套件
import streamlit as st

# 頁面配置
st.set_page_config(page_title="🛡️ 三輪過濾決策系統", layout="wide")

class MasterTraderSystem:
    def __init__(self):
        # 11 個核心板塊標的
        self.sectors = {
            "AI 晶片": "NVDA", "國防科技": "KTOS", "軟體服務": "MSFT", 
            "大型電商": "AMZN", "電動車": "TSLA", "社群媒體": "META",
            "搜尋引擎": "GOOGL", "晶圓代工": "TSM", "金融科技": "PYPL",
            "網路設備": "CSCO", "串流影音": "NFLX"
        }

    def get_data(self, ticker):
        try:
            # 抓取 2026-03-17 的實時數據
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty: return None

            # F1: 指標計算 (使用 ta 套件)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['MACD'] = ta.trend.macd(df['Close'])
            df['MACD_Diff'] = ta.trend.macd_diff(df['Close'])
            
            # F3: 生命線 (20MA)
            df['LifeLine'] = df['Close'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # F2: 型態判斷 (影線與連黑)
            body = abs(latest['Open'] - latest['Close'])
            upper_shadow = latest['High'] - max(latest['Open'], latest['Close'])
            # 長上影線判定：影線長於實體 1.5 倍
            has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
            is_black = latest['Close'] < latest['Open']
            prev_black = prev['Close'] < prev['Open']

            return {
                "price": float(latest['Close']),
                "rsi": float(latest['RSI']),
                "macd": float(latest['MACD']),
                "macd_diff": float(latest['MACD_Diff']),
                "lifeline": float(latest['LifeLine']),
                "has_shadow": has_shadow,
                "black_k": 2 if (is_black and prev_black) else (1 if is_black else 0)
            }
        except:
            return None

    def analyze(self, d):
        # F1: 技術指標 (MACD > 0, RSI > 50, MACD柱狀 > 0)
        # 排除像 NVDA 這種 RSI 只有 41.4 的標的
        f1 = (d['macd'] > 0 and d['rsi'] > 50 and d['macd_diff'] > 0)
        
        # F2: 高手邏輯 (排除長上影線、連續黑K)
        f2 = (not d['has_shadow'] and d['black_k'] < 2)
        
        # F3: 生命線判定 (一票否決)
        if d['price'] > d['lifeline'] * 1.01:
            res, icon = "站穩", "☀️"
        elif d['price'] >= d['lifeline'] * 0.99:
            res, icon = "觸碰", "☁️"
        else:
            res, icon = "破位", "🌧️"
        return f1, f2, res, icon

    def get_stage_text(self, f1, f2, f3_res, d):
        # 白話文階段判讀
        if f3_res == "破位":
            return f"【空頭排列】已跌破生命線。目前趨勢極弱 (RSI:{d['rsi']:.1f})，嚴禁入場買進。"
        if not f1:
            return f"【動能背離】雖然還在生命線附近，但 RSI({d['rsi']:.1f}) 或 MACD 已轉弱，多頭動能不足。"
        if not f2:
            return "【高檔派發】指標雖強但型態不佳 (長上影線/連黑)，賣壓沉重，小心誘多陷阱。"
        return "【多頭攻擊】三指標共振且站穩生命線。結構健康，屬於標準的多頭續攻階段。"

# --- UI 介面 ---
st.title("🛡️ 11 大板塊「三輪過濾」決策系統")
st.write(f"當前系統日期：2026年3月17日")

system = MasterTraderSystem()

if st.button("啟動 F1-F3 11 大板塊實時掃描"):
    results = []
    with st.spinner('正在分析市場數據...'):
        for name, ticker in system.sectors.items():
            data = system.get_data(ticker)
            if data:
                f1, f2, f3_res, f3_icon = system.analyze(data)
                stage = system.get_stage_text(f1, f2, f3_res, data)
                results.append({
                    "板塊": name, "代號": ticker, "目前價格": round(data['price'], 2),
                    "F1/F2": f"{'OK' if f1 else 'NG'} / {'OK' if f2 else 'NG'}",
                    "F3": f"{f3_icon} {f3_res}", "階段分析 (白話文)": stage
                })
        
        if results:
            st.table(pd.DataFrame(results))



