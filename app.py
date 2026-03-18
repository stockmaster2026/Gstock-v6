
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import streamlit as st

class MasterTraderSystem:
    def __init__(self):
        # 定義 11 個核心板塊與對應標的
        self.sector_map = {
            "AI 晶片": "NVDA", "國防科技": "KTOS", "軟體服務": "MSFT", 
            "大型電商": "AMZN", "電動車": "TSLA", "社群媒體": "META",
            "搜尋引擎": "GOOGL", "晶圓代工": "TSM", "金融科技": "PYPL",
            "網路設備": "CSCO", "串流影音": "NFLX"
        }

    def fetch_and_calculate(self, ticker):
        """抓取數據並計算 F1, F2, F3 所需指標"""
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty: return None

            # 計算 F1: RSI 與 MACD
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            
            # 計算 F3: 生命線 (以 20MA 為基準)
            df['LifeLine'] = ta.sma(df['Close'], length=20)
            
            # 取得最新一筆數據
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # F2 邏輯: 偵測長上影線與連黑
            body = abs(latest['Open'] - latest['Close'])
            upper_shadow = latest['High'] - max(latest['Open'], latest['Close'])
            has_shadow = upper_shadow > (body * 1.5) # 長上影線定義
            is_black_k = latest['Close'] < latest['Open']
            prev_black_k = prev['Close'] < prev['Open']

            return {
                "price": float(latest['Close']),
                "rsi": float(latest['RSI']),
                "macd_val": float(latest['MACD_12_26_9']),
                "macd_hist": float(latest['MACDh_12_26_9']),
                "lifeline": float(latest['LifeLine']),
                "has_shadow": has_shadow,
                "black_k_count": 2 if (is_black_k and prev_black_k) else (1 if is_black_k else 0)
            }
        except Exception as e:
            return None

    def analyze_wheels(self, data):
        """嚴格執行 F1, F2, F3 過濾邏輯"""
        # F1: 技術指標 (MACD > 0, RSI > 50, MACD 柱狀體 > 0)
        f1_pass = (data['macd_val'] > 0 and data['rsi'] > 50 and data['macd_hist'] > 0)
        
        # F2: 高手邏輯 (排除長上影線、連續黑K)
        f2_pass = (not data['has_shadow'] and data['black_k_count'] < 2)
        
        # F3: 生命線 (一票否決)
        if data['price'] > data['lifeline'] * 1.01:
            f3_res, f3_icon = "站穩", "☀️"
        elif data['price'] >= data['lifeline'] * 0.99:
            f3_res, f3_icon = "觸碰", "☁️"
        else:
            f3_res, f3_icon = "破位", "🌧️"
            
        return f1_pass, f2_pass, f3_res, f3_icon

    def get_plain_text_stage(self, f1, f2, f3_res, data):
        """輸出白話文階段分析"""
        if f3_res == "破位":
            return "【空頭排列】已跌破生命線。目前屬於下跌趨勢，指標嚴重轉弱（RSI: {:.1f}），嚴禁買入。".format(data['rsi'])
        if not f1:
            return "【動能背離】雖然還在生命線附近，但 RSI 或 MACD 已死叉轉弱，多頭動能不足，不宜進場。"
        if f1 and not f2:
            return "【高檔派發】指標雖強，但出現長上影線或連黑，顯示上方賣壓沉重，高手正在撤退。"
        if f1 and f2 and f3_res == "站穩":
            return "【多頭攻擊】三指標共振且站穩生命線。目前結構最健康，屬於標準多頭階段。"
        return "【區間震盪】多空不明，建議觀望。"

# --- Streamlit 介面呈現 ---
st.set_page_config(layout="wide")
st.title("🛡️ 11 大板塊「三輪過濾」實時監控系統")
system = MasterTraderSystem()

if st.button("開始掃描全球板塊"):
    results = []
    for sector, ticker in system.sector_map.items():
        data = system.fetch_and_calculate(ticker)
        if data:
            f1, f2, f3_res, f3_icon = system.analyze_wheels(data)
            stage = system.get_plain_text_stage(f1, f2, f3_res, data)
            results.append({
                "板塊": sector, "標代號": ticker, "當前價格": round(data['price'], 2),
                "F1/F2": f"{'OK' if f1 else 'NG'}/{'OK' if f2 else 'NG'}",
                "F3生命線": f"{f3_icon} {f3_res}", "階段判讀": stage
            })
    
    st.table(pd.DataFrame(results))



