# 📈 VIX Alert Bot

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Automated-orange.svg)

这个项目旨在帮助投资者实时监控市场情绪。通过 **GitHub Actions** 定时抓取 Yahoo Finance 的 VIX 指数数据，并在波动率突破预设阈值时发送多渠道提醒。

## ✨ 核心功能

- **多周期 VIX 监控**：同时追踪 VIX、VIX9D（短期）、VIX3M（中期）、VIX6M（长期）
- **自动化运行**：无需服务器，利用 GitHub Actions 每小时自动检查
- **多渠道通知**：支持 Telegram、Discord、Email 三种通知方式
- **可视化图表**：自动生成 VIX 走势图，方便快速了解市场情绪
- **动态阈值**：支持设定固定数值或基于波动百分比触发报警

## 🛠️ 技术栈

- **Data**: `yfinance`
- **Visualization**: `matplotlib`
- **Automation**: `GitHub Actions`
- **Notification**: `Telegram Bot` / `Discord Webhook` / `SMTP`

## 🚀 快速开始

### 1. 配置 GitHub Secrets

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret Name | 说明 | 必需 |
|-------------|------|------|
| `VIX_THRESHOLD` | 预警阈值（默认 25） | 否 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 可选 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可选 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可选 |
| `MAIL_USER` | 发送邮箱 | 可选 |
| `MAIL_PASS` | 邮箱密码/App Password | 可选 |
| `RECEIVER_MAIL` | 接收邮箱 | 可选 |

### 2. Telegram 配置（可选）

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)，创建 Bot 获取 Token
2. 搜索 [@userinfobot](https://t.me/userinfobot) 获取你的 Chat ID
3. 将 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 添加到 GitHub Secrets

### 3. Discord 配置（可选）

1. 在 Discord 服务器设置 → Integrations → Webhooks 创建 Webhook
2. 复制 Webhook URL 添加到 `DISCORD_WEBHOOK_URL`

## 📊 功能说明

### 多周期 VIX 数据

| 指数 | 名称 | 说明 |
|------|------|------|
| `^VIX` | 恐慌指数 | 标准 VIX 指数，反映市场恐慌情绪 |
| `^VIX9D` | 9日短期 | 短期波动率预测 |
| `^VIX3M` | 3月中期 | 中期波动率预测 |
| `^VIX6M` | 6月长期 | 长期波动率预测 |

### 预警阈值

- 默认阈值：`25`
- 可通过 `VIX_THRESHOLD` 环境变量修改
- VIX > 阈值时触发多渠道通知

### 生成的图表

每次运行会自动生成包含以下内容的图表：
- 各周期 VIX 当前值对比柱状图
- 5日历史走势图
- 阈值参考线

## 📁 项目结构

```
VIX_tracker/
├── monitor.py          # 主程序
├── vix_chart.png       # 生成的图表（自动）
├── .github/
│   └── workflows/
│       └── vix_alert.yml   # GitHub Actions 配置
└── README.md
```

## ⚙️ 自定义修改

### 修改阈值
在 GitHub Secrets 中修改 `VIX_THRESHOLD` 值即可。

### 禁用某个通知渠道
不填写对应的 Secrets 即可禁用该渠道。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
