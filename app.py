import pandas as pd
import yfinance as yf
import ta
import streamlit as st

# --- 1. 系統環境設定 ---
st.set_page_config(page_title="🛡️ 三輪過濾決策系統", layout="wide")

class MasterTraderSystem:
    def __init__(self):
        # 嚴格定義 11 個核心板塊，確保無遺漏
        self.sectors = {
            "AI 晶片": "NVDA", "國防科技": "KTOS", "軟體服務": "MSFT", 
            "大型電商": "AMZN", "電動車": "TSLA", "社群媒體": "META",
            "搜尋引擎": "GOOGL", "晶圓代工": "TSM", "金融科技": "PYPL",
            "網路設備": "CSCO", "串流影音": "NFLX"
        }

    def get_market_data(self, ticker):
        """核心數據抓取與指標計算 (解決 KTOS $95.31 與 NVDA 指標問題)"""
        try:
            # 抓取 6 個月的日 K 線
            df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if df is None or len(df) < 30: return None

            # --- F1 運算: 技術指標 (RSI 50 / MACD 零軸) ---
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['MACD'] = ta.trend.macd(df['Close'])
            df['MACD_Diff'] = ta.trend.macd_diff(df['Close']) # MACD 柱狀體
            
            # --- F3 運算: 生命線 (20MA) ---
            df['LifeLine'] = df['Close'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # --- F2 運算: 高手型態 (偵測長上影線與連黑) ---
            # 取得最新一根 K 線的實體與影線
            ope, close, high = latest['Open'], latest['Close'], latest['High']
            body = abs(ope - close)
            upper_shadow = high - max(ope, close)
            
            # 判斷邏輯：影線長度 > 實體長度的 1.5 倍視為長上影線
            has_shadow = upper_shadow > (body * 1.5) if body > 0 else upper_shadow > 0.5
            is_black = close < ope
            
            return {
                "price": float(close), "rsi": float(latest['RSI']),
                "macd": float(latest['MACD']), "macd_diff": float(latest['MACD_Diff']),
                "lifeline": float(latest['LifeLine']), "has_shadow": has_shadow, "black_k": 1 if is_black else 0
            }
        except Exception as e:
            return None

    def execute_three_wheels(self, d):
        """嚴格執行三輪過濾邏輯"""
        # Wheel 1: 技術指標 (MACD > 0, RSI > 50, 柱狀體 > 0)
        # NVDA 的 RSI 41.4 會在這裡被攔截為 False
        f1 = (d['macd'] > 0 and d['rsi'] > 50 and d['macd_diff'] > 0)
        
        # Wheel 2: 高手型態 (排除長上影線、排除黑K)
        f2 = (not d['has_shadow'] and d['black_k'] == 0)
        
        # Wheel 3: 生命線判定 (站穩/觸碰/破位)
        if d['price'] > d['lifeline'] * 1.01: 
            res, icon = "站穩", "☀️"
        elif d['price'] >= d['lifeline'] * 0.99: 
            res, icon = "觸碰", "☁️"
        else: 
            res, icon = "破位", "🌧️"
            
        return f1, f2, res, icon

    def generate_plain_text_analysis(self, f1, f2, f3_res, d):
        """將數據轉化為白話文階段分析"""
        if f3_res == "破位":
            return f"【空頭排列】已跌破生命線。目前下行趨勢明顯(RSI:{d['rsi']:.1f})，風險極大，嚴禁買入。"
        if not f1:
            return f"【動能背離】價格雖在生命線附近，但動能指標(RSI:{d['rsi']:.1f}/MACD)轉弱，多頭熄火。"
        if not f2:
            return "【高檔派發】指標雖強但型態不佳(長上影線/黑K)，顯示賣壓沉重，小心誘多陷阱。"
        return "【多頭攻擊】三指標共振且站穩生命線。結構最為健康，屬於標準的多頭續航階段。"

# --- 2. Streamlit 介面呈現 ---
st.title("🛡️ 11 大板塊「三輪過濾」決策系統")
st.write("數據來源：Yahoo Finance (實時更新)")

system = MasterTraderSystem()

if st.button("啟動 F1-F3 全板塊實時掃描"):
    results = []
    with st.status("正在獲取全球板塊實時數據...", expanded=True) as status:
        for name, ticker in system.sectors.items():
            st.write(f"正在計算 {name} ({ticker}) 指標...")
            data = system.get_market_data(ticker)
            if data:
                f1, f2, f3_res, f3_icon = system.execute_three_wheels(data)
                stage = system.generate_plain_text_analysis(f1, f2, f3_res, data)
                results.append({
                    "板塊名稱": name, "標的代號": ticker, "當前價格": round(data['price'], 2),
                    "F1/F2 狀態": f"{'OK' if f1 else 'NG'} / {'OK' if f2 else 'NG'}",
                    "F3 生命線": f"{f3_icon} {f3_res}", "階段判讀 (白話文)": stage
                })
        status.update(label="11 大板塊分析完成！", state="complete", expanded=False)

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("掃描過程中未能取得數據，請重新點擊按鈕。")



