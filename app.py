import streamlit as st
import yfinance as yf
#import pandas_ta 
import streamlit.components.v1 as components

st.set_page_config(page_title="三維戰略 V6.6", layout="wide")
T_LIST = "POET, TSM, AVGO, SOUN, NVDA, PLTR, OKLO, SMR, IONQ, TSLA, HIMS"
st.markdown("<h1 style='text-align: center; color: #007AFF;'>🛡️ 三維戰略系統 V6.6</h1>", unsafe_allow_html=True)

js = '<script>function openPrompt(){var i=window.prompt("代號：","POET,TSM");if(i)window.parent.postMessage({type:"streamlit:set_component_value",value:i},"*")}</script><button onclick="openPrompt()" style="background:#007AFF;color:white;padding:10px;border:none;border-radius:8px;width:100%">📝 修改監控名單</button>'
components.html(js, height=60)

def get_diag(c, p, b, avg):
    c_d = "✅ 方向明確，油門踩死" if c >= 70 else ("⚠️ 趨勢模糊，方向盤在抖" if c >= 40 else "❌ 正在倒車，非常危險")
    p_d = "✅ 地板紮實，大戶在撐" if p >= 70 else ("⚠️ 正在蓋地基，要耐心" if p >= 40 else "❌ 支撐已斷，套牢冤魂多")
    b_d = "✅ 買盤瘋搶，引擎噴火" if b >= 70 else ("⚠️ 沒熱度，大家在觀望" if b >= 40 else "❌ 能量枯竭，反彈是假的")
    if avg >= 75: return "🔥 【滿倉進攻】", "green", c_d, p_d, b_d
    elif avg >= 65: return "➕ 【分批加碼】", "blue", c_d, p_d, b_d
    elif 50 <= avg < 65: return "🔍 【減碼觀察】", "orange", c_d, p_d, b_d
    else: return "❌ 【全面撤退】", "red", c_d, p_d, b_d

@st.cache_data(ttl=300)
def analyze(ts_str):
    ts = [x.strip().upper() for x in ts_str.split(",") if x.strip()]
    raw = yf.download(ts, period="1y", group_by='ticker', progress=False)
    d_list = []
    for t in ts:
        try:
            df = raw[t].dropna()
            df.ta.macd(append=True); df.ta.rsi(append=True); df.ta.sma(length=20, append=True); df.ta.sma(length=60, append=True)
            l = df.iloc[-1]
            c = sum([40 if l['Close'] > l['SMA_20'] else 10, 60 if l['RSI_14'] > 50 else 20])
            p = 80 if l['Close'] > l['SMA_60'] else 30
            b = 80 if l['Volume'] > df['Volume'].tail(5).mean() else 30
            avg = int((c + p + b) / 3)
            res = get_diag(c, p, b, avg)
            d_list.append({"t":t,"avg":avg,"p":round(l['Close'],2),"o":res[0],"col":res[1],"c":res[2],"p_t":res[3],"b_t":res[4]})
        except: continue
    return d_list

data = analyze(T_LIST)
st.subheader("🌡️ 板塊氣候儀表板")
c1, c2, c3 = st.columns(3)
with c1: st.info(f"矽光子: ☀️ 晴 ({round(sum([i['avg'] for i in data if i['t'] in ['TSM','AVGO','POET']])/3)}分)")
with c2: st.warning(f"AI醫療: ⛅ 雲 ({round(sum([i['avg'] for i in data if i['t'] in ['HIMS','NVDA','PLTR']])/4)}分)")
with c3: st.error(f"量子/能源: ⛈️ 雨 ({round(sum([i['avg'] for i in data if i['t'] in ['IONQ','OKLO']])/2)}分)")
st.markdown("---")
st.subheader("📋 今日速報 Action Report")
s1, s2, s3 = st.columns(3)
with s1: st.success(f"🔥 進攻: {', '.join([i['t'] for i in data if i['avg'] >= 75])}")
with s2: st.info(f"➕ 加碼: {', '.join([i['t'] for i in data if 65 <= i['avg'] < 75])}")
with s3: st.error(f"❌ 撤退: {', '.join([i['t'] for i in data if i['avg'] < 55])}")
st.markdown("---")
for i in sorted(data, key=lambda x: x['avg'], reverse=True):
    with st.expander(f"💎 {i['t']} | ${i['p']} | 分數: {i['avg']}"):
        st.write(f"**建議：{i['o']}**")
        st.write(f"核心: {i['c']}"); st.write(f"型態: {i['p_t']}"); st.write(f"能量: {i['b_t']}")
