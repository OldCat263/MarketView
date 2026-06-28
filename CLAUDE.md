# CLAUDE.md — MarketView 全市场数据展示平台

> **写给后来者**：无论你是人类还是 AI，先读完这个再动手。
> **当前版本**：V2.2.7（生产环境错误修复 5 项：美股降级+SSE 抑制+卡片就绪同步+重试退避+加密说明）
> **最后更新**：2026-06-28

---

## 项目概览

- **名称**：MarketView
- **干什么**：一站式展示全球金融市场实时数据 + K线图 + 新闻 + 智能预测
- **架构**：FastAPI 后端 + 多文件 HTML 前端（HTML骨架+CSS+核心引擎+模块注册） + 服务端磁盘缓存（V2.0.2）+ 首屏快照（V1.8.6）
- **数据源**：AkShare + 腾讯 qt.gtimg.cn + Binance + 新浪 + 东财 push2（V2.2.0）+ Pollinations/智谱 AI（V2.0.0+）— 全部免费公开 API
- **实时机制**：分片滚动刷新（错峰启动 V2.0.3）+ SSE 推送 + 3s 心跳（V1.6.0.6）
- **图表**：ECharts 5（K线/V1.7.0+）
- **角色**：设计师 / 执行者 / 审批员 / 用户（四方协作流程详见 [开发手册 §十](./docs/开发手册.md)）

## 固定文件清单

| 文件 | 职责 |
|------|------|
| `CLAUDE.md` | 📖 项目手册（**本文件**）|
| `docs/开发手册.md` | 🎨 设计哲学总纲（设计者手册）|
| `docs/设计师入门指南.md` | 👶 设计师 Onboarding（2.5h 上手 + 设计稿模板）|
| `docs/执行者入门指南.md` | 🔨 执行者 Onboarding（2h 上手 + 回报模板）|
| `docs/审批员入门指南.md` | 🔍 审批员 Onboarding（1.5h 上手 + 标级模板）|
| `docs/API文档.md` | 🔌 接口定义（含 9 模块 + K线 + 预测）|
| `docs/部署文档.md` | 🚀 部署指南（Nginx + systemd + SSL + .cache 权限）|
| `docs/故障排查.md` | 🛠️ 故障排查手册（9 大类 + 预测/K线案例）|
| `backend/main.py` | FastAPI 入口（V2.0.2 磁盘缓存 + V2.0.3 错峰 + V2.2.0 数据源分离）|
| `backend/fetcher/` | 数据获取模块（17 个文件：crypto/stock/etf/hk/us/index/news + kline + indicators + chanlun + backtest + scorer + fundamentals + ai_analyzer + utils）|
| `backend/requirements.txt` | Python 依赖 |
| `frontend/index.html` | 前端入口（V1.8.6 首屏快照 + 9 模块卡片）|
| `frontend/css/main.css` | 样式（V1.9.0 predict 面板 + V1.8.6 就绪信号）|
| `frontend/js/core.js` | 核心引擎（V1.6.0.16 viewTime + 9 模块注册）|
| `frontend/js/kline.js` | K线图（V1.7.0 Step 3+5 ECharts 三联图 + SSE）|
| `frontend/js/modules/*.js` | 9 模块独立文件 |
| `frontend/snapshot.json` | V1.8.6 首屏快照（main.py 启动时生成）|
| `.cache/` | V2.0.2 磁盘缓存（spot_cache.json + kline_cache.json + watchlist.json）|
| `chanlun/` | 参考资料（只读）|
| `.trae/skills/` | ⭐ 4 个 AI Skill（designer/executor/reviewer/validator），按角色触发节省 token |

## 模块清单

