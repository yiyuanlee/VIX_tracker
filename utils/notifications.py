"""
Notifications Module
Unified notification handlers for Telegram, Discord, Email
"""

import os
import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_telegram(message):
    """Send message via Telegram Bot"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Telegram not configured, skipping...")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        with urllib.request.urlopen(req) as response:
            response.read().decode()
            print("Telegram sent OK")
            return True
    except Exception as e:
        print(f"Telegram failed: {e}")
        return False


def send_discord(message, webhook_url=None):
    """Send message via Discord Webhook"""
    url = webhook_url or os.environ.get('DISCORD_WEBHOOK_URL')

    if not url:
        print("Discord webhook not configured, skipping...")
        return False

    data = {'content': message}

    try:
        req = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            response.read().decode()
            print("Discord sent OK")
            return True
    except Exception as e:
        print(f"Discord failed: {e}")
        return False


def send_email(subject, body, to_addr=None):
    """Send email via SMTP"""
    user = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    receiver = to_addr or os.environ.get('RECEIVER_MAIL')

    if not user or not password or not receiver:
        print("Email not configured, skipping...")
        return False

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print("Email sent OK")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False