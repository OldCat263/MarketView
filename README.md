# MarketView — Global Market Data Dashboard · 全市场数据展示平台

[English](#english) | [中文](#中文)

---

## English

### Overview

**MarketView** is a one-stop real-time financial market dashboard. View live quotes for stocks, ETFs, indices, crypto, and K-line charts — all from free public APIs. No API keys required.

### Features

- ⚡ **Real-time**: SSE push + 3s heartbeat, data latency < 5s
- 📈 **K-line Charts**: ECharts 5 triple-panel (Price + VOL + MACD), 8 periods (1m~1M), minute chart, MA/BOLL/MACD indicators
- 📰 **News Feed**: Real-time financial news from Sina Finance + Caixin, card-style layout, click to read original article
- 🆓 **Zero Cost**: All data from free public APIs (Tencent, Binance, AkShare, Sina Finance)
- 🚫 **Zero Disk Storage**: Pure in-memory cache + client sessionStorage
- 📱 **Responsive**: Phone / Tablet / Desktop adaptive (breakpoints at 768px, 480px)
- 🔌 **Modular**: 8 independent modules, each with isolated state and data source

### Modules

| # | Module | Data Source (priority L→R) | Items | Status |
|---|--------|---------------------------|-------|--------|
| 1 | 🪙 Crypto | Binance API (requires proxy) | Full real-time | ✅ |
| 2 | 📈 China A-Shares | Tencent qt.gtimg.cn → EastMoney → Sina | 5,528 live | ✅ |
| 3 | 📊 ETF | EastMoney fund_etf_spot_em → THS | 1,516 live | ✅ |
| 4 | 🌏 Hong Kong | Tencent → EastMoney → Sina | 2,773 live | ✅ |
| 5 | 🇺🇸 US Stocks | Tencent qt.gtimg.cn (us prefix) → EastMoney → Sina | 17,209 live | ✅ |
| 6 | 📉 Indices | EastMoney → Sina | 562 live | ✅ |
| 7 | 📈 K-line | Tencent K-line + Binance klines | 750 candles | ✅ |
| 8 | 📰 News | Sina Finance HTTP → Caixin headline | ~50 items | ✅ |

### Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --workers 1

# Open frontend/index.html in browser
```

> ⚠️ `--workers 1` is required — SSE long connections route incorrectly with multiple workers.

### Architecture

```
MarketView/
├── backend/                    # FastAPI backend
│   ├── main.py                 # Entry point: cache + SSE + routes
│   ├── requirements.txt        # Python dependencies
│   └── fetcher/                # Data fetchers (one per module)
│       ├── stock.py            # A-Shares (Tencent priority)
│       ├── etf.py              # ETF (EastMoney)
│       ├── hk.py               # Hong Kong stocks (Tencent → EastMoney → Sina)
│       ├── us.py               # US stocks (Tencent us prefix)
│       ├── index_mod.py        # Indices (EastMoney → Sina)
│       ├── crypto.py           # Cryptocurrency (Binance)
│       ├── kline.py            # K-line data (Tencent + Binance)
│       ├── news.py             # News feed (Sina + Caixin) [V1.8.0]
│       ├── indicators.py       # MA/BOLL/MACD calculation
│       └── utils.py            # Shared utilities
├── frontend/                   # Vanilla HTML/CSS/JS frontend
│   ├── index.html              # Entry page
│   ├── css/main.css            # Dark theme + responsive
│   ├── js/core.js              # Core engine (state, SSE, render)
│   ├── js/kline.js             # K-line chart (ECharts 5)
│   └── js/modules/             # 8 independent modules
├── docs/                       # Documentation (Chinese)
│   ├── API文档.md              # API reference
│   ├── 部署文档.md             # Deployment guide
│   └── 故障排查.md             # Troubleshooting handbook
├── .trae/skills/               # AI Skills (Designer / Executor / Reviewer / Validator)
├── CLAUDE.md                   # Project handbook
└── README.md
```

### Data Sources

All data comes from **free public APIs** — no registration, no API keys:

| Source | Used For | Details |
|--------|----------|---------|
| Tencent `qt.gtimg.cn` | A-Shares, HK, US, K-line | Primary source, batch queries |
| EastMoney via AkShare | ETF, Indices, fallback | Python wrapper, free |
| Sina Finance `feed.mix.sina.com.cn` | News, fallback | Direct HTTP, no key needed |
| Binance `api.binance.com` | Crypto tickers, klines | Free, may need proxy in some regions |

### Real-time Mechanism

- **Shard Rolling Refresh**: Each module's data is split into shards, refreshed in rotating intervals (1~60s)
- **SSE Push**: Server-Sent Events push updated shards to browser, cells flash on change
- **Heartbeat**: Every 3s, maintains green "Live" indicator
- **K-line SSE**: Pushes latest candle every 5s, ECharts updates the last bar without animation

### AI Skills

4 role-based AI Skills in [`.trae/skills/`](.trae/skills/):

| Skill | Role | Trigger |
|-------|------|---------|
| `mv-designer` | Designer | "出设计" / "审批代码" |
| `mv-executor` | Executor | "我是执行者" / "实施" |
| `mv-reviewer` | Reviewer | "我是审批员" / "复审" |
| `mv-validator` | Validator | "跑验收" / "验证模块" |

```bash
# One-click validation (no AI needed)
python .trae/skills/mv-validator/scripts/mv_validate.py all
```

### Deployment

See [deployment guide](docs/部署文档.md) (Chinese). Requires Nginx + systemd + SSL (Let's Encrypt).

### Version

**V1.8.0** — News module + full responsive adaptation. See [CLAUDE.md](CLAUDE.md) for version history.

---

## 中文

### 项目简介

**MarketView** 是一站式全球金融市场实时数据展示平台。免注册、免 API Key，基于免费公开 API 获取全球股票、ETF、指数、加密货币行情和 K 线图，SSE 实时推送 + 分片 diff 闪动刷新。

### 核心特性

- ⚡ **实时推送**：SSE 分片推送 + 3s 心跳保活，数据延迟 < 5s
- 📈 **K 线图表**：ECharts 5 三联图（主图+VOL+MACD），8 周期（1m~月K），分时图，MA/BOLL/MACD 纯 Python 计算
- 📰 **新闻模块**：新浪财经 + 财新头条双源，卡片流渲染，点击跳转原文
- 🆓 **零成本**：全部免费公开 API（腾讯行情、Binance、AkShare、新浪财经）
- 🚫 **零磁盘存储**：纯内存缓存 + 客户端 sessionStorage，不落盘
- 📱 **响应式适配**：手机/平板/桌面三端自适应（768px、480px 双断点）
- 🔌 **模块化隔离**：8 个独立模块，各自封装状态、数据源、渲染逻辑

### 模块一览

| # | 模块 | 数据源 | 数据量 | 首启速度 |
|---|------|--------|--------|----------|
| 1 | 🪙 加密货币 | Binance API | 全量实时 | 0.5s |
| 2 | 📈 A股 | 腾讯 qt.gtimg.cn | 5,528 条 | 63ms |
| 3 | 📊 ETF | 东财 fund_etf_spot_em | 1,516 条 | ~5s |
| 4 | 🌏 港股 | 腾讯 → 东财 → 新浪 | 2,773 条 | ~2min（AkShare 冷启） |
| 5 | 🇺🇸 美股 | 腾讯 qt.gtimg.cn | 17,209 条 | ~8min（首拉代码表） |
| 6 | 📉 指数 | 东财 → 新浪 | 562 条 | <1s |
| 7 | 📈 K线 | 腾讯 K线 + Binance | 750 根 | <2s |
| 8 | 📰 新闻 | 新浪财经 → 财新头条 | ~50 条 | ~2s |

### 快速开始

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --workers 1    # ⚠️ 必须 --workers 1（SSE 长连接路由要求）
# 浏览器打开 frontend/index.html
```

### 项目结构

```
MarketView/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 入口：分片缓存 + SSE 推送 + 路由
│   ├── requirements.txt        # Python 依赖
│   └── fetcher/                # 数据获取层（每模块独立文件）
│       ├── stock.py            # A股（腾讯优先）
│       ├── etf.py              # ETF（东财 → 同花顺）
│       ├── hk.py               # 港股（腾讯 → 东财 → 新浪 三源 fallback）
│       ├── us.py               # 美股（腾讯 us 前缀）
│       ├── index_mod.py        # 指数（东财 → 新浪）
│       ├── crypto.py           # 加密货币（Binance，自动扫描代理）
│       ├── kline.py            # K线（腾讯日/周/月 + mkline 分钟 + Binance）
│       ├── news.py             # 新闻（新浪财经 HTTP + 财新头条）[V1.8.0]
│       ├── indicators.py       # 技术指标（MA/BOLL/MACD 纯 Python）
│       └── utils.py            # 工具函数
├── frontend/                   # 原生 HTML/CSS/JS 前端
│   ├── index.html              # 入口页面
│   ├── css/main.css            # 暗色主题 + 响应式
│   ├── js/core.js              # 核心引擎（状态管理/SSE/渲染/缓存）
│   ├── js/kline.js             # K线图表（ECharts 5）
│   └── js/modules/             # 8 个独立模块
├── docs/                       # 文档
│   ├── API文档.md              # 接口字段表
│   ├── 部署文档.md             # 部署指南（Nginx + systemd + SSL）
│   ├── 故障排查.md             # 故障排查手册
│   ├── 开发手册.md             # 设计哲学总纲
│   ├── 设计师入门指南.md       # 设计师 Onboarding
│   ├── 执行者入门指南.md       # 执行者 Onboarding
│   └── 审批员入门指南.md       # 审批员 Onboarding
├── .trae/skills/               # 4 个 AI Skill（设计师/执行者/审批员/验收）
├── CLAUDE.md                   # 项目手册（版本历史/铁律/审计清单）
└── README.md
```

### 数据源说明

全部基于**免费公开 API**，无需注册或 API Key：

| 数据源 | 用途 | 特点 |
|--------|------|------|
| 腾讯 `qt.gtimg.cn` | A股/港股/美股/K线 | 批量查询，50 只/请求，首源 |
| 东财（通过 AkShare） | ETF/指数/备源 | Python 封装，免费 |
| 新浪财经 | 新闻主源/行情备源 | 直接 HTTP，无需 Key |
| Binance | 加密货币 | 部分区域需代理 |

### 实时机制

- **分片滚动刷新**：每模块数据分片，轮转间隔刷新（1~60s）
- **SSE 推送**：后端推分片增量，前端 `EventSource` 接收，单元格 diff 闪动
- **心跳保活**：每 3s 推 `shard:-1`，维持绿色"实时"指示灯
- **K线 SSE**：每 5s 推最新 K 线，ECharts 无动画更新最后一根

### 设计铁律

| # | 铁律 |
|---|------|
| 1 | 核心文件不变，不许随意加文件 |
| 2 | 先改 CLAUDE.md 再写代码 |
| 3 | 零本地存储 |
| 4 | 数据源仅限免费公开 API |
| 5 | 做完记录版本历史 |
| 6 | 每个模块完全独立封装 |
| 7 | 每次新需求必须同步更新文档 |
| 8 | 设计师改完代码必须审批执行者的技术文档 |

### AI Skill（按角色触发，节省 60%~70% token）

| Skill | 角色 | 触发语 |
|-------|------|--------|
| `mv-designer` | 设计师 | "出设计" / "审批代码" / "我是设计师" |
| `mv-executor` | 执行者 | "我是执行者" / "实施" / "改代码" |
| `mv-reviewer` | 审批员 | "我是审批员" / "复审" |
| `mv-validator` | 验收员 | "跑验收" / "验证模块" |

```bash
# 自动化验收脚本
python .trae/skills/mv-validator/scripts/mv_validate.py all     # 全量
python .trae/skills/mv-validator/scripts/mv_validate.py sse     # SSE 心跳
python .trae/skills/mv-validator/scripts/mv_validate.py kline   # K线接口
python .trae/skills/mv-validator/scripts/mv_validate.py rules   # 铁律自检
```

### 文档导航

| 我想... | 看这个 |
|---------|--------|
| 快速了解项目 | 👉 你正在看（README） |
| 查项目状态/版本/已完成功能 | [CLAUDE.md](CLAUDE.md) |
| 写代码/改模块/遵循设计原则 | [开发手册](docs/开发手册.md) |
| 新接手设计师 | [设计师入门指南](docs/设计师入门指南.md) |
| 新接手执行者 | [执行者入门指南](docs/执行者入门指南.md) |
| 新接手审批员 | [审批员入门指南](docs/审批员入门指南.md) |
| 调 API / 查接口字段 | [API 文档](docs/API文档.md) |
| 部署到服务器 | [部署文档](docs/部署文档.md) |
| 排障 / 找 bug | [故障排查](docs/故障排查.md) |

### 技术栈

- **Backend**: Python 3.11+, FastAPI, httpx, AkShare, uvicorn
- **Frontend**: Vanilla JS (no framework), ECharts 5, Server-Sent Events
- **Deploy**: Nginx + systemd + Let's Encrypt SSL
- **Chart**: ECharts 5 candlestick + VOL + MACD triple-panel

### License

MIT

---

**Version**: V1.8.0 · **Last Updated**: 2026-06-27
