import psycopg2
from datetime import datetime
import random

DATABASE_URL = "postgresql://postgres:omQrLafTJTYjdwRonPmZDfGzeCudZFds@switchyard.proxy.rlwy.net:16123/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Example candle
time = datetime.now()
open_price = random.uniform(22100, 22200)
high_price = open_price + random.uniform(5, 20)
low_price = open_price - random.uniform(5, 20)
close_price = random.uniform(low_price, high_price)

cur.execute("""
INSERT INTO nifty_5min_intraday_10days (time, open, high, low, close)
VALUES (%s, %s, %s, %s, %s)
""", (time, open_price, high_price, low_price, close_price))

conn.commit()

cur.close()
conn.close()

print("Candle inserted successfully")