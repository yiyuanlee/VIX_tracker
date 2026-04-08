# 📈 VIX Alert Bot

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Automated-orange.svg)

这个项目旨在帮助投资者实时监控市场情绪。通过 **GitHub Actions** 定时抓取 Yahoo Finance 的 VIX 指数数据，并在波动率突破预设阈值时发送邮件提醒。

### ✨ 核心功能
- **自动化运行**：无需服务器，利用 GitHub Actions 每小时自动检查。
- **动态阈值**：支持设定固定数值或基于波动百分比触发报警。
- **零成本方案**：完全基于开源库与免费的 CI/CD 工具。

### 🛠️ 技术栈
- **Data**: `yfinance`
- **Automation**: `GitHub Actions`
- **Notification**: `SMTP / smtplib`
