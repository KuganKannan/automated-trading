import time
import pandas as pd
from dhanhq import marketfeed
from dotenv import load_dotenv
import os
from send_email import SendEmail
from logging_config import setup_logging, get_logger

load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

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
    df_5min_resampled = df_1min.resample('5min').agg({
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
        print(f"🚀 {t} BUY SIGNAL - Price: {latest}, RSI: {rsi:.2f}", flush=True)
        logger.info(f"{t} BUY")
        subject = f"BUY SIGNAL at {t}"
        body = (
            f"BUY signal generated at {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        logger.info(f"Attempting to send email - {subject}")
        emailer.sendEmail(subject, body)
    elif ema5 < sma20 and latest < vwap and rsi < 40:
        print(f"📉 {t} SELL SIGNAL - Price: {latest}, RSI: {rsi:.2f}", flush=True)
        logger.info(f"{t} SELL")
        subject = f"SELL SIGNAL at {t}"
        body = (
            f"SELL signal generated at {t}\n"
            f"Time: {t}\n"
            f"Price: {latest}\n"
            f"RSI: {rsi:.2f}\n"
            f"VWAP: {vwap:.2f}\n"
            f"EMA5: {ema5:.2f}\n"
            f"SMA20: {sma20:.2f}"
        )
        logger.info(f"Attempting to send email - {subject}")
        emailer.sendEmail(subject, body)
    else:
        print(f"⚪ {t} NO SIGNAL - Price: {latest}, RSI: {rsi:.2f}", flush=True)
        logger.debug(f"{t} NO SIGNAL")

# --- Dhan marketfeed connection and event loop ---



def connect_and_run():
    try:

        logger.info("Establishing connection to Dhan market feed...")
        data = marketfeed.DhanFeed(client_id, access_token, instruments, version)
        
        while True:
            try:
                logger.debug("Before run forever ")
                data.run_forever()
                logger.debug("After run forever ")
                response = data.get_data()
                logger.debug("Received response from marketfeed")
                
                if response is None:
                    logger.warning("No data received, retrying...")
                    time.sleep(1)
                    continue
                    
                print(f"📈 Received response: {response}", flush=True)
                logger.debug(f"Received response: {response}")
                
                # Adapted: call on_tick for each tick in response
                if isinstance(response, list):
                    print("📊 Processing list response", flush=True)
                    logger.debug("Processing list response")
                    for tick in response:
                        print(f"📊 Processing tick: {tick}", flush=True)
                        logger.debug("Processing tick")
                        on_tick(tick)
                        logger.debug("Tick processed")
                elif isinstance(response, dict):
                    print("📊 Processing dict response", flush=True)
                    logger.debug("Processing dict response")
                    on_tick(response)
                    logger.debug("Dict response processed")
                    
            except Exception as inner_e:
                logger.error(f"Connection error: {inner_e}")
                logger.info("Connection lost, will reconnect...")
                break
                
    except Exception as e:
        logger.error(f"Error establishing connection: {e}")
        return False
    
    return True

# Main loop with reconnection
while True:
    try:
        if connect_and_run():
            logger.info("Connection ended normally")
        else:
            logger.error("Failed to establish connection")
            
   
            
        logger.info("Reconnecting in 30 seconds...")
        time.sleep(30)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        break
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.info("Retrying in 60 seconds...")
        time.sleep(60)

# Close Connection
