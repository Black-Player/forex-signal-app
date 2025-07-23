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

# --- Validate data
if df.empty or "Close" not in df.columns or df["Close"].isnull().sum() > 0:
    st.error("No valid data found or data contains missing values.")
else:
    df.dropna(subset=["Close"], inplace=True)

    if len(df) < 60:
        st.warning("Not enough data to calculate indicators. Try a longer period.")
    else:
        try:
            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
            df["SMA_50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()

            last_row = df.iloc[-1]
            signal = "🔍 Neutral"
            explanation = ""

            if last_row["RSI"] < 30 and last_row["SMA_20"] > last_row["SMA_50"]:
                signal = "🟢 Buy"
                explanation = "RSI indicates oversold and short-term trend is above long-term trend."
            elif last_row["RSI"] > 70 and last_row["SMA_20"] < last_row["SMA_50"]:
                signal = "🔴 Sell"
                explanation = "RSI indicates overbought and short-term trend is below long-term trend."

            st.subheader(f"Signal for {pair} on {timeframe.upper()}")
            st.metric(label="Trading Signal", value=signal)
            st.write(explanation)

            st.line_chart(df[["Close", "SMA_20", "SMA_50"]].dropna())

        except Exception as e:
            st.error(f"Indicator calculation failed: {e}")
