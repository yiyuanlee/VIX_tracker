"""
Technical Indicators Module
Common indicators used across VIX and Portfolio monitoring
"""

import numpy as np


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average (EMA)"""
    prices = np.array(prices)
    alpha = 2 / (period + 1)
    ema = np.zeros(len(prices))
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
    return ema


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate MACD indicator

    Returns:
        dict with:
            - macd_line: DIF (fast EMA - slow EMA)
            - signal_line: DEA (signal line EMA)
            - histogram: MACD line - signal line
            - prev_macd_line: previous DIF (for cross detection)
            - prev_signal_line: previous signal (for cross detection)
            - all_macd/signal/histogram: full arrays for charting
    """
    prices = np.array(prices)
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return {
        'macd_line': macd_line[-1],
        'signal_line': signal_line[-1],
        'histogram': histogram[-1],
        'prev_macd_line': macd_line[-2] if len(macd_line) > 1 else macd_line[-1],
        'prev_signal_line': signal_line[-2] if len(signal_line) > 1 else signal_line[-1],
        'all_macd': macd_line,
        'all_signal': signal_line,
        'all_histogram': histogram,
    }


def detect_macd_cross(macd_data):
    """
    Detect MACD cross signals

    Returns:
        'golden_cross': EMA12 crosses above EMA26 (bullish)
        'death_cross': EMA12 crosses below EMA26 (bearish)
        None: no cross detected
    """
    macd = macd_data['macd_line']
    signal = macd_data['signal_line']
    prev_macd = macd_data['prev_macd_line']
    prev_signal = macd_data['prev_signal_line']

    if prev_macd <= prev_signal and macd > signal:
        return 'golden_cross'
    elif prev_macd >= prev_signal and macd < signal:
        return 'death_cross'
    return None


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)"""
    prices = np.array(prices)
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (rs + 1))
    return float(rsi)