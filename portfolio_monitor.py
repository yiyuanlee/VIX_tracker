import yfinance as yf
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json

# ============== 配置 ==============
# Telegram 配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 持仓配置
POSITIONS = [
    {'symbol': 'GOOGL', 'shares': 7, 'alert_below': 320, 'alert_above': 180},
    {'symbol': 'AMD', 'shares': 2, 'alert_below': 240, 'alert_above': 150},
]

# ============== Telegram 通知 ==============
def send_telegram(message):
    """发送 Telegram 消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 配置不完整，跳过...")
        return False
    
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
            print(f"Telegram 发送成功")
            return True
    except Exception as e:
        print(f"Telegram 发送失败: {e}")
        return False

# ============== 获取股票数据 ==============
def get_stock_data(symbol):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        
        if len(hist) == 0:
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change_percent = ((current_price - prev_close) / prev_close) * 100
        
        # 获取更多信息
        info = ticker.info
        company_name = info.get('shortName', symbol)
        
        return {
            'symbol': symbol,
            'name': company_name,
            'current_price': current_price,
            'prev_close': prev_close,
            'change_percent': change_percent,
            'hist': hist,
            'shares': None  # 稍后填充
        }
    except Exception as e:
        print(f"获取 {symbol} 数据失败: {e}")
        return None

# ============== 生成持仓图表 ==============
def generate_portfolio_chart(positions_data, output_path='portfolio_chart.png'):
    """生成持仓可视化图表"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('📊 Portfolio Monitor', fontsize=16, fontweight='bold')
    
    symbols = [p['symbol'] for p in positions_data]
    prices = [p['current_price'] for p in positions_data]
    changes = [p['change_percent'] for p in positions_data]
    
    colors = ['#FF6B6B' if c < 0 else '#4ECDC4' for c in changes]
    
    # 上图：当前价格
    ax1 = axes[0]
    bars = ax1.bar(symbols, prices, color=colors, edgecolor='white', linewidth=1.5)
    ax1.set_ylabel('Stock Price ($)', fontsize=12)
    ax1.set_title('Current Stock Prices', fontsize=14)
    
    for bar, price, change in zip(bars, prices, changes):
        emoji = "📉" if change < 0 else "📈"
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{emoji} ${price:.2f}\n({change:+.2f}%)', 
                ha='center', va='bottom', fontsize=10)
    
    # 下图：5日走势图
    ax2 = axes[1]
    for p in positions_data:
        df = p['hist']
        ax2.plot(df.index, df['Close'], label=f"{p['symbol']} (${p['current_price']:.2f})", 
                linewidth=2, marker='o', markersize=3)
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Stock Price ($)', fontsize=12)
    ax2.set_title('5-Day Price Trend', fontsize=14)
    ax2.legend(loc='upper left')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path

# ============== 格式化消息 ==============
def format_price_alert(position, current_price):
    """格式化价格提醒消息"""
    direction = "跌破" if current_price < position['alert_below'] else "突破"
    emoji = "🔴" if current_price < position['alert_below'] else "🟢"
    
    message = f"""
{emoji} <b>价格提醒</b>

{position['name']} ({position['symbol']})
当前价格: <b>${current_price:.2f}</b>
{direction}阈值: ${position.get('alert_below' if current_price < position['alert_below'] else 'alert_above'):.2f}

持仓: {position['shares']}股
市值: ${current_price * position['shares']:.2f}
"""
    return message.strip()

def format_daily_summary(positions_data, total_value, total_change, total_change_percent):
    """格式化每日收盘总结"""
    lines = [
        "📊 <b>每日持仓总结</b>",
        f"📅 {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "<b>持仓明细</b>",
        "━━━━━━━━━━━━━━━",
    ]
    
    for p in positions_data:
        emoji = "📉" if p['change_percent'] < 0 else "📈"
        lines.append(
            f"{emoji} <b>{p['symbol']}</b> ({p['name']})"
        )
        lines.append(
            f"   当前价: ${p['current_price']:.2f} ({p['change_percent']:+.2f}%)"
        )
        lines.append(
            f"   持仓: {p['shares']}股 | 市值: ${p['current_price'] * p['shares']:.2f}"
        )
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━")
    overall_emoji = "📈" if total_change_percent >= 0 else "📉"
    lines.append(f"{overall_emoji} <b>总市值</b>: ${total_value:,.2f}")
    lines.append(f"   今日变化: ${total_change:,.2f} ({total_change_percent:+.2f}%)")
    
    lines.append("")
    lines.append("⚙️ 由 Portfolio Monitor 自动发送")
    
    return "\n".join(lines)

# ============== 主逻辑 ==============
def check_alerts():
    """检查是否触发价格提醒"""
    alerts_triggered = []
    
    for position in POSITIONS:
        data = get_stock_data(position['symbol'])
        if data is None:
            continue
        
        data['shares'] = position['shares']
        
        # 检查是否触发提醒
        if position['alert_below'] and data['current_price'] < position['alert_below']:
            alerts_triggered.append({
                'type': 'below',
                'position': position,
                'current_price': data['current_price']
            })
        
        if position['alert_above'] and data['current_price'] > position['alert_above']:
            alerts_triggered.append({
                'type': 'above',
                'position': position,
                'current_price': data['current_price']
            })
    
    return alerts_triggered

def send_daily_summary():
    """发送每日持仓总结"""
    positions_data = []
    total_value = 0
    total_prev_value = 0
    
    for position in POSITIONS:
        data = get_stock_data(position['symbol'])
        if data is None:
            continue
        
        data['shares'] = position['shares']
        positions_data.append(data)
        
        total_value += data['current_price'] * position['shares']
        total_prev_value += data['prev_close'] * position['shares']
    
    if not positions_data:
        print("获取持仓数据失败")
        return
    
    total_change = total_value - total_prev_value
    total_change_percent = ((total_value - total_prev_value) / total_prev_value) * 100
    
    # 生成图表
    chart_path = 'portfolio_chart.png'
    try:
        generate_portfolio_chart(positions_data, chart_path)
        print(f"✅ 图表已生成: {chart_path}")
    except Exception as e:
        print(f"⚠️ 图表生成失败: {e}")
        chart_path = None
    
    # 发送消息
    message = format_daily_summary(positions_data, total_value, total_change, total_change_percent)
    send_telegram(message)
    
    print(f"\n📊 每日总结已发送")
    print(f"总市值: ${total_value:,.2f} ({total_change_percent:+.2f}%)")

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Portfolio Monitor 启动...")
    
    # 模式选择：通过环境变量控制
    mode = os.environ.get('PORTFOLIO_MODE', 'daily')
    
    if mode == 'alert':
        # 价格提醒模式
        alerts = check_alerts()
        if alerts:
            for alert in alerts:
                message = format_price_alert(
                    alert['position'], 
                    alert['current_price']
                )
                send_telegram(message)
            print(f"✅ 已发送 {len(alerts)} 条价格提醒")
        else:
            print("🟢 未触发价格提醒")
    else:
        # 每日总结模式
        send_daily_summary()
