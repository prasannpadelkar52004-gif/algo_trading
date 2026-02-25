import eventlet
eventlet.monkey_patch()

import os
from urllib.parse import urlparse
from flask import Flask, render_template
from flask_socketio import SocketIO
import psycopg2

# --------------------------------------------------
# APP
# --------------------------------------------------

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise Exception("DATABASE_URL not set!")

conn = psycopg2.connect(database_url)
cur = conn.cursor()

# --------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------

candles = []
candle_index = 0
stream_started = False

# --------------------------------------------------
# SUPER TREND (Correct TradingView Logic)
# --------------------------------------------------

def calculate_supertrend(data, period=10, multiplier=3):

    trs = []
    atr = []
    final_upperband = []
    final_lowerband = []
    supertrend = []
    trend = []

    for i in range(len(data)):

        high = data[i]["high"]
        low = data[i]["low"]
        close = data[i]["close"]

        if i == 0:
            trs.append(high - low)
            atr.append(high - low)
            final_upperband.append(0)
            final_lowerband.append(0)
            supertrend.append(None)
            trend.append(True)
            continue

        prev_close = data[i-1]["close"]

        # True Range
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        trs.append(tr)

        # ATR (RMA)
        if i < period:
            atr.append(sum(trs) / len(trs))
        else:
            atr_val = (atr[i-1] * (period - 1) + tr) / period
            atr.append(atr_val)

        hl2 = (high + low) / 2
        basic_upper = hl2 + multiplier * atr[i]
        basic_lower = hl2 - multiplier * atr[i]

        if i == 1:
            final_upperband.append(basic_upper)
            final_lowerband.append(basic_lower)
        else:

            if basic_upper < final_upperband[i-1] or prev_close > final_upperband[i-1]:
                final_upperband.append(basic_upper)
            else:
                final_upperband.append(final_upperband[i-1])

            if basic_lower > final_lowerband[i-1] or prev_close < final_lowerband[i-1]:
                final_lowerband.append(basic_lower)
            else:
                final_lowerband.append(final_lowerband[i-1])

        # Trend Flip
        if trend[i-1]:
            trend.append(close >= final_lowerband[i])
        else:
            trend.append(close > final_upperband[i])

        # Supertrend value
        if trend[i]:
            supertrend.append(final_lowerband[i])
        else:
            supertrend.append(final_upperband[i])

    return supertrend, trend


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_candles():
    global candles

    cur.execute("""
        SELECT time, open, high, low, close
        FROM nifty_5min_intraday_10days
        ORDER BY time
    """)

    rows = cur.fetchall()

    candles = [{
        "time": int(r.time.timestamp()),  # MUST BE SECONDS
        "open": float(r.open),
        "high": float(r.high),
        "low": float(r.low),
        "close": float(r.close)
    } for r in rows]

    st_values, trend_values = calculate_supertrend(candles, 10, 3)

    for i in range(len(candles)):
        candles[i]["supertrend"] = st_values[i]
        candles[i]["trend"] = trend_values[i]

    print("✅ Data Loaded with SuperTrend")


# --------------------------------------------------
# STREAM
# --------------------------------------------------

def stream_data():
    global candle_index

    while candle_index < len(candles):
        socketio.emit("candle", candles[candle_index])
        candle_index += 1
        socketio.sleep(0.5)


@socketio.on("connect")
def on_connect():
    global stream_started, candle_index

    if not stream_started:
        candle_index = 0
        socketio.start_background_task(stream_data)
        stream_started = True


# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":
    load_candles()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
