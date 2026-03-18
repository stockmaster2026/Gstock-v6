
import datetime

class MasterTradingSystem:
    def __init__(self):
        self.report_date = "2026-03-17"
        # 實時數據校正 (修正 KTOS 價格與 NVDA 弱勢狀態)
        self.market_data = {
            "AI 晶片": {"ticker": "NVDA", "price": 120.45, "rsi": 41.4, "macd_v": -1.5, "macd_h": -0.2, "kd_k": 32, "kd_d": 48, "shadow": True, "black_k": 3, "lifeline": 135.0},
            "國防科技": {"ticker": "KTOS", "price": 95.31, "rsi": 43.5, "macd_v": -0.5, "macd_h": 0.1, "kd_k": 45, "kd_d": 40, "shadow": False, "black_k": 0, "lifeline": 95.0},
            "軟體服務": {"ticker": "MSFT", "price": 412.50, "rsi": 55.2, "macd_v": 2.1, "macd_h": 0.5, "kd_k": 72, "kd_d": 65, "shadow": False, "black_k": 0, "lifeline": 400.0},
            "大型電商": {"ticker": "AMZN", "price": 178.30, "rsi": 58.0, "macd_v": 1.8, "macd_h": 0.4, "kd_k": 75, "kd_d": 68, "shadow": False, "black_k": 0, "lifeline": 170.0},
            "電動車":   {"ticker": "TSLA", "price": 162.40, "rsi": 38.5, "macd_v": -3.2, "macd_h": -0.8, "kd_k": 25, "kd_d": 35, "shadow": True, "black_k": 4, "lifeline": 185.0},
            "社群媒體": {"ticker": "META", "price": 498.20, "rsi": 52.1, "macd_v": 0.8, "macd_h": 0.1, "kd_k": 55, "kd_d": 52, "shadow": False, "black_k": 1, "lifeline": 485.0},
            "搜尋引擎": {"ticker": "GOOGL", "price": 142.10, "rsi": 47.5, "macd_v": -0.2, "macd_h": -0.1, "kd_k": 42, "kd_d": 45, "shadow": False, "black_k": 1, "lifeline": 150.0},
            "晶圓代工": {"ticker": "TSM", "price": 142.80, "rsi": 45.3, "macd_v": -0.5, "macd_h": -0.1, "kd_k": 38, "kd_d": 42, "shadow": True, "black_k": 2, "lifeline": 155.0},
            "金融科技": {"ticker": "PYPL", "price": 61.50, "rsi": 42.1, "macd_v": -1.2, "macd_h": -0.3, "kd_k": 35, "kd_d": 40, "shadow": False, "black_k": 2, "lifeline": 68.0},
            "網路設備": {"ticker": "CSCO", "price": 48.50, "rsi": 51.2, "macd_v": 0.5, "macd_h": 0.1, "kd_k": 52, "kd_d": 48, "shadow": False, "black_k": 0, "lifeline": 47.0},
            "串流影音": {"ticker": "NFLX", "price": 615.40, "rsi": 62.1, "macd_v": 3.5, "macd_h": 0.8, "kd_k": 82, "kd_d": 75, "shadow": False, "black_k": 0, "lifeline": 590.0}
        }

    def execute_filters(self, data):
        # F1: 技術指標 (三位一體) - MACD > 0, RSI > 50, KD 金叉
        f1 = (data['macd_v'] > 0 and data['rsi'] > 50 and data['kd_k'] > data['kd_d'])
        
        # F2: 高手邏輯 - 排除長上影線、連續黑K
        f2 = (not data['shadow'] and data['black_k'] < 2)
        
        # F3: 生命線 (一票否決) - 站穩為☀️, 觸碰為☁️, 破位為🌧️
        if data['price'] > data['lifeline'] * 1.01:
            f3_status, f3_icon = "站穩", "☀️"
        elif data['price'] >= data['lifeline'] * 0.99:
            f3_status, f3_icon = "觸碰", "☁️"
        else:
            f3_status, f3_icon = "破位", "🌧️"
            
        return f1, f2, f3_status, f3_icon

    def translate_stage(self, f1, f2, f3_status):
        # 根據三層 Filter 的結果，轉化為白話文階段
        if f3_status == "破位":
            return "空頭確立：已跌破生命線，屬於逃命波或空頭排列，嚴禁買入。"
        if not f1:
            if f3_status == "觸碰":
                return "弱勢震盪：雖在生命線邊緣，但動能指標（RSI/MACD）太差，不具攻擊力。"
            return "技術轉弱：短線動能已失，目前正在找支撐，不宜進場。"
        if f1 and not f2:
            return "高檔賣壓：指標雖美，但出現長上影線或連續黑K，高手正在出貨，小心誘多。"
        if f1 and f2 and f3_status == "站穩":
            return "多頭強勢：三指標共振且站穩生命線，屬於標準的多頭攻擊階段。"
        return "觀察階段：目前處於多空交戰區，等待進一步方向訊號。"

    def run_analysis(self):
        print(f"=== {self.report_date} 11 大板塊三輪過濾分析報告 ===\n")
        print(f"{'板塊':<8} | {'標的':<6} | {'價格':<8} | {'F1/F2':<10} | {'F3(生命線)':<8} | {'當前階段 (白話文判讀)'}")
        print("-" * 110)
        
        for sector, data in self.market_data.items():
            f1, f2, f3_s, f3_i = self.execute_filters(data)
            stage_msg = self.translate_stage(f1, f2, f3_s)
            f1f2_status = f"{'OK' if f1 else 'NG'}/{'OK' if f2 else 'NG'}"
            
            print(f"{sector:<8} | {data['ticker']:<6} | {data['price']:<8.2f} | {f1f2_status:<10} | {f3_i} {f3_s:<4} | {stage_msg}")

# 執行系統
MasterTradingSystem().run_analysis()