| # | 模块 | 数据源（优先级从左到右） | 数量 | 状态 |
|---|------|------------------------|------|------|
| 1 | 🪙 加密货币 | Binance API（需代理，服务器无代理时显示未检测） | 全量实时 | ✅ |
| 2 | 📈 A股 | **东财 push2（V2.2.0 主源）** → 腾讯 qt.gtimg.cn → 新浪 | 5528 条 | ✅ |
| 3 | 📊 ETF | **东财 push2（V2.2.0 主源）** → fund_etf_spot_em → 同花顺 | 1516 条 | ✅ |
| 4 | 🌏 港股 | 腾讯 → 东财 stock_hk_spot_em → 新浪 stock_hk_spot | 2773 条 | ✅ |
| 5 | 🇺🇸 美股 | **腾讯 qt.gtimg.cn（us 前缀，3 分片 V2.1.0）** → 东财 → 新浪 | 17209 条 | ✅ |
| 6 | 📉 指数 | **东财 push2（V2.2.0 主源）** → 新浪（global 需海外网络，限流时为空） | 562 条 | ✅ |
| 7 | 📰 新闻 | 新浪财经 feed.mix.sina.com.cn（主）→ 财新头条 stock_news_main_cx（备） | 50 条/次 | ✅ V1.8.0 |
| 8 | 🤖 智能预测 | 缠论（chanlun.py）+ 回测（backtest.py）+ 7维评分（scorer.py）+ 基本面（fundamentals.py）+ AI 分析（ai_analyzer.py，Pollinations/智谱） | 200 排行/模块 | ✅ V1.9.0 |
| 9 | 📈 K线 | 腾讯 K线接口 + Binance klines（6 模块） | 750 根/请求 | ✅ V1.7.0 |

## 数据源详解

### A股：东财 push2（V2.2.0 改）+ 腾讯兜底
- V2.2.0 起主源改东财 push2（8 分片 × 5s = 40s 完整轮转）
- 腾讯 qt.gtimg.cn 兜底（50 只/请求）
- 字段：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、最高、最低、今开、昨收、振幅、换手率、量比

### ETF：东财 push2（V2.2.0 改）
- V2.2.0 起主源东财 push2（5 分片 × 5s = 25s 完整轮转）
- 东财 fund_etf_spot_em + 同花顺兜底

### 港股：腾讯 → 东财 → 新浪（V1.6.0.1 改，保留）
- 腾讯为主源（10 只/请求）
- 东财 AkShare `stock_hk_spot_em` 冷启动 ~2 分钟
- 新浪 `stock_hk_spot` 兜底
- 多源 fallback 解决 RemoteDisconnected 导致 0 行

### 加密货币：Binance API（V1.6.0 起不变）
- 端点：`api.binance.com/api/v3/ticker/24hr`
- 自动扫描代理端口：7897/7890/10809/10808/1080/8118/8888
- 用户也可手动设置 `CRYPTO_PROXY` 环境变量

### 美股：腾讯 qt.gtimg.cn（V2.1.0 改 3 分片）
- V2.1.0 起改 3 分片 × 5s = 15s 完整轮转（150 只/批 × 50 = 3 批）
- us 前缀（V1.6.0 改）
- 东财/新浪兜底

### 指数：东财 push2（V2.2.0 改）
- V2.2.0 起主源东财 push2（1 分片 × 5s = 5s）
- 新浪兜底（global 字段需海外网络）

### 新闻：新浪财经 → 财新头条（V1.8.0+）
- 主源：feed.mix.sina.com.cn（50 条/次，60s 刷新）
- 备源：AKShare stock_news_main_cx
- 字段：datetime / content / source / url
- 渲染：卡片流（V1.8.5+ URL 跳转 + 年份格式）

### 智能预测：缠论 + 10 因子 + AI（V1.9.0+）
- 七维评分（scorer.py）：缠论 25% + 回测 20% + 量化因子 15% + 基本面 15% + 技术指标 10% + 资金面 10% + 新闻 5%
- 缠论进阶层（chanlun.py）：包含处理 → 分型 → 笔 → 线段 → 中枢 → 走势 → 背驰 → 二三买卖点
- 回测（backtest.py）：9 指标
- 基本面（fundamentals.py）：5 接口 + TTL 300s
- AI 分析（ai_analyzer.py）：Pollinations 主源 + 智谱 fallback
- V2.2.2 加速：启动 10s 快刷 5 轮，存够切 300s
- V2.2.0 限定：只预测 stock + etf（不再预测 index）

