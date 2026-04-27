import yfinance as yf
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json
import numpy as np

# ============== 配置 ==============
# Telegram 配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 持仓配置
POSITIONS = [
    {'symbol': 'GOOGL', 'shares': 7, 'alert_below': 320, 'alert_above': 350},
    {'symbol': 'AMD', 'shares': 2, 'alert_below': 230, 'alert_above': 270},
]

# MACD 追踪标的（哪些股票需要追踪 MACD 金叉）
MACD_TRACKED = [
    {'symbol': 'GOOGL', 'shares': 7},
    {'symbol': 'NVDA', 'shares': 7},
    {'symbol': 'MSFT', 'shares': 4},
]

# MACD 参数
MACD_FAST = 12   # 快速 EMA 周期
MACD_SLOW = 26   # 慢速 EMA 周期
MACD_SIGNAL = 9  # 信号线 EMA 周期


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


# ============== 工具函数 ==============
def calculate_ema(prices, period):
    """计算指数移动平均线 (EMA)"""
    ema = []
    alpha = 2 / (period + 1)
    
    for i, price in enumerate(prices):
        if i == 0:
            ema.append(price)
        else:
            ema.append(alpha * price + (1 - alpha) * ema[-1])
    
    return np.array(ema)


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    计算 MACD 指标
    
    返回:
        macd_line: DIF 线 (快速EMA - 慢速EMA)
        signal_line: DEA 信号线 (MACD 的 9 日 EMA)
        histogram: 柱状图 (MACD线 - 信号线)
        prev_macd_line: 上一日的 DIF 线（用于检测交叉）
        prev_signal_line: 上一日的信号线（用于检测交叉）
    """
    prices = np.array(prices)
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    prev_macd_line = macd_line[-2] if len(macd_line) > 1 else macd_line[-1]
    prev_signal_line = signal_line[-2] if len(signal_line) > 1 else signal_line[-1]
    
    return {
        'macd_line': macd_line[-1],
        'signal_line': signal_line[-1],
        'histogram': histogram[-1],
        'prev_macd_line': prev_macd_line,
        'prev_signal_line': prev_signal_line,
        'all_macd': macd_line,
        'all_signal': signal_line,
        'all_histogram': histogram,
    }


def detect_macd_cross(macd_data):
    """
    检测 MACD 交叉信号
    
    返回:
        'golden_cross': EMA12 上穿 EMA26（DIF 从下方穿越信号线，看涨）
        'death_cross':  EMA12 下穿 EMA26（DIF 从上方穿越信号线，看跌）
        None: 无交叉
    """
    macd = macd_data['macd_line']
    signal = macd_data['signal_line']
    prev_macd = macd_data['prev_macd_line']
    prev_signal = macd_data['prev_signal_line']
    
    # 金叉：前一天 DIF <= 信号线，今天 DIF > 信号线
    if prev_macd <= prev_signal and macd > signal:
        return 'golden_cross'
    # 死叉：前一天 DIF >= 信号线，今天 DIF < 信号线
    elif prev_macd >= prev_signal and macd < signal:
        return 'death_cross'
    
    return None


# ============== 获取股票数据 ==============
def get_stock_data(symbol, period='1mo'):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if len(hist) == 0:
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change_percent = ((current_price - prev_close) / prev_close) * 100
        
        info = ticker.info
        company_name = info.get('shortName', symbol)
        
        return {
            'symbol': symbol,
            'name': company_name,
            'current_price': current_price,
            'prev_close': prev_close,
            'change_percent': change_percent,
            'hist': hist,
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
    
    ax1 = axes[0]
    bars = ax1.bar(symbols, prices, color=colors, edgecolor='white', linewidth=1.5)
    ax1.set_ylabel('Stock Price ($)', fontsize=12)
    ax1.set_title('Current Stock Prices', fontsize=14)
    
    for bar, price, change in zip(bars, prices, changes):
        emoji = "📉" if change < 0 else "📈"
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{emoji} ${price:.2f}\n({change:+.2f}%)', 
                ha='center', va='bottom', fontsize=10)
    
    ax2 = axes[1]
    for p in positions_data:
        df = p['hist']
        ax2.plot(df.index, df['Close'], label=f"{p['symbol']} (${p['current_price']:.2f})", 
                linewidth=2, marker='o', markersize=3)
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Stock Price ($)', fontsize=12)
    ax2.set_title('Price Trend', fontsize=14)
    ax2.legend(loc='upper left')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def generate_macd_chart(positions_data, macd_results, output_path='macd_chart.png'):
    """生成 MACD 图表"""
    fig, axes = plt.subplots(len(positions_data), 2, figsize=(14, 4 * len(positions_data)))
    if len(positions_data) == 1:
        axes = axes.reshape(1, -1)
    
    for idx, p in enumerate(positions_data):
        symbol = p['symbol']
        if symbol not in macd_results:
            continue
        
        macd_data = macd_results[symbol]
        df = p['hist']
        prices = df['Close'].values
        
        # 左图：价格 + EMA
        ax_price = axes[idx, 0]
        ax_price.plot(df.index, prices, label=f'{symbol} price', color='#333333', linewidth=2)
        
        ema12 = calculate_ema(prices, MACD_FAST)
        ema26 = calculate_ema(prices, MACD_SLOW)
        ax_price.plot(df.index[-len(ema12):], ema12, label=f'EMA12', color='#2196F3', linewidth=1.5, alpha=0.8)
        ax_price.plot(df.index[-len(ema26):], ema26, label=f'EMA26', color='#FF9800', linewidth=1.5, alpha=0.8)
        ax_price.set_title(f'{symbol} - Price & EMA', fontsize=12, fontweight='bold')
        ax_price.legend(loc='upper left', fontsize=9)
        ax_price.grid(True, alpha=0.3)
        ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # 右图：MACD
        ax_macd = axes[idx, 1]
        all_macd = macd_data['all_macd']
        all_signal = macd_data['all_signal']
        all_hist = macd_data['all_histogram']
        
        start_idx = max(0, len(prices) - len(all_macd))
        x = df.index[start_idx:]
        
        ax_macd.plot(x, all_macd, label='MACD (DIF)', color='#2196F3', linewidth=2)
        ax_macd.plot(x, all_signal, label='Signal (DEA)', color='#FF9800', linewidth=2)
        
        colors = ['#4CAF50' if v >= 0 else '#F44336' for v in all_hist]
        ax_macd.bar(x, all_hist, label='Histogram', color=colors, alpha=0.6, width=0.8)
        ax_macd.axhline(y=0, color='#888888', linewidth=1)
        ax_macd.set_title(f'{symbol} - MACD', fontsize=12, fontweight='bold')
        ax_macd.legend(loc='upper left', fontsize=9)
        ax_macd.grid(True, alpha=0.3)
        ax_macd.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    
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


def format_macd_cross_alert(symbol, company_name, cross_type, shares, macd_data):
    """格式化 MACD 交叉提醒"""
    is_golden = cross_type == 'golden_cross'
    emoji = "🟢" if is_golden else "🔴"
    cross_name = "金叉 📈" if is_golden else "死叉 📉"
    
    macd_val = macd_data['macd_line']
    signal_val = macd_data['signal_line']
    hist_val = macd_data['histogram']
    
    direction_desc = "EMA12 上穿 EMA26，看涨信号！" if is_golden else "EMA12 下穿 EMA26，看跌信号！"
    
    message = f"""
{emoji} <b>MACD {cross_name}</b>

