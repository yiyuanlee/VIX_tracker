# 📈 VIX Alert Bot

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Automated-orange.svg)

实时监控市场波动率，通过 **GitHub Actions** 定时抓取 VIX 指数并在突破阈值时发送多渠道提醒。

[English](./README_EN.md) | 中文

---

## ✨ 核心功能

- **多周期 VIX 监控**：同时追踪 VIX、VIX9D（短期）、VIX3M（中期）、VIX6M（长期）
- **自动化运行**：无需服务器，利用 GitHub Actions 每小时自动检查
- **多渠道通知**：支持 Telegram、Discord、Email 三种通知方式
- **可视化图表**：自动生成 VIX 走势图，方便快速了解市场情绪
- **动态阈值**：支持设定固定数值或基于波动百分比触发报警
- **MACD 交叉追踪**：自动检测持仓股的 EMA12/EMA26 交叉信号

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 数据 | [yfinance](https://github.com/ranaroussi/yfinance) |
| 可视化 | matplotlib |
| 自动化 | GitHub Actions |
| 通知 | Telegram Bot / Discord Webhook / SMTP |
| 配置 | YAML |

## 🚀 快速开始

### 1. 配置 GitHub Secrets

在 GitHub 仓库 `Settings → Secrets and variables → Actions` 中添加：

| Secret Name | 说明 | 必需 |
|-------------|------|------|
| `VIX_THRESHOLD` | VIX 预警阈值（默认 25） | 否 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 可选 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可选 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可选 |
| `MAIL_USER` | 发送邮箱 | 可选 |
| `MAIL_PASS` | 邮箱密码/App Password | 可选 |
| `RECEIVER_MAIL` | 接收邮箱 | 可选 |
| `PORTFOLIO_MODE` | daily/alert/macd | 可选 |

### 2. Telegram 配置（可选）

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)，创建 Bot 获取 Token
2. 搜索 [@userinfobot](https://t.me/userinfobot) 获取你的 Chat ID
3. 将 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 添加到 GitHub Secrets

### 3. 运行脚本

```bash
# 克隆项目
git clone https://github.com/yiyuanlee/VIX_tracker.git
cd VIX_tracker

# 安装依赖
pip install -r requirements.txt

# 运行 VIX 监控
python monitor.py

# 运行持仓监控
python portfolio_monitor.py
```

## 📁 项目结构

```
VIX_tracker/
├── monitor.py              # VIX 监控主程序
├── portfolio_monitor.py   # 持仓追踪 + MACD 程序
├── utils/
│   ├── __init__.py
│   ├── indicators.py      # 技术指标（EMA、MACD、RSI）
│   └── notifications.py   # 通知模块（Telegram、Discord、Email）
├── config/
│   └── positions.yaml     # 持仓配置文件（可单独修改）
├── .github/
│   └── workflows/
│       ├── vix_alert.yml      # VIX 监控 workflow
│       └── portfolio_alert.yml # 持仓监控 workflow
└── README.md
```

## 📊 VIX 监控功能

### 监控的 VIX 指数

| 指数 | 名称 | 说明 |
|------|------|------|
| `^VIX` | 恐慌指数 | 标准 VIX 指数，反映市场恐慌情绪 |
| `^VIX9D` | 9日短期 | 短期波动率预测 |
| `^VIX3M` | 3月中期 | 中期波动率预测 |
| `^VIX6M` | 6月长期 | 长期波动率预测 |

### 预警条件

- VIX 超过阈值（默认 25）
- RSI 超过超买区间（默认 60）
- 期限结构陡峭化（短期 - 长期 > 2）
- VIX 单日跳变超过阈值（默认 15%）
- 3 日内 VIX 涨幅超过 30%

## 💼 持仓追踪功能

### 修改持仓配置

编辑 `config/positions.yaml` 文件即可，无需修改代码：

```yaml
positions:
  - symbol: GOOGL
    shares: 7
    alert_below: 320
    alert_above: 350

  - symbol: MSFT
    shares: 4
    alert_below: 310
    alert_above: 380

macd_tracked:
  - symbol: GOOGL
    shares: 7

  - symbol: ETH-USD
    shares: 0.26

macd_fast: 12
macd_slow: 26
macd_signal: 9
```

### 运行模式

| 模式 | 说明 |
|------|------|
| `daily`（默认） | 发送每日持仓总结 + 自动检查 MACD 交叉 |
| `alert` | 仅检查价格提醒 |
| `macd` | 仅检查 MACD 交叉信号 |

### MACD 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MACD_FAST` | 12 | 快速 EMA 周期 |
| `MACD_SLOW` | 26 | 慢速 EMA 周期 |
| `MACD_SIGNAL` | 9 | 信号线 EMA 周期 |

### MACD 信号说明

- **MACD 金叉 📈**：EMA12 上穿 EMA26，看涨信号
- **MACD 死叉 📉**：EMA12 下穿 EMA26，看跌信号

## ❓ 常见问题

**Q: 如何添加新的追踪标的？**
A: 编辑 `config/positions.yaml`，在 `positions` 列表中添加新条目。

**Q: 如何关闭某个通知渠道？**
A: 不填写对应的 GitHub Secret 即可自动跳过该渠道。

**Q: VIX 阈值如何调整？**
A: 在 GitHub Secrets 中修改 `VIX_THRESHOLD` 值。

**Q: 可以同时追踪股票和加密货币吗？**
A: 是的，在 `config/positions.yaml` 中可以混合添加（如 `ETH-USD`、`SOL-USD`）。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License