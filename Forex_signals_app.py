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

# --- Interval mapping for Yahoo
interval_map = {"1d": "1d", "1h": "60m", "15m": "15m"}

@st.cache_data
def get_data(pair, period, interval):
    try:
        data = yf.download(tickers=pair, period=f"{period}d", interval=interval)
        return data
    except Exception as e:
        st.error(f"Data download failed: {e}")
        return pd.DataFrame()

# --- Load data
df = get_data(pair, period, interval_map[timeframe])

# --- Validate data
if df.empty:
    st.error("⚠️ No data returned. Try changing the pair or timeframe.")
elif "Close" not in df.columns:
    st.error("⚠️ 'Close' column is missing from the data.")
elif df["Close"].isnull().sum() > 0:
    st.error("⚠️ Missing 'Close' price values. Try a different pair or period.")
else:
    df.dropna(subset=["Close"], inplace=True)

    if len(df) < 60:
        st.warning("⚠️ Not enough data to calculate indicators. Try a longer period.")
    else:
        try:
            # --- Indicators
            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
            df["SMA_50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()

            # --- Signal logic
            last = df.iloc[-1]
            signal = "🔍 Neutral"
            explanation = "Conditions are not strong enough for a Buy or Sell signal."

            if last["RSI"] < 30 and last["SMA_20"] > last["SMA_50"]:
                signal = "🟢 Buy"
                explanation = "RSI indicates oversold and short-term trend is above long-term trend."
            elif last["RSI"] > 70 and last["SMA_20"] < last["SMA_50"]:
                signal = "🔴 Sell"
                explanation = "RSI indicates overbought and short-term trend is below long-term trend."

            # --- Display
            st.subheader(f"Signal for {pair} on {timeframe.upper()}")
            st.metric(label="Trading Signal", value=signal)
            st.caption(explanation)

            # --- Chart
            st.line_chart(df[["Close", "SMA_20", "SMA_50"]].dropna())

            # --- Data Preview
            with st.expander("🔎 View raw price data"):
                st.dataframe(df.tail(15))

        except Exception as e:
            st.error(f"⚠️ Error calculating indicators: {e}")