{company_name} ({symbol})

{cross_type == 'golden_cross' and '🔥 出现 MACD 金叉 — 关注买入机会'}
{cross_type == 'death_cross' and '⚠️ 出现 MACD 死叉 — 注意风险'}

MACD(DIF):  {macd_val:+.4f}
Signal(DEA): {signal_val:+.4f}
Histogram:  {hist_val:+.4f}

{direction_desc}

持仓: {shares}股
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
def check_price_alerts():
    """检查是否触发价格提醒"""
    alerts_triggered = []
    
    for position in POSITIONS:
        data = get_stock_data(position['symbol'])
        if data is None:
            continue
        
        data['shares'] = position['shares']
        
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


def check_macd_crosses():
    """检查 MACD 交叉信号"""
    crosses = []
    
    for item in MACD_TRACKED:
        symbol = item['symbol']
        data = get_stock_data(symbol, period='3mo')
        
        if data is None or len(data['hist']) < MACD_SLOW + MACD_SIGNAL:
            print(f"⚠️ {symbol} 数据不足，跳过 MACD 计算")
            continue
        
        prices = data['hist']['Close'].values
        macd_data = calculate_macd(prices, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
        cross = detect_macd_cross(macd_data)
        
        if cross:
            crosses.append({
                'symbol': symbol,
                'name': data['name'],
                'cross_type': cross,
                'shares': item['shares'],
                'macd_data': macd_data,
                'current_price': data['current_price'],
            })
    
    return crosses


def send_daily_summary():
    """发送每日持仓总结 + MACD 交叉检查"""
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
    
    chart_path = 'portfolio_chart.png'
    try:
        generate_portfolio_chart(positions_data, chart_path)
        print(f"✅ 图表已生成: {chart_path}")
    except Exception as e:
        print(f"⚠️ 图表生成失败: {e}")
        chart_path = None
    
    message = format_daily_summary(positions_data, total_value, total_change, total_change_percent)
    send_telegram(message)
    
    # 检查 MACD 交叉
    macd_crosses = check_macd_crosses()
    if macd_crosses:
        print(f"\n🔔 检测到 {len(macd_crosses)} 个 MACD 交叉信号:")
        for cross in macd_crosses:
            print(f"  {cross['symbol']} - {cross['cross_type']}")
            msg = format_macd_cross_alert(
                cross['symbol'],
                cross['name'],
                cross['cross_type'],
                cross['shares'],
                cross['macd_data'],
            )
            send_telegram(msg)
    
    print(f"\n📊 每日总结已发送")
    print(f"总市值: ${total_value:,.2f} ({total_change_percent:+.2f}%)")


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Portfolio Monitor 启动...")
    
    mode = os.environ.get('PORTFOLIO_MODE', 'daily')
    
    if mode == 'alert':
        alerts = check_price_alerts()
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
    
    elif mode == 'macd':
        crosses = check_macd_crosses()
        if crosses:
            for cross in crosses:
                msg = format_macd_cross_alert(
                    cross['symbol'],
                    cross['name'],
                    cross['cross_type'],
                    cross['shares'],
                    cross['macd_data'],
                )
                send_telegram(msg)
            print(f"✅ 已发送 {len(crosses)} 条 MACD 提醒")
        else:
            print("🟢 今日无 MACD 交叉信号")
    
    else:
        send_daily_summary()
