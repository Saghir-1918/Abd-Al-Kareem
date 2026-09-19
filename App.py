
import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="EUR/USD Signal Bot",
    page_icon="📊",
    layout="centered"
)

st.title("📊 EUR/USD Signal Bot")
st.caption("EMA9 + RSI14 | 1 Minute")

# API key محفوظ طریقے سے Streamlit Secrets سے آئے گی
API_KEY = st.secrets["TWELVE_DATA_API_KEY"]

url = "https://api.twelvedata.com/time_series"

params = {
    "symbol": "EUR/USD",
    "interval": "1min",
    "outputsize": 100,
    "apikey": API_KEY,
    "format": "JSON"
}

try:
    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if "values" not in data:
        st.error("Data نہیں مل رہا۔ API settings check کریں۔")
        st.write(data)
        st.stop()

    df = pd.DataFrame(data["values"])

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    # EMA 9
    df["EMA9"] = df["close"].ewm(
        span=9,
        adjust=False
    ).mean()

    # RSI 14
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]

    price = float(last["close"])
    ema = float(last["EMA9"])
    rsi = float(last["RSI14"])

    if price > ema and rsi >= 55:
        signal = "BUY"
    elif price < ema and rsi <= 45:
        signal = "SELL"
    else:
        signal = "WAIT"

    st.metric("EUR/USD Price", f"{price:.6f}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("EMA9", f"{ema:.6f}")

    with col2:
        st.metric("RSI14", f"{rsi:.2f}")

    st.divider()

    if signal == "BUY":
        st.success("🟢 BUY")
    elif signal == "SELL":
        st.error("🔴 SELL")
    else:
        st.warning("🟡 WAIT")

    st.write("Candle:", last["datetime"])

    st.divider()

    st.subheader("Latest Candles")

    st.dataframe(
        df[
            ["datetime", "open", "high", "low", "close", "EMA9", "RSI14"]
        ].tail(10),
        use_container_width=True
    )

except Exception as e:
    st.error(f"Error: {e}")
