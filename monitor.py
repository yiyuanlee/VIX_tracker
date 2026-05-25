"""
VIX Monitor - Enhanced Edition
Term Structure + RSI + Jump Detection + Multi-Condition Alerts
"""

import yfinance as yf
import smtplib
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
import urllib.request
import urllib.parse

# ============== Config ==============
VIX_THRESHOLD = float(os.environ.get('VIX_THRESHOLD', '25'))
RSI_THRESHOLD = float(os.environ.get('RSI_THRESHOLD', '60'))
JUMP_THRESHOLD = float(os.environ.get('JUMP_THRESHOLD', '15'))

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
MAIL_USER = os.environ.get('MAIL_USER')
MAIL_PASS = os.environ.get('MAIL_PASS')
RECEIVER_MAIL = os.environ.get('RECEIVER_MAIL')


# ============== VIX Data Fetch ==============
def get_vix_data(period='3mo'):
    tickers = {
        '^VIX': 'VIX',
        '^VIX9D': 'VIX 9D',
        '^VIX3M': 'VIX 3M',
        '^VIX6M': 'VIX 6M',
    }
    data = {}
    for symbol, name in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if len(hist) > 0:
                closes = hist['Close']
                current = closes.iloc[-1]
                prev_close = closes.iloc[-2] if len(closes) > 1 else current
                change = ((current - prev_close) / prev_close) * 100
                deltas = closes.diff()
                gains = deltas.clip(lower=0).rolling(14).mean()
                losses = (-deltas.clip(upper=0)).rolling(14).mean()
                rs = gains / losses.replace(0, np.nan)
                rsi = (100 - (100 / (rs + 1))).iloc[-1]
                if np.isnan(rsi):
                    rsi = 50.0
                data[symbol] = {
                    'name': name,
                    'current': current,
                    'prev_close': prev_close,
                    'change': change,
                    'rsi': round(float(rsi), 1),
                    'hist': hist
                }
        except Exception as e:
            print(f"Failed to fetch {symbol}: {e}")
    return data


# ============== Term Structure Analysis ==============
def analyze_term_structure(vix_data):
    vix9d = vix_data.get('^VIX9D', {}).get('current', 0)
    vix6m = vix_data.get('^VIX6M', {}).get('current', 0)
    spread = round(vix9d - vix6m, 2)
    if spread > 2:
        direction = 'STEEPER'
        signal = 'Term structure STEEPER - short-term panic rising'
    elif spread < -2:
        direction = 'FLATTER'
        signal = 'Term structure FLATTER - long-term concern dominant'
    else:
        direction = 'NORMAL'
        signal = 'Term structure NORMAL'
    return {'vix9d': vix9d, 'vix6m': vix6m, 'spread': spread, 'direction': direction, 'signal': signal}


# ============== Jump Detection ==============
def detect_vix_jump(vix_data, threshold=JUMP_THRESHOLD):
    vix = vix_data.get('^VIX', {})
    change = vix.get('change', 0)
    current = vix.get('current', 0)
    if abs(change) > threshold:
        return {'jumped': True, 'direction': 'UP' if change > 0 else 'DOWN', 'change': round(change, 1), 'current': current}
    return {'jumped': False}


# ============== Alert Generation ==============
def generate_alerts(vix_data, term_structure, jump_detected):
    vix = vix_data.get('^VIX', {})
    current = vix.get('current', 0)
    rsi = vix.get('rsi', 50)
    alerts = []
    if current > VIX_THRESHOLD:
        alerts.append(f'VIX above threshold ({current:.1f} > {VIX_THRESHOLD})')
    if rsi > RSI_THRESHOLD:
        alerts.append(f'VIX RSI overbought ({rsi} > {RSI_THRESHOLD})')
    if term_structure['direction'] == 'STEEPER' and current > VIX_THRESHOLD:
        alerts.append(f'Term structure steepening (spread {term_structure["spread"]:+.2f})')
    if jump_detected['jumped']:
        alerts.append(f'VIX jumped {jump_detected["change"]:+.1f}% in one day')
    if len(vix.get('hist', [])) >= 4:
        hist = vix['hist']['Close']
        three_day = ((hist.iloc[-1] / hist.iloc[-4]) - 1) * 100
        if three_day > 30:
            alerts.append(f'VIX up {three_day:.1f}% in 3 days')
    return alerts


