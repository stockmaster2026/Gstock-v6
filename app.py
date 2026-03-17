import pandas as pd
import numpy as np
import time

# --- [ 1. 完整板塊定義：包含原有、量子與 AI 醫療 ] ---
# 我確保了這裡是一個完整的字典，不會漏掉任何一個板塊
watch_list = {
    "半導體板塊": ["NVDA", "TSM", "AMD", "AVGO", "ARM"],
    "科技龍頭股": ["AAPL", "MSFT", "AMZN", "GOOGL", "META"],
    "電動車板塊": ["TSLA", "RIVN", "LCID", "FSR"],
    "量子運算板塊": ["IONQ", "RGTI", "QUAN", "QBTS"],
    "AI 醫療板塊": ["RXRX", "SDGR", "ABSI", "HLTH", "GEHC"],
    "大盤參考": ["SPY", "QQQ", "VIX"]
}

# --- [ 2. 核心評分引擎：三個 Filter 的明細與加權 ] ---
def calculate_comprehensive_scores(ticker):
    """
    這裡執行您要求的三濾網邏輯：
    F1: 趨勢 (Trend) - 佔 40%
    F2: 動能 (Momentum) - 佔 30%
    F3: 成交量 (Volume) - 佔 30%
    """
    # 模擬數據 (實際對接時會在此抓取收盤價、RSI、成交量)
    f1_trend = np.random.randint(40, 100)
    f2_momentum = np.random.randint(35, 100)
    f3_volume = np.random.randint(30, 100)
    
    # 計算加權總分
    total_score = (f1_trend * 0.4) + (f2_momentum * 0.3) + (f3_volume * 0.3)
    
    return {
        "F1_Trend": f1_trend,
        "F2_Momentum": f2_momentum,
        "F3_Volume": f3_volume,
        "Total": round(total_score, 2)
    }

# --- [ 3. 晴雨表狀態判定 ] ---
def get_weather_icon(score):
    if score >= 80: return "☀️ 大太陽 (極強勢)"
    if score >= 65: return "🌤️ 晴時多雲 (偏多)"
    if score >= 50: return "☁️ 陰天 (盤整)"
    return "🌧️ 降雨 (弱勢)"

# --- [ 4. 主執行程序：修正 Input 與回應邏輯 ] ---
def main():
    print("\n" + "="*50)
    print("📈 投資組合三濾網評分 & 板塊晴雨表系統")
    print("="*50)
    
    # 修正：加上明顯的輸入提示，避免昨天反應的「輸入後無回應」問題
    print("\n[系統指令說明]")
    print("1. 輸入特定代號 (如: TSLA, IONQ) 查看單檔明細")
    print("2. 輸入 'ALL' 執行全板塊掃描並輸出晴雨表")
    print("3. 輸入 'EXIT' 結束程式")
    
    while True:
        user_input = input("\n👉 請輸入指令: ").strip().upper()
        
        if user_input == "EXIT":
            print("系統已關閉。")
            break
            
        if not user_input:
            print("⚠️ 偵測到空值，請輸入代號或 'ALL'。")
            continue

        # --- 情境 A: 執行全板塊掃描 ---
        if user_input == "ALL":
            print("\n🔄 正在掃描全板塊數據，請稍候...")
            all_results = []
            sector_stats = []
            
            for sector, tickers in watch_list.items():
                sector_scores = []
                for t in tickers:
                    s = calculate_comprehensive_scores(t)
                    all_results.append([sector, t, s["F1_Trend"], s["F2_Momentum"], s["F3_Volume"], s["Total"]])
                    sector_scores.append(s["Total"])
                
                avg_score = round(np.mean(sector_scores), 2)
                sector_stats.append([sector, avg_score, get_weather_icon(avg_score)])
            
            # 顯示個股表
            df_stocks = pd.DataFrame(all_results, columns=["板塊", "代碼", "趨勢(F1)", "動能(F2)", "量能(F3)", "總分"])
            print("\n【個股三濾網評分明細】")
            print(df_stocks.to_string(index=False))
            
            # 顯示晴雨表
            df_sectors = pd.DataFrame(sector_stats, columns=["板塊名稱", "平均分", "目前氣候"])
            print("\n【市場板塊晴雨表總覽】")
            print(df_sectors.to_string(index=False))
            print("\n" + "-"*50)

        # --- 情境 B: 查詢單一股票 (例如 TSLA) ---
        else:
            print(f"\n🔍 正在分析 {user_input} ...")
            s = calculate_comprehensive_scores(user_input)
            
            print(f"--- {user_input} 評分報告 ---")
            print(f"🔹 趨勢濾網 (F1): {s['F1_Trend']} 分")
            print(f"🔹 動能濾網 (F2): {s['F2_Momentum']} 分")
            print(f"🔹 成交量濾網 (F3): {s['F3_Volume']} 分")
            print(f"⭐ 加權總得分: {s['Total']} 分")
            print(f"🌈 晴雨建議: {get_weather_icon(s['Total'])}")
            print("-" * 30)

if __name__ == "__main__":
    main()





  



