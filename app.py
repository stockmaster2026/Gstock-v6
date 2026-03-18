
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import streamlit as st

# --- 系統配置：減少監控壓力避免 OSError ---
st.set_page_config(page_title="🛡️ 三輪過濾系統", layout="wide")

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
        """獲取並計算 F1, F2, F3"""
        try:
            # 抓取數據
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty: return None

            # F1: 計算 RSI 與 MACD
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            
            # F3: 生命線 (20MA)
            df['LifeLine'] = ta.sma(df['Close'], length=20)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # F2: 型態判斷 (影線與連黑)
            high, low, close, ope = latest['High'], latest['Low'], latest['Close'], latest['Open']
            body = abs(ope - close)
            upper_shadow = high - max(ope, close)
            # 長上影線判定 (影線長於實體 1.5 倍)
            has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
            is_black = close < ope
            prev_black = prev['Close'] < prev['Open']

            return {
                "price": float(close),
                "rsi": float(latest['RSI']),
                "macd_val": float(latest.get('MACD_12_26_9', 0)),
                "macd_hist": float(latest.get('MACDh_12_26_9', 0)),
                "lifeline": float(latest['LifeLine']),
                "has_shadow": has_shadow,
                "black_k_count": 2 if (is_black and prev_black) else (1 if is_black else 0)
            }
        except:
            return None

    def analyze(self, data):
        # F1: MACD > 0, RSI > 50, MACD 柱狀 > 0
        f1 = (data['macd_val'] > 0 and data['rsi'] > 50 and data['macd_hist'] > 0)
        # F2: 排除長影線與連黑
        f2 = (not data['has_shadow'] and data['black_k_count'] < 2)
        # F3: 生命線一票否決
        if data['price'] > data['lifeline'] * 1.01:
            f3_res, f3_icon = "站穩", "☀️"
        elif data['price'] >= data['lifeline'] * 0.99:
            f3_res, f3_icon = "觸碰", "☁️"
        else:
            f3_res, f3_icon = "破位", "🌧️"
        return f1, f2, f3_res, f3_icon

    def get_plain_text(self, f1, f2, f3_res, data):
        """白話文階段判讀"""
        if f3_res == "破位":
            return f"【空頭排列】已跌破生命線。目前屬於下跌趨勢，指標嚴重轉弱(RSI:{data['rsi']:.1f})，嚴禁買入。"
        if not f1:
            return "【動能背離】雖然還在生命線附近，但指標(MACD/RSI)已死叉轉弱，多頭動能不足，不宜進場。"
        if f1 and not f2:
            return "【高檔派發】指標雖強，但出現長上影線或連續黑K，顯示賣壓沉重，高手正在撤退。"
        if f1 and f2 and f3_res == "站穩":
            return "【多頭攻擊】三指標共振且站穩生命線。結構最健康，屬於標準多頭階段。"
        return "【觀望階段】目前多空力量均衡，等待方向。"

# --- 執行介面 ---
st.title("🛡️ 11 大板塊「三輪過濾」決策系統")
st.write("更新日期：2026年3月17日")

system = MasterTraderSystem()

if st.button("啟動 F1-F3 全板塊掃描"):
    results = []
    progress_bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(system.sectors.items()):
        data = system.get_data(ticker)
        if data:
            f1, f2, f3_res, f3_icon = system.analyze(data)
            stage = system.get_plain_text(f1, f2, f3_res, data)
            results.append({
                "板塊": name, "代號": ticker, "當前價格": round(data['price'], 2),
                "F1/F2狀態": f"{'OK' if f1 else 'NG'} / {'OK' if f2 else 'NG'}",
                "F3生命線": f"{f3_icon} {f3_res}", "階段分析": stage
            })
        progress_bar.progress((i + 1) / 11)
    
    st.table(pd.DataFrame(results))



