import yfinance as yf
import smtplib
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header

# ============== 配置 ==============
# 提醒阈值
VIX_THRESHOLD = float(os.environ.get('VIX_THRESHOLD', '25'))
# Telegram 配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
# Discord 配置
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
# Email 配置
MAIL_USER = os.environ.get('MAIL_USER')
MAIL_PASS = os.environ.get('MAIL_PASS')
RECEIVER_MAIL = os.environ.get('RECEIVER_MAIL')

# ============== VIX 多周期数据获取 ==============
def get_vix_data():
    """获取多种 VIX 指数数据"""
    tickers = {
        '^VIX': 'VIX (恐慌指数)',
        '^VIX9D': 'VIX 9日短期',
        '^VIX3M': 'VIX 3月中期',
        '^VIX6M': 'VIX 6月长期'
    }
    
    data = {}
    for symbol, name in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) > 0:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev_close) / prev_close) * 100
                data[symbol] = {
                    'name': name,
                    'current': current,
                    'prev_close': prev_close,
                    'change': change,
                    'hist': hist
                }
        except Exception as e:
            print(f"获取 {symbol} 失败: {e}")
    
    return data

# ============== 绘图功能 ==============
def generate_vix_chart(vix_data, output_path='vix_chart.png'):
    """生成 VIX 多周期图表"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
    fig.suptitle('VIX Market Volatility Monitor', fontsize=16, fontweight='bold')
    
    colors = {'^VIX': '#FF6B6B', '^VIX9D': '#4ECDC4', '^VIX3M': '#45B7D1', '^VIX6M': '#96CEB4'}
    
    # 上图：VIX 当前值对比
    ax1 = axes[0]
    symbols = list(vix_data.keys())
    values = [vix_data[s]['current'] for s in symbols]
    names = [vix_data[s]['name'] for s in symbols]
    bar_colors = [colors.get(s, '#888888') for s in symbols]
    
    bars = ax1.bar(names, values, color=bar_colors, edgecolor='white', linewidth=1.5)
    ax1.axhline(y=VIX_THRESHOLD, color='red', linestyle='--', linewidth=2, label=f'Threshold ({VIX_THRESHOLD})')
    ax1.set_ylabel('VIX Value', fontsize=12)
    ax1.set_title('Current VIX Levels', fontsize=14)
    ax1.legend()
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{val:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 下图：历史走势
    ax2 = axes[1]
    for symbol in ['^VIX', '^VIX9D', '^VIX3M']:
        if symbol in vix_data:
            df = vix_data[symbol]['hist']
            ax2.plot(df.index, df['Close'], label=vix_data[symbol]['name'], 
                    color=colors.get(symbol, '#888888'), linewidth=2)
    
    ax2.axhline(y=VIX_THRESHOLD, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('VIX Value', fontsize=12)
    ax2.set_title('VIX Historical Trend (5 Days)', fontsize=14)
    ax2.legend(loc='upper right')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path

# ============== 通知渠道 ==============
def send_telegram(message, image_path=None):
    """发送 Telegram 消息/图片"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 配置不完整，跳过...")
        return
    
    import urllib.request
    import urllib.parse
    
    # 发送文字消息
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        with urllib.request.urlopen(req) as response:
            result = response.read().decode()
            print(f"Telegram 消息发送结果: {result}")
        
        # 发送图片
        if image_path and os.path.exists(image_path):
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as f:
                import multipart
                # 简化：直接用表单上传
                from urllib.parse import urlencode
                import http.client
                
            print("Telegram 图片已生成，可手动查看")
            
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def send_discord(message, image_path=None):
    """发送 Discord 消息/图片"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord 配置不完整，跳过...")
        return
    
    import urllib.request
    import json
    
    # 构建 embed
    data = {
        "content": message,
        "embeds": [
            {
                "title": "📈 VIX 市场波动预警",
                "color": 16734296,  # 红色
                "footer": {"text": "VIX Tracker by yiyuanlee"}
            }
        ]
    }
    
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"Discord 消息发送结果: {response.read().decode()}")
    except Exception as e:
        print(f"Discord 发送失败: {e}")

def send_email_with_image(vix_value, image_path=None):
    """发送邮件（可选带图表）"""
    if not MAIL_USER or not MAIL_PASS or not RECEIVER_MAIL:
        print("Email 配置不完整，跳过...")
        return
    
    smtp_server = "smtp.gmail.com"
    
    content = f"""
    <h2>⚠️ VIX 市场恐慌预警</h2>
    <p>当前 VIX 指数已突破阈值：<strong>{vix_value:.2f}</strong></p>
    <p>请关注市场风险，适当调整仓位。</p>
    <hr>
    <p><small>由 VIX Tracker 自动发送 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    """
    
    message = MIMEMultipart('related')
    message['From'] = MAIL_USER
    message['To'] = RECEIVER_MAIL
    message['Subject'] = Header("⚠️ VIX 市场恐慌预警", 'utf-8')
    
    # HTML 内容
    html_part = MIMEText(content, 'html', 'utf-8')
    message.attach(html_part)
    
    # 图表图片
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<vix_chart>')
            img.add_header('Content-Disposition', 'inline')
            message.attach(img)
    
    try:
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, [RECEIVER_MAIL], message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# ============== 主逻辑 ==============
def format_alert_message(vix_data):
    """格式化预警消息"""
    vix = vix_data.get('^VIX', {})
    current = vix.get('current', 0)
    change = vix.get('change', 0)
    
    # 构建多周期数据表格
    lines = ["📊 <b>VIX 多周期数据</b>", ""]
    for symbol in ['^VIX', '^VIX9D', '^VIX3M', '^VIX6M']:
        if symbol in vix_data:
            d = vix_data[symbol]
            emoji = "🔴" if d['current'] > VIX_THRESHOLD else "🟢"
            lines.append(f"{emoji} <b>{d['name']}</b>: {d['current']:.2f} ({d['change']:+.2f}%)")
    
    lines.append("")
    lines.append(f"⚠️ <b>VIX 现已突破 {VIX_THRESHOLD} 阈值！</b>")
    lines.append(f"当前值: <code>{current:.2f}</code> | 变化: {change:+.2f}%")
    lines.append("")
    lines.append("📌 请关注市场风险，合理调整仓位。")
    
    return "\n".join(lines)

def check_vix():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查 VIX...")
    
    # 获取数据
    vix_data = get_vix_data()
    if not vix_data:
        print("获取 VIX 数据失败")
        return
    
    # 打印数据
    print("\n📊 VIX 多周期数据:")
    for symbol, data in vix_data.items():
        print(f"  {data['name']}: {data['current']:.2f} ({data['change']:+.2f}%)")
    
    # 生成图表
    chart_path = 'vix_chart.png'
    try:
        generate_vix_chart(vix_data, chart_path)
        print(f"✅ 图表已生成: {chart_path}")
    except Exception as e:
        print(f"⚠️ 图表生成失败: {e}")
        chart_path = None
    
    # 检查是否触发预警
    current_vix = vix_data.get('^VIX', {}).get('current', 0)
    
    if current_vix > VIX_THRESHOLD:
        print(f"\n⚠️ VIX ({current_vix:.2f}) 突破阈值 ({VIX_THRESHOLD})，发送预警...")
        
        # 格式化消息
        message = format_alert_message(vix_data)
        
        # 多渠道发送
        send_telegram(message, chart_path)
        send_discord(message, chart_path)
        send_email_with_image(current_vix, chart_path)
    else:
        print(f"\n🟢 VIX ({current_vix:.2f}) 未突破阈值 ({VIX_THRESHOLD})，无需预警。")

if __name__ == "__main__":
    check_vix()
