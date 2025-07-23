import streamlit as st
import pandas as pd
import json
import websocket
import ta
import threading

st.set_page_config(page_title="Deriv Signal Generator", layout="centered")
st.title("📈 Deriv Signal Generator (Live Data)")

# === User Inputs ===
symbols = {
    "Volatility 75 Index": "volatility_75_index",
    "Boom 1000 Index": "boom_1000_index",
    "Crash 1000 Index": "crash_1000_index"
}

symbol_name = st.selectbox("Select Instrument", list(symbols.keys()))
symbol = symbols[symbol_name]

granularities = {
    "1 Minute": 60,
    "5 Minutes": 300,
    "1 Hour": 3600
}
gran_label = st.selectbox("Select Timeframe", list(granularities.keys()))
granularity = granularities[gran_label]

count = st.slider("Number of Candles", 50, 500, 100)

# === Global candle holder ===
candles_data = []

def fetch_candles():
    global candles_data
    try:
        ws = websocket.WebSocket()
        ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")

        request = {
            "ticks_history": symbol,
            "style": "candles",
            "granularity": granularity,
            "count": count,
            "end": "latest"
        }

        ws.send(json.dumps(request))

        while True:
            msg = json.loads(ws.recv())
            if "candles" in msg:
                candles_data = msg["candles"]
                break
            elif "error" in msg:
                st.error(f"❌ API Error: {msg['error']['message']}")
                break

        ws.close()
    except Exception as e:
        st.error(f"WebSocket Error: {e}")

# === Run fetch in thread ===
thread = threading.Thread(target=fetch_candles)
thread.start()
thread.join()

# === Process Candles ===
if not candles_data:
    st.error("❌ Failed to fetch candles. Try changing symbol or timeframe.")
else:
    df = pd.DataFrame(candles_data)
    df["time"] = pd.to_datetime(df["epoch"], unit="s")
    df.set_index("time", inplace=True)
    df = df[["open", "high", "low", "close"]].astype(float)

    # === Calculate Indicators ===
    try:
        df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
        df["SMA_20"] = ta.trend.SMAIndicator(df["close"], window=20).sma_indicator()
        df["SMA_50"] = ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()

        last = df.iloc[-1]
        signal = "🔍 Neutral"
        reason = "No strong signal."

        if last["RSI"] < 30 and last["SMA_20"] > last["SMA_50"]:
            signal = "🟢 Buy"
            reason = "RSI oversold and SMA 20 > SMA 50."
        elif last["RSI"] > 70 and last["SMA_20"] < last["SMA_50"]:
            signal = "🔴 Sell"
            reason = "RSI overbought and SMA 20 < SMA 50."

        st.metric("Signal", signal)
        st.caption(reason)
        st.line_chart(df[["close", "SMA_20", "SMA_50"]].dropna())

        with st.expander("📊 Show Data"):
            st.dataframe(df.tail(10))

    except Exception as e:
        st.error(f"⚠️ Indicator calculation error: {e}")
