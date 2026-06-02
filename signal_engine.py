import yfinance as yf
import pandas as pd
import numpy as np

from datetime import datetime


# -------------------------
# MARKET STATUS
# -------------------------

def market_open():

    day = datetime.utcnow().weekday()

    if day in [5, 6]:
        return False

    return True


# -------------------------
# DATA DOWNLOAD
# -------------------------

def get_data(pair, timeframe):

    interval = "1m"

    if str(timeframe) == "5":
        interval = "5m"

    df = yf.download(
        tickers=pair,
        period="2d",
        interval=interval,
        progress=False
    )

    if df is None:
        return None

    if len(df) < 60:
        return None

    return df


# -------------------------
# EMA
# -------------------------

def add_ema(df):

    close = df["Close"]

    df["EMA20"] = close.ewm(span=20).mean()
    df["EMA50"] = close.ewm(span=50).mean()

    return df


# -------------------------
# RSI
# -------------------------

def add_rsi(df):

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    return df


# -------------------------
# TREND
# -------------------------

def detect_trend(df):

    ema20 = df["EMA20"].iloc[-1]
    ema50 = df["EMA50"].iloc[-1]

    if ema20 > ema50:
        return "Bullish"

    if ema20 < ema50:
        return "Bearish"

    return "Neutral"


# -------------------------
# SUPPORT
# -------------------------

def support_level(df):

    return float(
        df["Low"].tail(20).min()
    )


# -------------------------
# RESISTANCE
# -------------------------

def resistance_level(df):

    return float(
        df["High"].tail(20).max()
    )


# -------------------------
# BREAKOUT
# -------------------------

def breakout_signal(df):

    last_close = float(
        df["Close"].iloc[-1]
    )

    resistance = resistance_level(df)

    support = support_level(df)

    if last_close > resistance:
        return "UP"

    if last_close < support:
        return "DOWN"

    return "NONE"
    # -------------------------
# BULLISH ENGULFING
# -------------------------

def bullish_engulfing(df):

    if len(df) < 3:
        return False

    prev_open = float(df["Open"].iloc[-2])
    prev_close = float(df["Close"].iloc[-2])

    curr_open = float(df["Open"].iloc[-1])
    curr_close = float(df["Close"].iloc[-1])

    if (
        prev_close < prev_open and
        curr_close > curr_open and
        curr_open < prev_close and
        curr_close > prev_open
    ):
        return True

    return False


# -------------------------
# BEARISH ENGULFING
# -------------------------

def bearish_engulfing(df):

    if len(df) < 3:
        return False

    prev_open = float(df["Open"].iloc[-2])
    prev_close = float(df["Close"].iloc[-2])

    curr_open = float(df["Open"].iloc[-1])
    curr_close = float(df["Close"].iloc[-1])

    if (
        prev_close > prev_open and
        curr_close < curr_open and
        curr_open > prev_close and
        curr_close < prev_open
    ):
        return True

    return False


# -------------------------
# SCORE ENGINE
# -------------------------

def calculate_score(df):

    score = 50

    trend = detect_trend(df)

    rsi = float(df["RSI"].iloc[-1])

    breakout = breakout_signal(df)

    if trend == "Bullish":
        score += 15

    if trend == "Bearish":
        score -= 15

    if rsi < 30:
        score += 15

    if rsi > 70:
        score -= 15

    if bullish_engulfing(df):
        score += 20

    if bearish_engulfing(df):
        score -= 20

    if breakout == "UP":
        score += 15

    if breakout == "DOWN":
        score -= 15

    score = max(0, min(100, score))

    return int(score)


# -------------------------
# M5 TREND
# -------------------------

def get_m5_trend(pair):

    try:

        df = yf.download(
            tickers=pair,
            interval="5m",
            period="2d",
            progress=False
        )

        if len(df) < 60:
            return "Neutral"

        df = add_ema(df)

        return detect_trend(df)

    except:
        return "Neutral"


# -------------------------
# MAIN ENGINE
# -------------------------

def generate_signal(pair, timeframe):

    if not market_open():

        return {
            "pair": pair.replace("=X", ""),
            "signal": "MARKET CLOSED",
            "score": 0,
            "trend": "Closed",
            "trendM5": "Closed",
            "market": "closed"
        }

    df = get_data(pair, timeframe)

    if df is None:

        return {
            "pair": pair.replace("=X", ""),
            "signal": "AVOID",
            "score": 50,
            "trend": "Neutral",
            "trendM5": "Neutral",
            "market": "open"
        }

    df = add_ema(df)
    df = add_rsi(df)

    trend = detect_trend(df)

    trend_m5 = get_m5_trend(pair)

    score = calculate_score(df)

    signal = "AVOID"

    if score >= 75:
        signal = "CALL"

    elif score <= 25:
        signal = "PUT"

    return {

        "pair": pair.replace("=X", ""),

        "signal": signal,

        "score": score,

        "trend": trend,

        "trendM5": trend_m5,

        "market": "open",

        "time": datetime.utcnow().strftime("%H:%M:%S"),

        "timeframe": f"M{timeframe}"
    }