# ============== Chart ==============
def generate_vix_chart(vix_data, term_structure, output_path='vix_chart.png'):
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 2, 1]})
    fig.suptitle('VIX Market Volatility Monitor (Enhanced)', fontsize=16, fontweight='bold')
    colors = {'^VIX': '#FF6B6B', '^VIX9D': '#4ECDC4', '^VIX3M': '#45B7D1', '^VIX6M': '#96CEB4'}

    ax1 = axes[0]
    symbols = list(vix_data.keys())
    values = [vix_data[s]['current'] for s in symbols]
    names = [vix_data[s]['name'] for s in symbols]
    ax1.bar(names, values, color=[colors.get(s, '#888888') for s in symbols])
    ax1.axhline(VIX_THRESHOLD, color='red', linestyle='--', linewidth=2)
    ax1.set_ylabel('VIX Value')
    ax1.set_title('Current VIX Levels')
    for i, (bar, val) in enumerate(zip(ax1.patches, values)):
        ax1.text(i, val + 0.3, f'{val:.1f}', ha='center', fontsize=10)

    ax2 = axes[1]
    for symbol in symbols:
        hist = vix_data[symbol]['hist']
        if len(hist) > 0:
            ax2.plot(hist.index, hist['Close'], label=vix_data[symbol]['name'], color=colors.get(symbol, '#888888'), linewidth=2)
    ax2.axhline(VIX_THRESHOLD, color='red', linestyle='--', linewidth=2)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.set_ylabel('VIX Value')
    ax2.set_title('VIX Historical Trend (3 Months)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[2]
    labels = ['Short\n(VIX9D)', 'Mid\n(VIX3M)', 'Long\n(VIX6M)']
    svals = [term_structure['vix9d'], vix_data.get('^VIX3M', {}).get('current', 0), term_structure['vix6m']]
    bar_c = '#FF6B6B' if term_structure['spread'] > 2 else '#96CEB4'
    ax3.bar(labels, svals, color=[bar_c]*3, alpha=0.7)
    ax3.set_title(f'Term Structure: {term_structure["signal"]} (Spread: {term_structure["spread"]:+.2f})')
    for i, v in enumerate(svals):
        ax3.text(i, v + 0.1, f'{v:.1f}', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart saved: {output_path}")


# ============== Notifications ==============
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping...")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        with urllib.request.urlopen(req):
            print("Telegram sent OK")
            return True
    except Exception as e:
        print(f"Telegram failed: {e}")
        return False


# ============== Main ==============
def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] VIX Enhanced Monitor running...")
    vix_data = get_vix_data()
    term_structure = analyze_term_structure(vix_data)
    jump_detected = detect_vix_jump(vix_data)
    alerts = generate_alerts(vix_data, term_structure, jump_detected)
    generate_vix_chart(vix_data, term_structure)

    print(f"\nVIX data:")
    for s, d in vix_data.items():
        print(f"  {d['name']}: {d['current']:.2f} ({d['change']:+.1f}%) | RSI: {d['rsi']}")
    print(f"\nTerm structure: {term_structure['signal']} (diff: {term_structure['spread']:+.2f})")
    if jump_detected['jumped']:
        print(f"Jump detected: {jump_detected['change']:+.1f}%")
    print(f"\nAlerts ({len(alerts)}):")
    for a in alerts:
        print(f"  - {a}")

    if alerts:
        msg = f"VIX Alert [{datetime.now().strftime('%Y-%m-%d %H:%M')}]\n\n"
        for a in alerts:
            msg += f"- {a}\n"
        msg += f"\nTerm: {term_structure['signal']}"
        send_telegram(msg)
    else:
        print("\nNo alerts triggered.")


if __name__ == "__main__":
    main()