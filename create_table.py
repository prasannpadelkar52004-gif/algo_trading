import psycopg2

DATABASE_URL = "postgresql://postgres:omQrLafTJTYjdwRonPmZDfGzeCudZFds@switchyard.proxy.rlwy.net:16123/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS nifty_5min_intraday_10days (
    time TIMESTAMP PRIMARY KEY,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION
);
""")

conn.commit()
cur.close()
conn.close()

print("Table created successfully")