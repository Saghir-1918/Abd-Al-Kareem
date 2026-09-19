import streamlit as st
import requests
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="EUR/USD Pro Signal",
    page_icon="📊",
    layout="centered"
)

# =========================
# MOBILE-FRIENDLY CSS
# =========================
st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding: 1rem 1rem 2rem 1rem;
}

.hero {
    padding: 22px 18px;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,.25);
    text-align: center;
    margin-bottom: 18px;
}

.hero h1 {
    margin-bottom: 5px;
    font-size: 32px;
}

.signal-box {
    width: 100%;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 24px;
    margin: 18px 0;
    color: white;
    font-weight: 900;
    box-shadow: 0 6px 18px rgba(0,0,0,.20);
}

.signal-text {
    font-size: 52px;
    line-height: 1;
}

.signal-description {
    font-size: 15px;
    margin-top: 12px;
    font-weight: 500;
}

.buy {
    background: #16a34a;
}

.sell {
    background: #dc2626;
}

.wait {
    background: #eab308;
}

@media (max-width: 600px) {
    .hero h1 {
        font-size: 27px;
    }

    .signal-box {
        min-height: 135px;
        border-radius: 20px;
    }

    .signal-text {
        font-size: 46px;
    }

    .signal-description {
        font-size: 13px;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div class="hero">
    <h1>📊 EUR/USD PRO SIGNAL</h1>
    <div>EMA 9 + RSI 14 • 1 Minute</div>
</div>
""", unsafe_allow_html=True)

# =========================
# API KEY
# =========================
try:
    API_KEY = st.secrets["TWELVE_DATA_API_KEY"]
except Exception:
    st.error(
        "API key نہیں ملی۔ "
        "Streamlit → Settings → Secrets میں "
        "TWELVE_DATA_API_KEY شامل کریں۔"
    )
    st.stop()

# =========================
# CONTROLS
# =========================
col1, col2 = st.columns(2)

with col1:
    auto_refresh = st.checkbox(
        "🔄 Auto Refresh",
        value=True
    )

with col2:
    refresh_seconds = st.selectbox(
        "Refresh",
        [15, 30, 60],
        index=1,
        disabled=not auto_refresh
    )

# =========================
# GET CANDLE DATA
# =========================
url = "https://api.twelvedata.com/time_series"

params = {
    "symbol": "EUR/USD",
    "interval": "1min",
    "outputsize": 100,
    "apikey": API_KEY,
    "format": "JSON"
}

try:

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if "values" not in data:
        st.error("EUR/USD candle data نہیں ملا۔")
        st.json(data)
        st.stop()

    df = pd.DataFrame(data["values"])

    # =========================
    # CLEAN DATA
    # =========================
    for column in [
        "open",
        "high",
        "low",
        "close"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce"
    )

    df = (
        df
        .dropna(
            subset=[
                "datetime",
                "close"
            ]
        )
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    # =========================
    # EMA 9
    # =========================
    df["EMA9"] = (
        df["close"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    # =========================
    # RSI 14
    # =========================
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI14"] = (
        100 -
        (100 / (1 + rs))
    )

    # =========================
    # LAST CANDLE
    # =========================
    last = df.iloc[-1]

    price = float(last["close"])
    ema = float(last["EMA9"])
    rsi = float(last["RSI14"])

    # =========================
    # SIGNAL
    # =========================
    if price > ema and rsi >= 55:

        signal = "BUY"
        signal_class = "buy"
        icon = "🟢"

        description = (
            "Price EMA9 سے اوپر ہے اور "
            "RSI BUY conditions کو support کر رہا ہے۔"
        )

    elif price < ema and rsi <= 45:

        signal = "SELL"
        signal_class = "sell"
        icon = "🔴"

        description = (
            "Price EMA9 سے نیچے ہے اور "
            "RSI SELL conditions کو support کر رہا ہے۔"
        )

    else:

        signal = "WAIT"
        signal_class = "wait"
        icon = "🟡"

        description = (
            "BUY یا SELL conditions مکمل نہیں ہوئیں۔"
        )

    # =========================
    # BIG MOBILE SIGNAL
    # =========================
    st.markdown(
        f"""
        <div class="signal-box {signal_class}">
            <div class="signal-text">
                {icon} {signal}
            </div>
            <div class="signal-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================
    # METRICS
    # =========================
    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(
            "EUR/USD",
            f"{price:.6f}"
        )

    with m2:
        st.metric(
            "EMA 9",
            f"{ema:.6f}"
        )

    with m3:
        st.metric(
            "RSI 14",
            f"{rsi:.2f}"
        )

    # =========================
    # MARKET BIAS
    # =========================
    if price > ema:
        st.info("📈 Current Bias: **Bullish**")

    elif price < ema:
        st.info("📉 Current Bias: **Bearish**")

    else:
        st.info("➡️ Current Bias: **Neutral**")

    st.divider()

    # =========================
    # CHART
    # =========================
    st.subheader("📈 Price + EMA9")

    chart_df = (
        df
        .set_index("datetime")
        [["close", "EMA9"]]
        .tail(50)
    )

    st.line_chart(
        chart_df,
        height=320
    )

    # =========================
    # LATEST CANDLES
    # =========================
    st.subheader("🕯️ Latest Candles")

    table = df[
        [
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "EMA9",
            "RSI14"
        ]
    ].tail(10).copy()

    table["datetime"] = (
        table["datetime"]
        .dt.strftime("%Y-%m-%d %H:%M")
    )

    table = table.round({
        "open": 6,
        "high": 6,
        "low": 6,
        "close": 6,
        "EMA9": 6,
        "RSI14": 2
    })

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )

    # =========================
    # FOOTER
    # =========================
    st.divider()

    st.caption(
        f"Last candle: {last['datetime']}"
    )

    st.caption(
        "Data source: Twelve Data • "
        "Strategy: EMA9 + RSI14"
    )

    st.warning(
        "⚠️ یہ analytical signal tool ہے۔ "
        "Signal profit کی guarantee نہیں دیتا۔ "
        "Trade سے پہلے price/feed اور candle timing verify کریں۔"
    )

    # =========================
    # AUTO REFRESH
    # =========================
    if auto_refresh:

        st.markdown(
            f"""
            <meta
                http-equiv="refresh"
                content="{refresh_seconds}"
            >
            """,
            unsafe_allow_html=True
        )

        st.caption(
            f"🔄 Auto-refresh: ہر "
            f"{refresh_seconds} seconds"
        )

except requests.RequestException as error:

    st.error(
        f"Network/API Error: {error}"
    )

except Exception as error:

    st.error(
        f"App Error: {error}"
  )
