# forex_signals_app.py

import yfinance as yf
import pandas as pd
import streamlit as st
import ta

st.set_page_config(page_title="Forex Signal Generator", layout="centered")

st.title("📈 Forex Signal Generator")
st.markdown("Select a Forex pair and timeframe to generate simple buy/sell signals.")

# --- User input
pair = st.selectbox("Select Forex Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "XAUUSD=X"])
timeframe = st.selectbox("Select Timeframe", ["1d", "1h", "15m"])
period = st.slider("Lookback Period (days)", 5, 100, 30)

# --- Download data
@st.cache_data
def get_data(pair, period, interval):
    data = yf.download(tickers=pair, period=f"{period}d", interval=interval)
    return data

interval_map = {"1d": "1d", "1h": "60m", "15m": "15m"}
df = get_data(pair, period, interval_map[timeframe])

if df.empty:
    st.error("No data found.")
else:
    # --- Apply indicators
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
    df["SMA_50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()

    # --- Generate Signal
    last_row = df.iloc[-1]
    signal = "🔍 Neutral"
    explanation = ""

    if last_row["RSI"] < 30 and last_row["SMA_20"] > last_row["SMA_50"]:
        signal = "🟢 Buy"
        explanation = "RSI indicates oversold and short-term trend is above long-term trend."
    elif last_row["RSI"] > 70 and last_row["SMA_20"] < last_row["SMA_50"]:
        signal = "🔴 Sell"
        explanation = "RSI indicates overbought and short-term trend is below long-term trend."

    # --- Display results
    st.subheader(f"Signal for {pair} on {timeframe.upper()}")
    st.metric(label="Trading Signal", value=signal)
    st.write(explanation)

    # --- Chart
    st.line_chart(df[["Close", "SMA_20", "SMA_50"]].dropna())
