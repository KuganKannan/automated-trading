import time
import pandas as pd
from dhanhq import marketfeed
from dotenv import load_dotenv
import os
from send_email import SendEmail

load_dotenv()

# Load credentials from .env
client_id = os.environ.get("DHAN_CLIENT_ID")
access_token = os.environ.get("DHAN_ACCESS_TOKEN")

# Structure for subscribing is (exchange_segment, "security_id", subscription_type)
instruments = [   # Quote - Quote Data
    (marketfeed.NSE, "13", marketfeed.Full),     # Full - Full Packet
  
]

version = "v2"  # Mention Version and set to latest version 'v2'

emailer = SendEmail()

# Data containers for 1-min and 5-min candles
ticks = []
df_1min = pd.DataFrame(columns=["open", "high", "low", "close", "volume"], dtype=float)
df_5min = pd.DataFrame(columns=["open", "high", "low", "close", "volume"], dtype=float)
current_min = None

def on_tick(tick):
    global current_min, ticks, df_1min
    # Use current timestamp since LTT is just time string
    import time
    ts_min = int(time.time() * 1000) // 60000 * 60000

    if current_min is None:
        current_min = ts_min
    if ts_min != current_min:
        finalize_minute(current_min)
        ticks = []
        current_min = ts_min

    ticks.append((float(tick['LTP']), tick['volume']))

def finalize_minute(min_ts):
    global df_1min, df_5min
    if not ticks:
        return
    P, V = zip(*ticks)
    candle = {
        "open": P[0], "high": max(P), "low": min(P),
        "close": P[-1], "volume": sum(V)
    }
    df_1min.loc[min_ts] = candle

    # Keep only last 100 1-min candles
    if len(df_1min) > 100:
        df_1min = df_1min.iloc[-100:]

    # Resample to 5-min candles
    df_1min.index = pd.to_datetime(df_1min.index)
    df_5min_resampled = df_1min.resample('5T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    df_5min = df_5min_resampled

    # Only check signal if we have at least 5 five-minute candles
    if len(df_5min) >= 5:
        check_signal(df_5min)

def check_signal(df_5min):
    sub = df_5min.iloc[-5:]
    ema5 = sub["close"].ewm(span=5).mean().iloc[-1]
    sma20 = df_5min["close"].rolling(20).mean().iloc[-1] if len(df_5min) >= 20 else df_5min["close"].mean()
    vwap = (df_5min["close"] * df_5min["volume"]).sum() / df_5min["volume"].sum()
    delta = df_5min["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14).mean().iloc[-1]
    loss = (-delta).clip(lower=0).ewm(alpha=1/14).mean().iloc[-1]
    rs = gain / (loss if loss > 0 else 1e-9)
    rsi = 100 - (100 / (1 + rs))
    latest = sub["close"].iloc[-1]
    t = sub.index[-1].strftime('%H:%M')

    if ema5 > sma20 and latest > vwap and rsi > 60:
        print(f"Line 90: {t} BUY")
        subject = f"BUY SIGNAL at {t}"
        body = (
            f"BUY signal generated at {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        print(f"Line 100: Attempting to send email - {subject}")
        emailer.sendEmail(subject, body)
    elif ema5 < sma20 and latest < vwap and rsi < 40:
        print(f"Line 102: {t} SELL")
        subject = f"SELL SIGNAL at {t}"
        body = (
            f"SELL signal generated at {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        print(f"Line 112: Attempting to send email - {subject}")
        emailer.sendEmail(subject, body)
    else:
        print(f"Line 114: {t} NO SIGNAL")

# --- Dhan marketfeed connection and event loop ---

try:
    data = marketfeed.DhanFeed(client_id, access_token, instruments, version)
    while True:
        data.run_forever()
        response = data.get_data()
        print(response)
        # Adapted: call on_tick for each tick in response
        if isinstance(response, list):
            print("Hello2")
            for tick in response:
                print("Hello3")
                on_tick(tick)
                print("Hello4")
        elif isinstance(response, dict):
            print("Hello5")
            on_tick(response)
            print("Hello6")
        # (If your API returns a different structure, adjust as needed)
except Exception as e:
    print(f"Line 131: {e}")

# Close Connection
