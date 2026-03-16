import eventlet
eventlet.monkey_patch()

import os
import psycopg2
from flask import Flask, render_template
from flask_socketio import SocketIO

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

database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:omQrLafTJTYjdwRonPmZDfGzeCudZFds@switchyard.proxy.rlwy.net:16123/railway"
)

# --------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------


candles = []
candle_index = 0
stream_started = False

# --------------------------------------------------
# SUPER TREND
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

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        trs.append(tr)

        if i < period:
            atr.append(sum(trs) / len(trs))
        else:
            atr.append((atr[i-1] * (period - 1) + tr) / period)

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

        if trend[i-1]:
            trend.append(close >= final_lowerband[i])
        else:
            trend.append(close > final_upperband[i])

        if trend[i]:
            supertrend.append(final_lowerband[i])
        else:
            supertrend.append(final_upperband[i])

    return supertrend, trend


# --------------------------------------------------
# LOAD HISTORY
# --------------------------------------------------

def load_candles():

    global candles

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    cur.execute("""
        SELECT time, open, high, low, close
        FROM nifty_5min_intraday_10days
        ORDER BY time
    """)

    rows = cur.fetchall()

    candles = [{
        "time": int(r[0].timestamp()),
        "open": float(r[1]),
        "high": float(r[2]),
        "low": float(r[3]),
        "close": float(r[4])
    } for r in rows]

    st_values, trend_values = calculate_supertrend(candles, 10, 3)

    for i in range(len(candles)):
        candles[i]["supertrend"] = st_values[i]
        candles[i]["trend"] = trend_values[i]

    print("✅ Loaded candles:", len(candles))

    cur.close()
    conn.close()


# --------------------------------------------------
# STREAM HISTORY
# --------------------------------------------------

def stream_history():

    global candle_index

    while candle_index < len(candles):

        socketio.emit("candle", candles[candle_index])

        candle_index += 1

        socketio.sleep(0.4)


# --------------------------------------------------
# STREAM LIVE
# --------------------------------------------------

def stream_live_updates():

    global candles

    last_time = candles[-1]["time"]

    while True:

        try:

            conn = psycopg2.connect(database_url)
            cur = conn.cursor()

            cur.execute("""
                SELECT time, open, high, low, close
                FROM nifty_5min_intraday_10days
                ORDER BY time DESC
                LIMIT 1
            """)

            r = cur.fetchone()

            if r:

                candle_time = int(r[0].timestamp())

                if candle_time != last_time:

                    new_candle = {
                        "time": candle_time,
                        "open": float(r[1]),
                        "high": float(r[2]),
                        "low": float(r[3]),
                        "close": float(r[4])
                    }

                    candles.append(new_candle)

                    st_values, trend_values = calculate_supertrend(candles, 10, 3)

                    new_candle["supertrend"] = st_values[-1]
                    new_candle["trend"] = trend_values[-1]

                    socketio.emit("candle", new_candle)

                    last_time = candle_time

            cur.close()
            conn.close()

        except Exception as e:
            print("DB ERROR:", e)

        socketio.sleep(2)


# --------------------------------------------------
# CLIENT CONNECT
# --------------------------------------------------

@socketio.on("connect")
def on_connect():

    global stream_started

    print("Client connected")

    # Send history to this client
    socketio.start_background_task(stream_history)

    # Start live updates only once
    if not stream_started:

        socketio.start_background_task(stream_live_updates)
        stream_started = True


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

load_candles()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    socketio.run(app, host="0.0.0.0", port=port)