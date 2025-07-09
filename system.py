import time
import pandas as pd
from dhanhq import dhanhq, marketfeed
from dotenv import load_dotenv
import os

# Import SendEmail class
from send_email import SendEmail

load_dotenv()

# Config - now loaded from environment variables
CLIENT_ID = os.environ.get("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.environ.get("DHAN_ACCESS_TOKEN")
SEC_ID = "13"  # Nifty 50

# Setup WebSocket
ctx = dhanhq(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
feed = marketfeed(ctx, mode=marketfeed.Full)

# Email sender instance
emailer = SendEmail()

# Data containers
ticks = []
df5 = pd.DataFrame(columns=["open","high","low","close","volume"], dtype=float)

current_min = None

def on_tick(t):
    global current_min, ticks, df5
    ts_min = t.timestamp // 60000 * 60000

    if current_min is None:
        current_min = ts_min
    if ts_min != current_min:
        finalize_minute(current_min)
        ticks = []
        current_min = ts_min

    ticks.append((t.LTP, t.volume))

def finalize_minute(min_ts):
    global df5
    if not ticks:
        return
    P, V = zip(*ticks)
    candle = {
        "open": P[0], "high": max(P), "low": min(P),
        "close": P[-1], "volume": sum(V)
    }
    df5.loc[min_ts] = candle

    # Keep only last 20 candles
    if len(df5) > 20:
        df5 = df5.iloc[-20:]

    if len(df5) >= 5:
        check_signal(min_ts)

def check_signal(min_ts):
    sub = df5.iloc[-5:]
    ema5 = sub["close"].ewm(span=5).mean().iloc[-1]
    sma20 = df5["close"].rolling(20).mean().iloc[-1] if len(df5) >= 20 else df5["close"].mean()
    vwap = (df5["close"] * df5["volume"]).sum() / df5["volume"].sum()
    delta = df5["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14).mean().iloc[-1]
    loss = (-delta).clip(lower=0).ewm(alpha=1/14).mean().iloc[-1]
    rs = gain / (loss if loss>0 else 1e-9)
    rsi = 100 - (100 / (1 + rs))
    latest = sub["close"].iloc[-1]
    t = time.strftime('%H:%M', time.localtime(min_ts/1000))

    if ema5 > sma20 and latest > vwap and rsi > 60:
        print(f"{t} BUY")
        subject = f"BUY SIGNAL at {t}"
        body = (
            f"BUY signal generated at {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        emailer.sendEmail(subject, body)
    elif ema5 < sma20 and latest < vwap and rsi < 40:
        print(f"{t} SELL")
        subject = f"SELL SIGNAL at {t}"
        body = (
            f"SELL signal generated at {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        emailer.sendEmail(subject, body)
    else:
        print(f"{t} NO SIGNAL")

# Run
feed.subscribe([(feed.IDX, SEC_ID)])
feed.on_full(on_tick)
print("Starting…")
feed.connect(threaded=True)

while True:
    time.sleep(1)