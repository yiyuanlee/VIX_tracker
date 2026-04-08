import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

def send_email(vix_value):
    # 从 GitHub Secrets 中读取敏感信息
    sender = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    receiver = os.environ.get('RECEIVER_MAIL')
    
    smtp_server = "smtp.gmail.com" # 如果用Gmail

    content = f"当前 VIX 指数已突破阈值：{vix_value:.2f}。请关注市场风险。"
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = Header("⚠️ VIX 市场恐慌预警", 'utf-8')

    try:
        # 使用 SSL 加密连接
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [receiver], message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"发送失败: {e}")

def check_vix():
    vix = yf.Ticker("^VIX")
    # 获取最新价格
    current_vix = vix.history(period="1d")['Close'].iloc[-1]
    
    # 设定一个提醒阈值，例如 25
    if current_vix > 25:
        send_email(current_vix)

if __name__ == "__main__":
    check_vix()