### K线（V1.7.0+）：腾讯 K线接口 + Binance Klines
- A股/ETF/指数：腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`
- 港股：腾讯 `appstock/app/hfqkline/get`（hk 前缀，3 源 fallback）
- 美股：腾讯 `appstock/app/usfqkline/get`（us 前缀）
- 加密：Binance `/api/v3/klines`
- 8 周期：1m/5m/15m/30m/60m/1d/1w/1M
- 指标：MA5/10/20/60/120/250 + BOLL(20/2) + MACD(12/26/9) + RSI/ATR/VPT（V1.9.0 加）
- V2.0.2 共享 K线缓存（utils.py：内存 + 磁盘 + LRU 500 key）
- V1.7.0 Step 5 K线 SSE 5s 推送（last_hash 增量 + heartbeat 兜底）

## 前端架构
- **首页**：9 张卡片网格（3×3），V1.8.6 起根据 `/api/health` 卡片**明亮/半透明**区分就绪状态
- **数据视图**：表格 + 搜索 + 排序 + 翻页（50条/页）
- **新闻视图**（V1.8.0）：卡片流，时间倒序，无翻页
- **预测视图**（V1.9.0）：**两 Tab（排行 + AI 内嵌展开）**，排行分页 20 条/页；signals 切片内部保留备用（V2.2.5 明确无"信号"独立 Tab — 文档-实现对齐）
- **K线视图**（V1.7.0）：独立行情页（顶部导航"行情"入口） + ECharts 三联图（主+VOL+MACD）
- **首屏快照**（V1.8.6）：`fetch('snapshot.json')` 零 HTTP 渲染，main.py 启动时写盘
- **实时推送**：SSE (`/api/stream/{module}`) + 分片滚动刷新，单元格 diff 闪动
- **心跳机制**（V1.6.0.6）：后端每 3s 推 `shard=-1` 空数据，前端刷新 `fetchTime` 维持绿点
- **客户端缓存**：sessionStorage（前端状态恢复，**非实时数据源**，TTL 15s）
- **模块隔离**：ST 对象独立存储每模块的 rows/cols/page/sort/search，互不干扰
- **时间显示三件套**：globalStamp（UI 时钟，每秒跳）+ viewTime（客户端实时时间，V1.6.0.8 回滚到 V1.6.0.3 行为，每秒跳）+ liveStatus（数据新鲜度，SSE 推时"实时"绿点，断连时"离线"红点）

## 服务端架构（V2.0+）
- **内存缓存** `_cache[key] = {'shards': {i: {'data': [], 'ts': 0}}, 'cols': [...]}` — 分片滚动
- **磁盘缓存** `backend/../.cache/spot_cache.json` — V2.0.2 启动恢复 + 每 30s dump（原子写入 tmp+os.replace）
- **K线磁盘缓存** `backend/../.cache/kline_cache.json` — V2.0.2 内存+磁盘+LRU 500 key
- **自选列表** `backend/../.cache/watchlist.json` — V2.0.3 用户自选股票持久化
- **首屏快照** `frontend/snapshot.json` — V1.8.6 启动后写一次，前端 fetch 后零 HTTP 渲染
- **错峰启动**（V2.0.3）：start_delay 0/5/10/15/20s 避免冷启动挤数据源
- **预测加速**（V2.2.2）：10s 快刷 5 轮 + 自动切 300s

## 🔴 铁律

| # | 铁律 |
|---|------|
| 1 | 核心文件不变，不许随意加文件 |
| 2 | 先改 CLAUDE.md 再写代码 |
| 3 | **服务端缓存允许**（内存 + 磁盘性能优化），**数据源必须免费公开 API**（V2.0.2 改：磁盘缓存是性能优化，非业务数据）|
| 4 | 数据源仅限免费公开 API |
| 5 | 做完记录版本历史 |
| 6 | 每个模块完全独立封装 |
| 7 | **每次新需求必须同步更新 [设计师入门指南 §0](./docs/设计师入门指南.md) 的同步更新规则** |
| 8 | **设计师：改完代码必须审批执行者改的技术文档** |

> **铁律 3 豁免清单**（V2.0.2 设计师审批）：
> - `backend/main.py` _save_cache 写 spot_cache.json（性能优化）
> - `backend/main.py` _save_watchlist 写 watchlist.json（V2.0.3 用户自选）
> - `backend/main.py` _write_snapshot 写 frontend/snapshot.json（V1.8.6 首屏优化）
> - `backend/fetcher/us.py` _load_us_codes 写 _US_CODES_FILE（白名单缓存）
> - `backend/fetcher/utils.py` _save_kline_cache 写 kline_cache.json（V2.0.2 性能优化）
> - `backend/fetcher/us.py` _save_us_disabled 写 us_disabled.json（V2.2.7 降级状态持久化）
>
> 上述写盘均为**性能优化**，非业务数据源；数据本身仍来自免费公开 API。

## 模块加载速度（V2.2.0 实测 2026-06-28）

| 模块 | 分片 | interval | start_delay | 完整轮转 | 状态 |
|------|------|----------|-------------|----------|------|
| 🪙 加密货币 | 1 | 5s | 0s | 5s | ✅ Binance 需代理 |
| 📈 A股 | 8 | 5s | 0s | 40s | ✅ V2.2.0 东财 push2 |
| 📊 ETF | 5 | 5s | 5s | 25s | ✅ V2.2.0 东财 push2 |
| 🌏 港股 | 6 | 5s | 10s | 30s | ✅ 腾讯主源 |
| 🇺🇸 美股 | **3** | 5s | 15s | 15s | ✅ V2.1.0 改 3 分片（150 只/批）|
| 📉 指数 | 1 | 5s | 20s | 5s | ✅ V2.2.0 东财 push2 |
| 📰 新闻 | 1 | **60s** | 0s | 60s | ✅ V1.8.0 新浪 50 条/次 |
| 🤖 预测 | 1 | **300s**（首轮 10s×5） | 45s | 5min | ✅ V1.9.0 缠论 + 7 维 |

> 错峰启动（V2.0.3）：stock → etf → hk → us → index 间隔 5s，避免冷启动全挤数据源。
> 预测（V2.2.2）：前 5 轮 10s 快刷，存够切 300s。
> V1.6.0 起：分片缓存 + SSE 实时推送，浏览器侧看到的是**持续跳动**的实时行情。
> V1.6.0.6 起：每 3s 心跳维持客户端 liveStatus 绿点。
> V1.8.6 起：`/api/health` 返回 9 模块就绪状态，前端卡片明亮/半透明。
> US 首次 8min 是 `_load_us_codes()` 一次性下载 17636 条代码，磁盘缓存后秒级。
> HK 首次 2min 是 AkShare `stock_hk_spot()` 冷启动一次成本，磁盘缓存后秒级。
> V2.0.2 起：磁盘缓存每 30s dump 一次，进程重启秒级恢复。

## 审计流程

每次重大修改后，按以下步骤自检：

### 1. 文档检查
- [ ] CLAUDE.md 模块清单（9 模块）是否反映最新状态
- [ ] CLAUDE.md 版本历史是否更新到最新 commit
- [ ] 文档中是否有硬编码的数量/限制（应标注"全量实时"）

### 2. 数据源检查（9 模块）
- [ ] 逐模块调用 API，确认返回数据量 > 0
- [ ] 关键列（代码、名称、最新价、涨跌幅）是否有值
- [ ] A股特有列（振幅、换手率、量比）是否非空
- [ ] V2.2.0 数据源切换（stock/etf/index→东财 push2）是否生效
- [ ] news 60s 刷新是否正常
- [ ] predict daemon 是否启动（看 main.py 日志）

### 3. 实时性检查
- [ ] SSE 推送是否在 3~5s 内更新（按模块分片周期）
- [ ] **3s 心跳**（V1.6.0.6）是否持续收到 `shard:-1` 数据
- [ ] 浏览器开发者工具 Network → EventStream 是否持续收到 `data:` 行
- [ ] **viewTime 每秒跳**（V1.6.0.8 客户端实时时间，与 SSE 解耦）
- [ ] **viewTime 在 openModule 切模块瞬间不显示数据时间**（V1.6.0.16 删 openModule 内的 viewTime=fetchTime 赋值）
- [ ] **liveStatus 由 fetchTime 算 ago**（心跳维持绿点，>15s 显式"离线"红点，V1.6.0.8）
- [ ] **首屏快照**（V1.8.6）`/api/health` 9 模块就绪状态

### 3.5 K线专项检查（V1.7.0+）
- [ ] 6 模块各跑一次 `/api/kline/{m}/{code}`，data 数组非空
- [ ] 8 周期切换都正常返回（1m/5m/15m/30m/60m/1d/1w/1M）
- [ ] MA/BOLL/MACD 指标计算结果正确（对账测试）
- [ ] ECharts 三联图渲染正常（主图 + VOL + MACD）
- [ ] K线 SSE 5s 推最新一根，ECharts 实时更新最后一根
- [ ] K线磁盘缓存命中（`/api/kline/stock/sh600519` 二次响应 < 100ms）

### 3.6 预测专项检查（V1.9.0+）
- [ ] `/api/predict/rank/stock` 返回 50 条排行
- [ ] `/api/predict/analyze/stock/sh600519?with_ai=true` 完整流水线 < 5s
- [ ] AI source 字段：pollinations=正常 / local=降级
- [ ] V2.2.2 加速：首轮 10s 5 次，存够切 300s

### 4. 模块隔离检查
- [ ] 切换模块后数据是否独立，不串台
- [ ] 搜索/排序/翻页是否每个模块独立
- [ ] `ST` 对象是否正确保存和恢复每个模块状态

### 5. 代码规范检查
- [ ] `backend/` 下是否有本地文件读写（搜 `open(` `write(` `dump(`）— V2.0.2 后豁免清单见铁律 3
- [ ] 是否有硬编码数据列表或数量限制
- [ ] 数据源是否全部来自免费公开 API
- [ ] Python 导入正常、JS 语法正常
- [ ] `node -c frontend/js/modules/*.js` 无语法错误
- [ ] `node -c frontend/js/kline.js` 无语法错误

```bash
# 快速验证命令
cd backend && python -c "from main import app; import fetcher; print('OK')"
curl -s http://localhost:8000/api/health | python -m json.tool
curl -s http://localhost:8000/api/etf/spot | python -c "import sys,json; print(len(json.load(sys.stdin)['data']),'ETF')"
python .trae/skills/mv-validator/scripts/mv_validate.py all  # 9 模块 + SSE + K线 + 铁律
```

## 如何运行

```bash
cd backend
pip install -r requirements.txt

# V1.6.0 起必须用 --workers 1（不要用 4）
# 原因：SSE 长连接 + 免费 API 限流，4 worker 会导致：
#   1. SSE 路由只在 1/4 worker 上生效，连接被路由到其他 worker 会立即断
#   2. 4 倍数据源拉取，免费 API 容易被封
#   3. 单进程足够支撑 9 模块 7 万+条数据并发
uvicorn main:app --workers 1
# 浏览器打开 frontend/index.html
```

## ⭐ AI Skill（节省 token）

4 个 Skill 按角色触发，加载极简 description（~200 字符），按需 Read 文档。**Token 节省 60%~70%**。

| Skill | 触发场景 | 作用 |
|-------|----------|------|
| `mv-designer` | "出设计"/"审批代码"/"我是设计师" | 出设计稿 + 维护 CLAUDE.md + 审批执行者 |
| `mv-executor` | "我是执行者"/"实施"/"改代码" | 写代码 + 跑验收 + 同步技术文档 + 回报 |
| `mv-reviewer` | "我是审批员"/"复审" | 复审 + 标 P0/P1/P2 + 改进意见 |
| `mv-validator` | "跑验收"/"验证模块" | 自动化验收（9 模块数据量 + SSE 心跳 + K线 + 预测 + 铁律）|

**验收脚本**（免 AI 介入）：
```bash
python .trae/skills/mv-validator/scripts/mv_validate.py all       # 全部
python .trae/skills/mv-validator/scripts/mv_validate.py modules   # 9 模块数据量
python .trae/skills/mv-validator/scripts/mv_validate.py sse       # SSE 心跳
python .trae/skills/mv-validator/scripts/mv_validate.py kline     # K线接口
python .trae/skills/mv-validator/scripts/mv_validate.py predict   # 预测端点（V2.0.0+）
python .trae/skills/mv-validator/scripts/mv_validate.py rules     # 铁律自检
```

> 详见 [.trae/skills/](./.trae/skills/) 目录。

## 已完成清单（按版本）

### V2.2.4 文档全面同步（2026-06-28）
- CLAUDE.md V1.7.0 → V2.2.0 全面重写（差 5 个大版本追上）
- 9 模块清单（加 news + predict + K线完整）
- 数据源 V2.2.0 变化（stock/etf/index→东财 push2）
- 加 V2.0.2 磁盘缓存 / V1.8.6 首屏快照 / V1.8.6 健康检查
- 加 V2.0.3 错峰启动 / V2.2.2 预测加速 / V2.2.3 predict 排行补 name
- 铁律 3 豁免清单（5 处性能优化写盘）
- README.md / 4 份入门指南 / 4 个 Skill 项目状态行对齐 V2.2.0

### V2.2.0 智能预测 + 数据源分离（2026-06-28）
- 6 大模块：chanlun.py（缠论进阶层）+ backtest.py（9 指标回测）+ scorer.py（7 维评分）+ fundamentals.py（5 接口）+ ai_analyzer.py（Pollinations/智谱）+ predict.js（4 Tab）
- 4 个端点：/api/predict/analyze、/api/predict/rank、/api/fundamental、/api/predict/batch
- 启动 10s 快刷 5 轮 + 自动切 300s
- 只预测 stock + etf

### V1.8.0 新闻模块（2026-06-27）
- 新浪财经（主）+ 财新头条（备）双源 fallback
- 60s 低频防限流
- 卡片流渲染（V1.8.5 URL 跳转 + 年份格式）

### V1.8.6 秒开体验（2026-06-27）
- `/api/health` 健康检查（9 模块就绪状态）
- 卡片明亮/半透明区分
- `frontend/snapshot.json` 首屏快照（零 HTTP 渲染）

### V1.7.0 K线图（2026-06-26）
- Step 1 后端 kline.py+indicators.py
- Step 2 港股 K线 3 源 fallback
- Step 3 前端 ECharts 三联图
- Step 4 数据集成 + 选代码
- Step 5 SSE 5s 推最新 K线
- V1.7.0 完整：MA5/10/20/60/120/250 + BOLL(20/2) + MACD(12/26/9) + 8 周期

### V1.6.0.16 viewTime 收尾（2026-06-26）
- viewTime 移出 if(tab) 块
- openModule 删 viewTime 数据时间赋值
- 4 场景全覆盖：首页/切模块/数据静止/SSE 断连

## 版本历史

| 版本 | 日期 | 做了什么 |
|------|------|----------|
| V1.0.0~V1.6.0 | 2026-06-24~25 | 项目立项 + 6 模块 + 实时化 + K线骨架（详见 git log）|
| V1.6.0.1~0.16 | 2026-06-25~26 | viewTime 系列修复（10 个子版本）+ 心跳 + 文档化 |
| V1.7.0 | 2026-06-26 | K线图（5 步分开发：后端 → HK fallback → ECharts 骨架 → 数据集成 → SSE）|
| V1.8.0 | 2026-06-27 | 新闻模块（新浪 + 财新 fallback）|
| V1.8.5 | 2026-06-27 | 新闻卡片 URL 跳转 + 年份格式 |
| V1.8.6 | 2026-06-27 | 秒开体验（健康检查 + 卡片就绪信号 + 首屏快照）|
| V1.9.0 | 2026-06-27~28 | 智能预测系统（10 步：API 端点 → chanlun 基础层 → fundamentals → backtest → scorer → ai_analyzer → kline 优化 → predict.js → CSS → 文档）|
| V2.0.0 | 2026-06-28 | 文档同步（API §11 预测端点 + 故障排查 §6.6-6.8）|
| V2.0.1 | 2026-06-28 | 智能预测加载加速 + MCP（context7）|
| V2.0.2 | 2026-06-28 | 磁盘缓存（spot_cache.json + kline_cache.json，30s dump）|
| V2.0.3 | 2026-06-28 | 错峰启动（start_delay 0~45s）+ 自选列表（watchlist.json）|
| V2.1.0 | 2026-06-28 | 美股改腾讯 3 分片（150 只/批）|
| V2.2.0 | 2026-06-28 | **数据源分离**：stock/etf/index→东财 push2，预测只做 stock+etf |
| V2.2.1 | 2026-06-28 | 健康检查加 predict 缓存判断 |
| V2.2.2 | 2026-06-28 | 预测加速：10s 快刷 5 轮 + 自动切 300s |
| V2.2.3 | 2026-06-28 | predict 排行补 name（从 spot 缓存映射）|
| V2.2.4 | 2026-06-28 | 文档全面同步：CLAUDE.md V1.7.0→V2.2.0 重写（差 5 个大版本追上）+ README.md/4 份入门指南/4 个 Skill 项目状态行对齐 V2.2.0 |
| **V2.2.5** | **2026-06-28** | **紧急热修（深挖 5 个 P0 + 1 个 P2）**：<br>• **P0-1** [main.py:90-112 `_save_cache`] 锁内 `copy.deepcopy` + `f.flush() + os.fsync` 防止 roller race + crash 丢数据<br>• **P0-2** [predict.js:25] 删 `index` 下拉项（V2.2.0 起只 stock+etf）<br>• **P0-3** [CLAUDE.md:118] predict 文档对齐："三 Tab（信号/排行/AI）" → "两 Tab（排行+AI 内嵌展开，signals 切片内部保留备用）"<br>• **P0-4** [kline.js:783-832] SSE `onerror` 加 5 次重试上限 + `MV.showToast` 错误提示<br>• **P0-5** [core.js:107-139] `loadModule` 加 try/catch，错误时显式 `fetchTime` + ❌ 状态 + toast<br>• **P2-22** [main.py:108-109] `_save_cache` 缺 `flush/fsync` 顺带修 |
| **V2.2.6** | **2026-06-28** | **P1 集中修复（11 项）+ 仓库瘦身**：<br>• **P1-1/P1-2** [predict.js:235-263] `viewDetail` 精确匹配代码 + try/catch + loading 态<br>• **P1-3** [main.py:138-147] `_load_watchlist` 静默吞错 → print 错误<br>• **P1-5** [main.py:494-496] K线 `count` 上限 1500 防内存/限流<br>• **P1-6** [main.py:532-535,591-596] 错误信息不外泄（返回通用错误码 + 内部日志）<br>• **P1-7** [core.js:363] flash 闪动列扩展（换手率/量比/振幅）<br>• **P1-8** [predict.js:77] `predictState` 全局 → `MV.Predict.state` 命名空间<br>• **P1-9** [kline.js:599/717/849,807-818] SSE onmessage 一次性捕获本地引用 + loadData 期间 `lastResp=null` 防脏写孤儿数据<br>• **P1-10** [main.py:764-765] `_sse_queues.remove` 防御性检查<br>• **P1-11** [main.py:355] roller/heartbeat 启动失败仅 print，不阻止启动<br>• **仓库瘦身** 删除 60+ 根目录临时脚本（`check_*.py` / `hotfix_*.py` / `push_hotfix*.py` / `tmp_*.py` / `deploy_*.py` / `verify.py`）+ `.openclaw/` 100+ SSH scratch 脚本（含硬编码凭据）+ `.agents/` 30+ agent identity + `.claude/plans/` 3 个过期设计 + `.claude/skills/` 100+ Claw 本地 skill + `docs/V1.*-实施指令.md` × 5 + `docs/V1.9.0-*.md` × 3 + `docs/V2.0.*-*.md` × 3（仅保留 6 份核心文档 + 3 份角色指南）|
| **V2.2.7** | **2026-06-28** | **生产环境错误修复（5 项）**（基于 `https://oldcat.site/` 浏览器实际错误汇总）：<br>• **P0-1 美股数据源** [us.py] 加 **降级占位符**：连续 3 次 fetch 失败/空数据 → 标记 `_us_disabled=True`，避免无效请求刷控制台<br>• **P0-2 美股 SSE 抑制** [core.js:296-300] `_connectSSE` 前先查 `/api/health`，`health[m]===false` 时**不建立连接**（避免 `net::ERR_ABORTED` 反复刷红）<br>• **P1 卡片就绪同步** [core.js:415-433] 健康检查轮询**直接读 health 字段**：`health[m.id]===false` 时卡片显示 ❌ + 半透明（之前只改 opacity，不改 status 图标）<br>• **P2-1 美股重试退避** [us.py] 连续失败计数器 + 指数退避（30s→60s→120s→300s→600s 上限），避免被限流时反复打数据源<br>• **P2-2 加密货币说明** [index.html] 卡片增加 tooltip「需配置 `CRYPTO_PROXY` 环境变量」说明 |

> **当前 V2.2.0 是封版基线**。后续 V2.3.x/V2.4.x 在此基础上迭代。
> **V1.6.0.16 之前版本**（viewTime 早期）已废弃，详见 git log。
