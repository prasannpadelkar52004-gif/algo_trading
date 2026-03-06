import pandas as pd
import psycopg2
from io import StringIO

print("Loading CSV...")

df = pd.read_csv("nifty_5min_intraday_10days.csv")

df["time"] = pd.to_datetime(df["time"])

print("Rows found:", len(df))

# Convert dataframe to CSV buffer
buffer = StringIO()
df.to_csv(buffer, index=False, header=False)
buffer.seek(0)

print("Connecting to database...")

conn = psycopg2.connect(
    "postgresql://postgres:omQrLafTJTYjdwRonPmZDfGzeCudZFds@switchyard.proxy.rlwy.net:16123/railway"
)

cur = conn.cursor()

print("Uploading data...")

cur.copy_expert(
    """
    COPY nifty_5min_intraday_10days(time, open, high, low, close)
    FROM STDIN WITH CSV
    """,
    buffer
)

conn.commit()

cur.close()
conn.close()

print("✅ CSV uploaded successfully!")