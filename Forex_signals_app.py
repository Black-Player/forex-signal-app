import streamlit as st
import pandas as pd
import numpy as np
import ta
import json
import websocket
import threading
import time

st.set_page_config(page_title="Deriv Signal Generator", layout="centered")
st.title("📈 Deriv Synthetic Index Signal Generator")

# User Input
symbol = st.selectbox("Choose Instrument", [
    "R_100", "R_75", "R_50", "R_25", "R_10", "Boom_1000_Index", "Crash_1000_Index", "Volatility_75_Index"
])
granularity = st.selectbox("Timeframe", {"1m": 60, "5m": 300, "1h": 3600})
candles_limit = st.slider("Candles to Fetch", 50, 500, 100)

# Global data holder
candles = []

# Mapping
symbol_map = {
    "Volatility_75_Index": "R_75",
    "Boom_1000_Index": "boom_1000_index",
    "Crash_1000_Index": "crash_1000_index",
    "R_100": "R_100",
    "R_75": "R_75",
    "R_50": "R_50",
    "R_25": "R_25",
    "R_10": "R_10"
}

deriv_symbol = symbol_map[symbol]

# Function to run websocket
def fetch_candles():
    global candles
    ws = websocket.WebSocket()
    try:
        ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
        request = {
            "ticks_history": deriv_symbol,
            "adjust_start_time": 1,
            "count": candles_limit,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": granularity
        }
        ws.send(json.dumps(request))
        result = json.loads(ws.recv())
        if "candles" in result:
            candles = result["candles"]
    except Exception as e:
        st.error(f"WebSocket error: {e}")
    finally:
        ws.close()

# Run in thread so Streamlit doesn't freeze
thread = threading.Thread(target=fetch_candles)
thread.start()
thread.join()

# Build DataFrame
if not candles:
    st.error("❌ Failed to fetch candles from Deriv.")
else:
    df = pd.DataFrame(candles)
    df['time'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index("time", inplace=True)
    df = df[["open", "high", "low", "close"]].astype(float)

    if len(df) > 50:
        try:
            df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
            df["SMA_20"] = ta.trend.SMAIndicator(df["close"], window=20).sma_indicator()
            df["SMA_50"] = ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()

            last = df.iloc[-1]
            signal = "🔍 Neutral"
            reason = "Conditions not met for strong signal."

            if last["RSI"] < 30 and last["SMA_20"] > last["SMA_50"]:
                signal = "🟢 Buy"
                reason = "RSI oversold and short-term trend above long-term."
            elif last["RSI"] > 70 and last["SMA_20"] < last["SMA_50"]:
                signal = "🔴 Sell"
                reason = "RSI overbought and short-term trend below long-term."

            st.subheader(f"Signal for {symbol} on {granularity} chart")
            st.metric("Trading Signal", signal)
            st.caption(reason)

            st.line_chart(df[["close", "SMA_20", "SMA_50"]].dropna())

            with st.expander("🔎 View Latest Candle Data"):
                st.dataframe(df.tail(10))

        except Exception as e:
            st.error(f"⚠️ Error calculating indicators: {e}")
    else:
        st.warning("Not enough candle data to calculate signals.")
