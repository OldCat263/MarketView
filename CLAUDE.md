# CLAUDE.md — MarketView 全市场数据展示平台

> **写给后来者**：无论你是人类还是 AI，先读完这个再动手。

---

## 项目概览

- **名称**：MarketView
- **干什么**：一站式展示全球金融市场实时数据 + K线图
- **架构**：FastAPI 后端 + 多文件 HTML 前端（HTML骨架+CSS+核心引擎+模块注册） + 客户端 sessionStorage 缓存
- **数据源**：东方财富 push2（stock/etf/index国内）+ 腾讯 qt.gtimg.cn（hk/us）+ Binance（crypto）+ AkShare（预测/指数全球）（全部免费公开 API）
- **实时机制**：分片滚动刷新 + SSE 推送 + 3s 心跳（V1.6.0.6）
- **图表**：ECharts 5（K线/V1.7.0+）
- **角色**：设计师 / 执行者 / 审批员 / 用户（四方协作流程详见 [开发手册 §十](./docs/开发手册.md)）

## 固定文件清单

| 文件 | 职责 |
|------|------|
| `CLAUDE.md` | 📖 项目手册 |
| `docs/开发手册.md` | 🎨 设计哲学总纲（设计者手册） |
| `docs/设计师入门指南.md` | 👶 设计师 Onboarding（2.5h 上手 + 设计稿模板）|
| `docs/执行者入门指南.md` | 🔨 执行者 Onboarding（2h 上手 + 回报模板）|
| `docs/审批员入门指南.md` | 🔍 审批员 Onboarding（1.5h 上手 + 标级模板）|
| `docs/API文档.md` | 🔌 接口定义 |
| `docs/部署文档.md` | 🚀 部署指南（Nginx + systemd + SSL） |
| `docs/故障排查.md` | 🛠️ 故障排查手册 |
| `backend/main.py` | FastAPI 入口，分片缓存 + SSE推送 |
| `backend/fetcher/` | 数据获取模块（每模块独立文件，详见模块清单；V2.0.0+ 含 chanlun/fundamentals/backtest/scorer/ai_analyzer） |
| `backend/requirements.txt` | Python 依赖 |
| `frontend/index.html` | 前端入口 | 纯HTML骨架，加载CSS/JS模块 |
| `frontend/css/main.css` | 样式 | 暗色主题，响应式 |
| `frontend/js/core.js` | 核心引擎 | 状态管理/渲染/SSE/模块切换 |
| `frontend/js/modules/*.js` | 9模块 | 每模块独立注册 |
| `chanlun/` | 参考资料（只读） |
| `.trae/skills/` | ⭐ 4 个 AI Skill（designer/executor/reviewer/validator），按角色触发节省 token |

## 模块清单

| # | 模块 | 数据源（优先级从左到右） | 数量 | 状态 |
|---|------|------------------------|------|------|
| 1 | 🪙 加密货币 | Binance API（需代理，服务器无代理时显示未检测） | 全量实时 | ✅ |
| 2 | 📈 A股 | 东方财富 push2 JSON（V2.2.0，5534只 4线程并发 ~6s）| 全量实时 | ✅ |
| 3 | 📊 ETF | 东方财富 push2 JSON（V2.2.0，1663只 4线程并发 ~2s）| 全量实时 | ✅ |
| 4 | 🌏 港股 | 腾讯 → 东财 stock_hk_spot_em → 新浪 stock_hk_spot | 全量实时 | ✅ |
| 5 | 🇺🇸 美股 | 腾讯 qt.gtimg.cn（V2.1.0 切回，白名单 164 只 4 分类）→ AkShare stock_us_spot_em fallback | 164 只（中概股/全球龙头/中概ETF/港股ADR）| ✅ |
| 6 | 📉 指数 | 东财/AkShare（全球指数 index_us_stock_sina）→ 新浪（global需海外网络，限流时为空） | 全量实时 | ✅ |
| 7 | 📈 K线 | 6 模块全支持 + ECharts 三联图 + 分时图 + K线 SSE 5s 实时推送（V1.7.0 Step 1+2 ✅ / Step 3 ✅ / Step 4 ✅ / Step 4.5 ✅ / Step 5 ✅） | 全量实时 | ✅ |
| 8 | 📰 新闻 | 新浪财经 HTTP（主源）→ 财新头条（fallback）（V1.8.0，60s 刷新，卡片流渲染） | 全量实时 | ✅ |
| 9 | 🤖 智能预测 | 缠论+回测+10因子+基本面+AI（V2.0.0，按需即时+批量排行） | 全量实时 | ✅ |

## 数据源详解

### A股：东方财富 push2 JSON（V2.2.0，5534只 4线程并发 ~6s）
- 批量查询：50 只/请求，自动分批拉取全量
- 字段：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、最高、最低、今开、昨收、**振幅、换手率、量比**
- 自动回退：东财 → 新浪

### 港股：腾讯 → 东财 → 新浪（V1.8.5 加速）
- 腾讯为主源（50 只/请求，6 线程并发，< 15s）
- 代码列表 24h 内存缓存
- 东财 AkShare `stock_hk_spot_em` 冷启动 ~2 分钟
- 新浪 `stock_hk_spot` 兜底
- 多源 fallback 解决 RemoteDisconnected 导致 0 行

### 加密货币：Binance API
- 端点：`api.binance.com/api/v3/ticker/24hr`
- 自动扫描代理端口：7897/7890/10809/10808/1080/8118/8888
- 用户也可手动设置 `CRYPTO_PROXY` 环境变量
- 每次点击重新检测代理连通性

### 新闻：新浪财经 HTTP + 财新头条 fallback（V1.8.0）
- 新浪财经 HTTP（主源）拉取实时财经新闻，财新头条作为 fallback
- 返回 datetime（发布时间）+ content（内容）+ source（实际媒体来源名称，如"环球市场播报"；财新源为"财新头条"）
- 60s 低频刷新防限流，异常返回空数组不崩主流程
- 前端卡片流渲染，时间倒序，搜索过滤
- SSE 全量替换（非 diff）：新闻无"代码"字段，`_connectSSE` 加 `renderMode==='news'` 分支全量替换，不影响其他 6 模块

### ETF/美股/指数（V2.1.0 更新）
- 所有模块均含数据源缓存，首次找到可用源后直接复用
- ETF：腾讯 qt.gtimg.cn（50 只/请求，6 线程并发）→ 东财 fund_etf_spot_em → 同花顺
- 美股：腾讯 qt.gtimg.cn 为主源（V2.1.0 切回，白名单 164 只全干净代码无 dot-suffix）→ AkShare fallback；4 分类筛选（中概股/全球龙头/中概ETF/港股ADR）；**3 分片/5s 滚动刷新**
- 指数：东财 index_global_spot_em → 新浪（global 字段需海外网络，限流时为空）

### K线（V1.7.0+ / V2.0.3 全球指数）
- A股/ETF/指数(A股)：腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`（日/周/月）+ `ifzq.gtimg.cn/appstock/app/kline/mkline`（分钟 1m/5m/15m/30m/60m，不带 web 前缀）
- 全球指数（dji/^IXIC/^GSPC）：AkShare `index_us_stock_sina`（V2.0.3，腾讯不支持纯字母指数代码）
- 港股：腾讯 `appstock/app/hfqkline/get`（hk 前缀）
- 美股：腾讯 `appstock/app/usfqkline/get`（us 前缀）
- 加密：Binance `/api/v3/klines`
- 8 周期：1m/5m/15m/30m/60m/1d/1w/1M
- 指标计算：纯 Python（MA5/10/20/60/120/250 + BOLL(20/2) + MACD(12/26/9)）
- 分钟K线注意：fqkline 不支持分钟周期（返回空），自动切换 mkline；mkline 不返回成交额（amount=0）
- **分时图**（V1.7.0 Step 4.5）：分钟周期（1m/5m）自动切分时折线图（价格线+昨收虚线+VOL柱）；"分时"按钮手动切换；昨收并行 fetch 日K倒数第二根 close，失败静默降级

## 前端架构
- **首页**：8 张卡片网格（3×3），V1.8.6 懒惰加载（逐个后台加载，首页立即可交互，卡片逐个从 ⏳→✅）
- **首屏快照**（V1.8.6）：后端并行预加载完成后写 `frontend/snapshot.json`，二次访问零 HTTP 渲染，SSE 连上后自动切实时
- **模块就绪信号**（V1.8.6）：`/api/health` 返回每模块缓存状态，前端每 5s 轮询，已就绪卡片明亮(opacity=1)，未就绪半透明(0.5)
- **数据视图**：表格 + 搜索 + 排序 + 翻页（50条/页）
- **K线视图**（V1.7.0）：独立行情页（顶部导航"行情"入口） + ECharts 三联图（主+VOL+MACD）+ 分时图（价格折线+昨收虚线+VOL柱） + 8周期切换 + 搜索（spot数据索引+6模块跨搜）+ ECharts 原生图例点击显隐 MA/BOLL
- **K线服务端缓存**（V1.8.6）：`_kline_cache` TTL 5min，同股票同周期二次请求 < 50ms
- **实时推送**：SSE (`/api/stream/{module}`) + 分片滚动刷新，单元格 diff 闪动
- **SSE 多客户端广播**（V1.8.5）：每连接独立 Queue，roller/heartbeat 广播到所有连接，多标签页同模块均收到数据
- **心跳机制**（V1.6.0.6）：后端每 3s 推 `shard=-1` 空数据，前端刷新 `fetchTime` 维持绿点
- **客户端缓存**：sessionStorage（前端状态恢复，**非实时数据源**，TTL 15s）
- **模块隔离**：ST 对象独立存储每模块的 rows/cols/page/sort/search，互不干扰
- **时间显示三件套**：globalStamp（UI 时钟，每秒跳）+ viewTime（客户端实时时间，V1.6.0.8 回滚到 V1.6.0.3 行为，每秒跳）+ liveStatus（数据新鲜度，SSE 推时"实时"绿点，断连时"离线"红点）

## 🔴 铁律

| # | 铁律 |
|---|------|
| 1 | 核心文件不变，不许随意加文件 |
| 2 | 先改 CLAUDE.md 再写代码 |
| 3 | 服务端缓存允许，数据源必须公开 API |
| 4 | 数据源仅限免费公开 API |
| 5 | 做完记录版本历史 |
| 6 | 每个模块完全独立封装 |
| 7 | **每次新需求必须同步更新 [设计师入门指南 §0](./docs/设计师入门指南.md) 的同步更新规则** |
| 8 | **设计师：改完代码必须审批执行者改的技术文档（见 [设计师入门指南 §7.1](./docs/设计师入门指南.md) 4 检查点）** |

## 模块加载速度（V1.8.5/V1.8.6 实测 2026-06-28）

| 模块 | 首启 | 稳态滚动 | 数据量 | 数据源 |
|------|------|----------|--------|--------|
| 🪙 加密货币 | 0.5s（需代理） | — | 0（无代理） | Binance |
| 📈 A股 | <6s（并发） | 5s diff 闪动 + 3s 心跳 | 5534 条 | 东方财富 push2 JSON |
| 📊 ETF | **< 2s**（腾讯并发） | 3s diff 闪动 + 3s 心跳 | 1516 条 | 腾讯 qt.gtimg.cn |
| 🌏 港股 | **< 30s 首次 / < 15s 后续** | 3s diff 闪动 + 3s 心跳 | 2773 条 | 腾讯 qt.gtimg.cn（并行）|
| 🇺🇸 美股 | **< 3s**（V2.1.0 腾讯 3 批）| 3s diff 闪动 + 3s 心跳 | 164 只（4 分类） | 腾讯 qt.gtimg.cn |
| 📉 指数 | <1s | 3s diff 闪动 + 3s 心跳 | 562 条 | 新浪 index_spot_sina |
| 📈 K线（V1.7.0） | **< 1s 首次 / < 50ms 缓存命中**（V1.8.6） | 5s 推最新 K线 | 750 根（日K） | 腾讯 K线 + Binance klines |
| 📰 新闻（V1.8.0） | ~2s | 60s 推增量 | ~50 条 | 新浪财经 HTTP + 财新头条 fallback |

> V1.6.0 起：分片缓存 + SSE 实时推送，浏览器侧看到的是**持续跳动**的实时行情，不再是 10s 静默刷新。
> V1.6.0.6 起：每 3s 心跳维持客户端 liveStatus 绿点（即使数据静止也不变红）。
> V1.8.5 起：US 代码列表磁盘缓存 `.cache/us_codes.json`，重启 30s 恢复（原 8min）。
> V1.8.5 起：HK/ETF 改用腾讯 qt.gtimg.cn 50 只/请求线程池并发（HK 2min→15s，ETF 5s→1s）。
> V1.8.5 起：启动并行预加载（6 线程），最快 10s 可访问新闻/指数/ETF。
> V1.8.6 起：首页懒惰加载 + 首屏快照，二次访问零等待渲染。

## 审计流程

每次重大修改后，按以下步骤自检：

### 1. 文档检查
- [ ] CLAUDE.md 模块清单是否反映最新状态
- [ ] 文档中是否有硬编码的数量/限制（应标注"全量实时"）
- [ ] 版本历史是否更新

### 2. 数据源检查
- [ ] 逐模块调用 API，确认返回数据量 > 0
- [ ] 关键列（代码、名称、最新价、涨跌幅）是否有值
- [ ] A股特有列（振幅、换手率、量比）是否非空
- [ ] 数据源自动切换逻辑是否生效（检查服务日志）

### 3. 实时性检查
- [ ] SSE 推送是否在 3~5s 内更新（按模块分片周期）
- [ ] **3s 心跳**（V1.6.0.6）是否持续收到 `shard:-1` 数据
- [ ] 数据时间戳是否在最近交易时段内
- [ ] 非交易时段数据是否为最近交易日收盘数据
- [ ] 浏览器开发者工具 Network → EventStream 是否持续收到 `data:` 行
- [ ] **viewTime 每秒跳**（V1.6.0.8 客户端实时时间，与 SSE 解耦）
- [ ] **viewTime 在 openModule 切模块瞬间不显示数据时间**（V1.6.0.16 删 openModule 内的 viewTime=fetchTime 赋值）
- [ ] **liveStatus 由 fetchTime 算 ago**（心跳维持绿点，>15s 显式"离线"红点，V1.6.0.8）

### 3.5 新闻专项检查（V1.8.0+）
- [ ] `/api/news/spot` data 数组非空，datetime/content/source 字段完整
- [ ] `/api/stream/news` SSE 连接正常（60s 间隔推送 + 3s 心跳）
- [ ] 卡片流渲染正常（时间倒序、搜索过滤）
- [ ] 新闻面板与表格面板 DOM 不串台
- [ ] 60s 内新新闻自动出现（SSE 全量替换，非 diff）
- [ ] SSE 全量替换分支守卫 `renderMode==='news'` 仅命中新闻模块

### 3.6 K线专项检查（V1.7.0+）
- [ ] 6 模块各跑一次 `/api/kline/{m}/{code}`，data 数组非空
- [ ] 8 周期切换都正常返回（1m/5m/15m/30m/60m/1d/1w/1M）
- [ ] MA/BOLL/MACD 指标计算结果正确（对账测试）
- [ ] ECharts 三联图渲染正常（主图 + VOL + MACD）
- [ ] **分时图**（V1.7.0 Step 4.5）：1m/5m 周期自动切分时折线图，昨收虚线可见，VOL 柱正常
- [ ] 分时按钮手动切换正常，切回 K线日K 正常
- [ ] 搜索功能：6 模块跨搜 + 回车选第一个 + 点击选中
- [ ] ECharts 图例点击显隐 MA/BOLL 各线正常
- [ ] 表格双击 → K线跳转正确（代码+名称）
- [ ] K线 SSE 5s 推最新一根，ECharts 实时更新最后一根

### 3.7 智能预测专项检查（V2.0.0+）
- [ ] `/api/predict/analyze/stock/sh600519` 返回 chanlun/buy_points/sell_points 非空
- [ ] 10 因子输出完整（Q1 动量~Q10 北向关联 + quant_score）
- [ ] `/api/predict/analyze/stock/sh600519?with_ai=true` 返回 ai.analysis_text 非空
- [ ] AI source 字段: pollinations→正常, zhipu→fallback, local→降级
- [ ] 回测 9 指标输出（胜率/盈亏比/夏普/最大回撤/连亏/盈利因子/持有天数/样本量）
- [ ] 历史相似场景 3 条含 result_30d
- [ ] 多周期确认因子在 0.7~1.3 之间
- [ ] 百分位排名 pct_total/pct_chanlun 在 0~100
- [ ] POST `/api/predict/batch/stock` → GET `/api/predict/rank/stock` 返回排序数据
- [ ] `/api/stream/predict/stock` SSE 推送正常
- [ ] K线图 markPoint（买卖点箭头）+ markArea（中枢矩形）可见
- [ ] 预测面板三 Tab 正常切换
- [ ] 非A股模块基本面返回 available:false 不崩

### 4. 模块隔离检查
- [ ] 切换模块后数据是否独立，不串台
- [ ] 搜索/排序/翻页是否每个模块独立
- [ ] `ST` 对象是否正确保存和恢复每个模块状态

### 5. 代码规范检查
- [ ] `backend/` 下是否有本地文件读写（搜 `open(` `write(` `dump(`）
- [ ] 是否有硬编码数据列表或数量限制
- [ ] 数据源是否全部来自免费公开 API
- [ ] Python 导入正常、JS 语法正常

```bash
# 快速验证命令
cd backend && python -c "from main import app; import fetcher; print('OK')"
curl -s http://localhost:8000/api/etf/spot | python -c "import sys,json; print(len(json.load(sys.stdin)['data']),'ETF')"
curl -s http://localhost:8000/api/news/spot | python -c "import sys,json; print(len(json.load(sys.stdin)['data']),'新闻')"
```

## 如何运行

```bash
cd backend
pip install -r requirements.txt

# V1.6.0 起必须用 --workers 1（不要用 4）
# 原因：SSE 长连接 + 免费 API 限流，4 worker 会导致：
#   1. SSE 路由只在 1/4 worker 上生效，连接被路由到其他 worker 会立即断
#   2. 4 倍数据源拉取，免费 API 容易被封
#   3. 单进程足够支撑 6 模块 6 万+条数据并发
uvicorn main:app --workers 1
# 浏览器打开 frontend/index.html
```

## ⭐ AI Skill（节省 token）

4 个 Skill 按角色触发，加载极简 description（~200 字符），按需 Read 文档。**Token 节省 60%~70%**。

| Skill | 触发场景 | 作用 |
|-------|----------|------|
| `mv-designer` | "出设计"/"审批代码"/"我是设计师" | 出设计稿 + 维护 CLAUDE.md + 审批执行者 |
| `mv-executor` | "我是执行者"/"实施"/"改代码" | 写代码 + 跑验收 + 同步技术文档 + 回报 |
| `mv-reviewer` | "我是审批员"/"复审" | 复审 + 标 P0/P1/P2 + 出改进意见 |
| `mv-validator` | "跑验收"/"验证模块" | 自动化验收（数据量/SSE/铁律/K线）|

**验收脚本**（免 AI 介入）：
```bash
python .trae/skills/mv-validator/scripts/mv_validate.py all      # 全部
python .trae/skills/mv-validator/scripts/mv_validate.py sse      # SSE 心跳
python .trae/skills/mv-validator/scripts/mv_validate.py kline    # K线接口（V1.7.0+）
python .trae/skills/mv-validator/scripts/mv_validate.py rules    # 铁律自检
```

> 详见 [.trae/skills/](./.trae/skills/) 目录。

## 已完成清单（按版本）

### V1.6.0.6 收尾清理（2026-06-26）

| 类型 | 位置 | 处理 |
|------|------|------|
| 死代码删除 | `backend/main.py:37` | `_heartbeat_threads = {}` 未被读/写，daemon 线程无需追踪 → ✅ 删除 |
| try/except 确认 | `backend/main.py:117-121` | 心跳启动有 try/except + print FAIL 日志 → ✅ 无需改 |
| 心跳分支位置 | `frontend/js/core.js:217-221` | 已位于 onmessage 最顶部 → ✅ 无需改 |

### V1.6.0.1 实施记录（已记录）

#### A. 垃圾文件（12 个，已删除 ✅）

| 文件 | 说明 |
|------|------|
| `nul` | PowerShell `curl -o NUL` 误创建的空文件 |
| `t.json` (1.3MB) | A股测试输出 |
| `te.json` `th.json` `ti.json` `ts.json` `tu.json` | ETF/港股/指数/A股/美股 测试输出 |
| `etf_test.json` `stock_test.json` | 测试输出 |
| `A股模块API测试报告.md` `ETF模块API测试报告.md` | 测试报告（速度已记入版本历史） |
| `oldcat-realtime-upgrade.html` | 旧实时化方案展示页（Trae 生成，已被 V1.6.0 设计取代） |
| `docs/V1.6.0-续做设计.md` | V1.6.0 设计稿（封版后删除，2026-06-26） |

#### B. 代码冗余（V1.6.0.1 清理 ✅）

| 位置 | 问题 | 处理 |
|------|------|------|
| `backend/main.py:21` | `_cached_get(key, fetcher_fn)` 的 `fetcher_fn` 参数从未被调用 | ✅ 删参数 |
| `backend/main.py:62` | `NO_CACHE = {}` 空字典当 headers 传等于没传，命名误导 | ✅ 删变量 |
| `backend/fetcher/crypto.py:8-15` | `detect()` 与 `status()` 功能重叠，仅 print 不设 `_found_proxy` | ✅ 合并进 `status()` |
| `frontend/js/core.js:51` | `let totalModules` 定义后从未使用（preloadAll 用 `totalMods`） | ✅ 删死变量 |

#### C. 文档同步（V1.6.0.1 + 2026-06-26 大更新 ✅）

| 文件 | 时机 | 状态 |
|------|------|------|
| `docs/API文档.md` | V1.6.0.1 + 2026-06-26 (V1.6.0.6/V1.7.0) | ✅ 已更新 7 处 |
| `CLAUDE.md` | 2026-06-26 全量更新 | ✅ 已更新 7 处 |
| `docs/开发手册.md` | 2026-06-26 新建 | ✅ 设计哲学沉淀 |
| `docs/设计师入门指南.md` | 2026-06-26 新建 | ✅ Onboarding 2.5h + 模板 |
| `docs/执行者入门指南.md` | 2026-06-26 新建 | ✅ Onboarding 2h + 回报模板 |
| `docs/审批员入门指南.md` | 2026-06-26 新建 | ✅ Onboarding 1.5h + 标级模板 |
| `docs/{设计师,执行者,审批员}入门指南.md` | 2026-06-26 加 §0.1 分工表 | ✅ 技术文档执行者改 / 设计文档设计师改 |

### V1.6.0.2~V1.6.0.5 viewTime 系列修复（已封版）

| 版本 | 关键改动 |
|------|----------|
| V1.6.0.2 | viewTime 挪出 `if(changed)` 块（方案 C 错误 + 方案 A 撤销） |
| V1.6.0.3 | viewTime 改由 `setInterval(refreshStamp,1000)` 驱动（与 SSE 解耦）|
| V1.6.0.4 | viewTime 更新从 `if (s && s.fetchTime)` 块内挪出（切模块卡死修复）|
| V1.6.0.5 | 3 处 ST 重建补 `fetchTime`（doSort/openModule/goPage，灯变红修复）|

## 版本历史

| 版本 | 日期 | 做了什么 |
|------|------|----------|
| V1.0.0 | 2026-06-24 | 项目立项 |
| V1.1.0 | 2026-06-24 | 模块一~六完成 |
| V1.2.0 | 2026-06-24 | 预加载缓存 + 模块隔离 + 分页 |
| V1.3.0 | 2026-06-25 | 腾讯数据源 + 振幅换手率量比 + 代理自动扫描 + 首页重构 |
| V1.4.0 | 2026-06-25 | 部署服务器(HTTPS+nginx+systemd) + 动态API + 刷新缓存优化 + 手机端适配 + 实时状态 |
| V1.4.1 | 2026-06-25 | 修复: fetchTime/0条误判/源缓存；A股强制腾讯源 |
| V1.4.2 | 2026-06-25 | 并行加载(Promise.all)+4worker；加载速度3倍提升 |
| V1.4.3 | 2026-06-25 | 视觉反馈+连接状态+SSL优化 |
| V1.5.0 | 2026-06-25 | 模块拆分: 7独立JS+核心引擎+CSS独立 |
| V1.5.1 | 2026-06-25 | 统一网格容器 |
| V1.6.0 | 2026-06-25 | **P0全部解除**：SSE推送+分片缓存+滚动刷新+diff闪动；美股腾讯源(us前缀,17209条)；crypto代理诊断；指数global限流说明 |
| V1.6.0.1 | 2026-06-25 | **回归修复**：预热键匹配_shards_→首次启动即生效；HK roller多源fallback→2773条恢复；index_{china,global}_结构保留；启动不再阻塞_crypto_status_fire-and-forget；except:pass全部改日志；API文档同步 |
| V1.6.0.2 | 2026-06-25 | **viewTime 第一版**（方案 C 错误 + 方案 A 撤销）：viewTime 挪出 if(changed) — 实际无效，因后端不推空分片 |
| V1.6.0.3 | 2026-06-25 | **viewTime 真正修复**：viewTime 改由 setInterval(refreshStamp,1000) 驱动（客户端时间），与 SSE 推送完全解耦。设计修正：viewTime=UI时钟（每秒跳），liveStatus=数据新鲜度（SSE推时"实时"绿点，无推时"Xs 前"） |
| V1.6.0.4 | 2026-06-26 | **viewTime 切模块卡死修复**：refreshStamp 的 viewTime 更新从 `if (s && s.fetchTime)` 块内挪出，确保即使 ST[tab] 状态异常也每 1s 跳一次。 |
| V1.6.0.5 | 2026-06-26 | **3 处 ST 重建补 fetchTime**：doSort/openModule/goPage 重建 ST[tab] 时都漏了 fetchTime，导致 liveStatus 变红(--)。3 处都加 `fetchTime: ST[tab]?.fetchTime || Date.now()` |
| V1.6.0.6 | 2026-06-26 | **A+D 心跳推送 + viewTime 数据驱动**：后端 A(所有分片 interval 内必推) + D(每 3s 心跳推 `shard=-1`)；前端 viewTime 只在真实数据推送时更新（稳定显示数据时间）、liveStatus 由 fetchTime 算 ago（心跳维持绿点），两指标解耦。解决"19秒前"红点 + 避免"绿点闪但时间不动"的错觉 |
| V1.6.0.7 | 2026-06-26 | **文档优化 10 项**：① 三份协作流程图统一为 10 步（设计师/执行者/审批员口径一致）② 加 V1.7.0 5 步分开发审批策略（Step 1~4 轻量验收 + Step 5 完整复审）③ 审批员 §6.2 加 K线专项实测（V1.7.0+）④ 审批员 §3 必读清单加部署文档 ⑤ 铁律数字 6+1=7 改为 6+2=8 ⑥ 加"标级=标 P0/P1/P2"术语对齐说明 ⑦ 复审不通过的责任划分表 ⑧ 失败回滚流程（git revert）⑨ CLAUDE.md 项目概览加"角色"行 ⑩ 复审时效 24h |
| V1.6.0.8 | 2026-06-26 | **viewTime 回滚实时时间 + SSE 断连显式"离线"**：回滚 V1.6.0.6 的 viewTime=数据时间设计（用户反馈"01:55:33+134秒前"看不懂），改回 V1.6.0.3 行为（客户端实时时间，每秒跳），与 SSE 推送完全解耦。SSE onerror 显式显示"离线"（红点 + 离线）替代"X秒前"，避免歧义。viewTime 与 liveStatus 仍解耦：viewTime=实时时钟（每秒跳），liveStatus=数据新鲜度（SSE 推时"实时"绿点，断连时"离线"红点）。两步协作：前端只改 core.js 的 refreshStamp + onerror 逻辑 + CLAUDE.md §7 文档同步 |
| V1.6.0.9 | 2026-06-26 | **AI Skill 化 + 验收脚本化**：解决 4 份入门指南（60% 内容重叠）每次 Read 消耗大量 token 的问题。新建 `.trae/skills/` 目录含 4 个 Skill：① `mv-designer`（出设计/审批/维护 CLAUDE.md）② `mv-executor`（写代码/跑验收/同步技术文档/回报）③ `mv-reviewer`（复审/标 P0P1P2/改进意见）④ `mv-validator`（自动化验收）。每个 Skill description 极简（< 200 字符），按需 Read 文档。验收脚本 `mv_validate.py` 覆盖 4 类检查：6 模块数据量 + 6 模块 SSE 心跳（6s 窗口）+ V1.7.0+ K线接口（6 模块 MA/BOLL/MACD）+ 铁律自检（无本地存储/无收费 API/核心文件 diff）。原 4 份文档保留不动。**Token 节省 60%~70%** |
| V1.6.0.10 | 2026-06-26 | **Skill 同步机制**：让 Skill 像本地文档一样"做一步更新一步"。① [开发手册 §十二](./docs/开发手册.md) 加第 8 步"⭐ 同步 `.trae/skills/` Skill" ② [设计师入门指南 §0.2](./docs/设计师入门指南.md) 加"Skill 同步三问"（角色职责变？必读必背变？验收工具变？满足任一即同步）③ [设计师指南 §0.1 分工表](./docs/设计师入门指南.md) 加 2 行（Skill.md / mv_validate.py 责任人 = 设计师）④ 同步规则：改代码 1 行 / 临时调试 / 字段顺序调整 → Skill 不动（只动"导航变化"） |
| V1.6.0.11 | 2026-06-26 | **全面文档同步 13 项**：① 删意外文件 `docs/V1.6.0.8+...-实施指令.md`（Trae 自动保存副本，违反铁律 1）② README.md 版本号 V1.6.0.6→V1.6.0.10 + 加 Skill 章节 ③ CLAUDE.md §3 实时性检查 + L93 时间三件套描述对齐 V1.6.0.8 设计 ④ [开发手册 §七](./docs/开发手册.md) viewTime 表改为"V1.6.0.8 回滚"+ "SSE 断连显式离线" ⑤ [开发手册 §九](./docs/开发手册.md) UI 原则 viewTime 描述同步 ⑥ 4 份入门指南铁律"6 条"→"8 条"（7 处分散）⑦ 4 份 Skill 必背"6 条铁律"→"8 条铁律"+ 加"协作流程 10 步" ⑧ 4 份 Skill 必读清单补 API 文档/故障排查 ⑨ mv-validator SKILL.md 补必背 + 触发 + 修错误命令 stock→modules ⑩ [故障排查 §10](./docs/故障排查.md) viewTime 设计描述对齐 V1.6.0.8 |
| V1.6.0.12 | 2026-06-26 | **二轮文档/Skill 同步 8 项**（自查自纠）：① README.md 版本号 V1.6.0.10→V1.6.0.11 ② [mv-executor SKILL.md](./.trae/skills/mv-executor/SKILL.md) 必背补"8 条铁律 + 协作 10 步" ③ [mv-reviewer SKILL.md](./.trae/skills/mv-reviewer/SKILL.md) 必背补"8 条铁律 + 协作 10 步" ④ 3 份入门指南项目状态 V1.6.0.6→V1.6.0.11 ⑤ [执行者入门指南 §4 铁律表](./docs/执行者入门指南.md) 补齐 7+8 两条 + 描述"6 条"→"8 条" ⑥ 3 份指南常见问题速查表 §1-§9 编号→§1.1-§5.x 精确定位 ⑦ 3 份指南版本记录补 1.1 行（V1.6.0.7 铁律升级 + V1.6.0.11 同步） ⑧ [审批员入门指南 §2 §二 铁律](./docs/审批员入门指南.md) 描述简化"项目 6 条 + 补充 2 条"→"8 条" |
| V1.6.0.13 | 2026-06-26 | **V1.6.0.8 实际落地封版**（2b2df26）：viewTime 回滚客户端实时时钟（core.js:288-291 refreshStamp 末尾 +3 行）+ SSE 断连显式"离线"（core.js:266-271 onerror + core.js:285 refreshStamp else 分支）。4 检查点全过：① viewTime 字段格式与设计一致 ② [故障排查 L389](./docs/故障排查.md) + [开发手册 L287](./docs/开发手册.md) 描述已对齐 ③ "离线"双保险触发（onerror + refreshStamp）+ 5s 自动重连 ④ git diff 16 行仅 core.js 无越界 |
| V1.6.0.14 | 2026-06-26 | **viewTime 移出 if(tab) 块**（5c688a4）：refreshStamp() 重构（core.js:276-294），viewTime 与 globalStamp 平级，**永远每秒跳**（首页/切模块瞬间/后台标签 3 场景全覆盖）。liveStatus 仍受 if(tab) 保护（首页不显示符合预期）。[故障排查 §1.3](./docs/故障排查.md#L73) 补第 3 条根因"V1.6.0.13 之前 viewTime 嵌套在 if(tab)"。6 项验收全过：① 首页 viewTime 跳秒（关键）② 切模块不停 ③ 后台标签切回立即跳 ④ liveStatus 仍正常 ⑤ git diff 仅 refreshStamp + 注释 ⑥ 范围仅 2 文件 |
| V1.6.0.15 | 2026-06-26 | **mv_validate Windows GBK 编码修复**（5350dee）：[mv_validate.py:24-28](./.trae/skills/mv-validator/scripts/mv_validate.py#L24-L28) 加 4 行 `sys.stdout/stderr.reconfigure(encoding='utf-8', errors='replace')`（hasattr 守卫兼容 Linux/旧 Python），emoji（✅/⚠️/❌）在 Windows PowerShell 5 终端正常输出。[故障排查 §7](./docs/故障排查.md#L401) 表格 +1 行"验收脚本崩溃"案例。SKILL.md 核对不需紧急修订（脚本自动 fix）。4 项验收全过：① py_compile ② PowerShell 5 跑 kline 不崩（关键） ③ all 4/4 全过 ④ hasattr 守卫无副作用。**附带遗留 P2**：subprocess capture_output pipe 层 GBK 解码警告，不影响验收结果输出，V1.6.0.16 计划 |
| V1.6.0.16 | 2026-06-26 | **openModule 移除 viewTime 数据时间赋值**（35c2bf7）：[core.js:113-116](./frontend/js/core.js#L113-L116) 删 3 行 `vtEl.textContent = '更新 ' + new Date(ST[m].fetchTime).toLocaleTimeString()`，改为 2 行 `if (ST[m]) ST[m].fetchTime = Date.now()` 维持 liveStatus 绿点。[故障排查 §1.3](./docs/故障排查.md#L76) 补第 4 条根因"V1.6.0.15 之前 openModule 设 viewTime=数据时间"。[CLAUDE.md §3 实时性检查](./CLAUDE.md#L147) 补 1 行"viewTime 在 openModule 切模块瞬间不显示数据时间"。**viewTime 现在所有场景都显示客户端实时时间**：① 首页（V1.6.0.14 移出 if(tab)）② 切模块瞬间（V1.6.0.16 删 fetchTime 赋值）③ 数据静止（refreshStamp 永远每秒跳）④ liveStatus 仍正常（切模块即刷 fetchTime）。5 项验收全过：node -c / git diff -3+2 / 切模块=客户端时间 / 红点+老数据已消除 / mv_validate rules 3/3 |
| V1.6.0.17 | 2026-06-26 | **V1.6.0.11~V1.6.0.16 文档同步 catch-up**（0e3a7ae）：11 文件（4 SKILL.md + CLAUDE.md + README.md + 5 docs）铁律 6→8 全文档对齐 + 4 份 Skill 必背补全 + 交叉引用 §x.y 精确化 + viewTime 三件套描述升级 + 项目状态更新。修复 API 文档 L271 data 列序 `l,h`→`h,l` 与实际后端对齐 |
| V1.7.0 | 2026-06-26 | ✅ **K线图**（P2 体验优化）：**Step 1 ✅**（后端 kline.py+indicators.py+路由，2f1494e，6 模块 + MA/BOLL/MACD 指标 + MA5 对账 manual=1267.536=API）；**Step 2 ✅**（港股 K线 3 源 fallback tencent→eastmoney→sina + API 文档 §9 K线字段表补 4 处 + 故障排查 §5.6.1 港股 K线 0 行案例，8043d69，4 检查点全过）；**Step 3 ✅**（K线前端骨架 ECharts 接入 — index.html + main.css + kline.js，导航栏+容器+三联图+MA/BOLL/MACD+8周期+显隐矩阵+dispose重建策略，验收 5/5 K线接口全过）；**Step 4 ✅ 分钟K线数据源修复**（`_fetch_tencent_minute` — 换用 `ifzq.gtimg.cn` mkline 接口 [HTTPS 无 web 前缀]，解析路径 `data[code][m5]` 6 列格式，datetime YYYYMMDDHHmm→标准格式，amount 填 0；`_fetch_tencent` 加点判断自动分流分钟→mkline）；**Step 4.5 ✅ 分时图 + K线美化**（a296607~1c54de3，20 commits，UA 测试 8/8 全过，见下）；**Step 5 ✅ K线 SSE 5s 实时推送**（44040f5，见下）。独立行情页（顶部导航"行情"入口）+ ECharts 三联图（主+VOL+MACD）+ 分时图（价格折线+昨收虚线+VOL柱）+ 8周期切换 + 搜索（spot数据索引+6模块跨搜）+ ECharts 原生图例点击显隐 MA/BOLL。VOL 副图必开、MACD 默认关。指标纯 Python 计算（不引 pandas）。**附带发现 P1**：验收脚本 mv_validate.py 在 Windows GBK 终端 emoji 编码崩溃（V1.6.0.15 ✅ 已修） |
| V1.8.0 | 2026-06-27 | **新闻模块**（模块 8 🚧→✅）：新增 `backend/fetcher/news.py`（新浪财经 HTTP 主源 + 财新头条 fallback，60s 刷新），`frontend/js/modules/news.js` 从 placeholder 改为真实模块（卡片流渲染），`core.js` 5 处适配（render 分支 / openModule 互斥 / preloadAll 去 skip / doFilter 分支 / SSE 全量替换 `renderMode==='news'`），`main.py` 加 `/api/news/spot` REST + `/api/stream/news` SSE，`main.css` 加新闻卡片样式，`index.html` 加 `#newsPanel` 容器。9 文件 +144/-16。铁律全合规。设计稿修订：原 AKShare `js_news` → 金十数据方案已失效（函数移除），改为新浪财经+财新头条。待审批员 Step 5 完整复审 |
| V1.8.5 | 2026-06-28 | **9 项性能+稳定性修复**（6 文件 / ~145 行）：**性能 5 项** — ① 美股代码列表磁盘缓存 `.cache/us_codes.json`（8min→30s 重启）② 港股腾讯并行路径 50 只/请求 6 线程（2min→15s）③ ETF 代码缓存 + 腾讯并行（5s→1s）④ K线 `httpx.Client` 连接复用（省 TLS 握手 200-500ms）⑤ 启动并行预加载 `ThreadPoolExecutor(max_workers=6)`（串行→并行，最快 10s 可访问）。**P0 修复 4 项** — ⑥ SSE 多客户端广播（`_sse_queues` 从单 Queue 改为 per-client list，多标签页同模块均收到数据）⑦ flash 动画先 `render()` 重建 DOM 再对 新 DOM 加 class（修复 SSE diff 后 flash 元素被销毁）⑧ `calc_ma` 单循环逐元素判断（修复数据<周期时数组长度不匹配）⑨ `_to_records` 字符串列 `fillna('')` 不用 0（修复 NaN→整數 0 显示错误，兼容 pandas 3.0 StringDtype） |
| V1.8.6 | 2026-06-28 | **5 项前端秒开 + 体验优化**（5 文件 / ~85 行）：**A** 前端懒惰加载 — `preloadAll()` 从 `Promise.all` 并行阻塞改为 for 循环逐个后台加载，首页立即可交互，卡片逐个 ⏳→✅。**B** K线服务端缓存 — `_kline_cache` TTL 5min，同股票同周期二次请求 < 50ms。**C** 美股热股预拉 — 代码按成交量降序排序，分片 0 优先拉前 100 只热门股（~3s 即显示）。**D** 首屏快照 — 后端并行预加载完成后写 `frontend/snapshot.json`，前端 `fetch` 快照零 HTTP 渲染，无快照降级走原逻辑。**E** 模块就绪信号 — `/api/health` 返回每模块缓存状态，前端每 5s 轮询，已就绪卡片明亮(opacity=1)，未就绪半透明(0.5) |
| V1.9.0 | 2026-06-28 | **7 项 P0 修复**（前置应用，6 文件 / ~35 行）：① `kline.py` 分钟K线 `raw[-count:]` 取最新数据（原 `[:count]` 取最旧）② 加密日内K线 `fmt = '%Y-%m-%d %H:%M'` 含时分（原统一 `%Y-%m-%d` 丢时分）③ `utils.py` 先转时间列再 `fillna(0)` 数值列（原全局 `fillna(0)` 破坏 NaT）④ `__init__.py` 逐模块 `importlib.import_module` + try/except（原一行炸全炸）⑤ `core.js` `formatChinese` 删 `|| col.includes('涨跌')`（涨跌额误加 %）⑥ `kline.js` `_fmtClose()` 安全格式化昨收（`null.toFixed(2)` → TypeError 图表白屏）⑦ `requirements.txt` 补 `httpx>=0.27.0` |
| V2.0.0 | 2026-06-28 | **智能预测系统**（11 步 / ~2700 行 / 5 新文件）：Step 1a `chanlun.py` 缠论基础层（包含处理→分型→笔→一类买卖点，~290行），Step 1b `utils.py` `_fallback()`+`_shard()`，Step 2 `fundamentals.py` 5接口基本面（~240行），Step 3 `backtest.py` 9指标回测（~200行），Step 3.5 `chanlun.py` 进阶层（线段→中枢→走势→背驰→二三买卖点，+290行），Step 4 `scorer.py` 七维评分+10因子+百分位（~450行），Step 5 `ai_analyzer.py` Pollinations+智谱 fallback（~260行），Step 6 `main.py` 6 端点 API 集成，Step 7 `kline.js` markPoint/markArea + O6搜索缓存，Step 8 `predict.js` 第9模块+三Tab，Step 9 predict CSS+ deploy 脚本，Step 10 文档同步。**零新依赖** |
| V2.0.1 | 2026-06-28 | **智能预测加载加速 + MCP**（4 项 / ~60 行 / 4 文件 / 零新依赖 + mcp/marketview_mcp.py 8 tools）：A 启动预计算(_initial_load→6模块预测排名，60s就绪)，B K线走缓存(_kline_cache 迁utils.py，scorer共享复用)，C SSE即时推送(前端SSE替代3s轮询，含重连兜底)，D 精简蜡烛数(quick 200→100，2处改)。审批员3×P0+5×P1全修。 |
| V2.0.1-hotfix | 2026-06-28 | **热修复：stock/etf 代码前缀缺失**（~15 行 / 2 文件 / 零新依赖）。改动：`backend/main.py` — `_stock_prefix()` / `_CODE_PREFIX` / items 解包 + isinstance / crypto 跳过；`backend/fetcher/scorer.py` — K线缓存补 indicators。审批：设计师 + 审批员（GLM-5.2）双通过 ✅ 已封版。 |
| V2.0.2 | 2026-06-28 | **全模块磁盘持久化缓存**（7 文件 / ~200 行）：`backend/main.py` — `_load_cache()` / `_save_cache()` / `_predict_daemon` + `_predict_status` 持久化；`backend/fetcher/utils.py` — K 线磁盘缓存（首次拉永不重拉）+ 原子写入；`mcp/marketview_mcp.py` — `import asyncio` / 版本号 V2.0.2。审批：设计师 + 审批员（GLM-5.2）双通过 ✅ 已封版。 |
| V2.0.3 | 2026-06-28 | **3 个 P1 修复**（4 文件 / ~80 行）：**BUG8** 美股 — `us.py` 切 `ak.stock_us_spot_em()` + `threading.Lock` 全局缓存（解决腾讯 dot-suffix 不认 105.INLF 等代码导致 0 条）; **BUG10** predict daemon — 从 roller 内存缓存读代码列表，不调 akshare（解决 fetcher 与 11 个 roller shard 同时调 `stock_zh_a_spot()` 限速互抢）; **BUG11** 全球指数 K 线 — `kline.py` 新增 `_GLOBAL_INDEX_MAP` + `ak.index_us_stock_sina`（dji/^IXIC/^GSPC 腾讯不支持），前端 `inferCode` index 纯字母代码不加 sh 前缀。**已封版** |
| V2.2.0 | 2026-06-28 | **数据源分离**（3 模块 / ~200 行）：① stock.py 切东方财富 push2 JSON — 5534只/56页 4线程并发~6s（脱离腾讯，不再跟 hk/us 共抢 qt.gtimg.cn）② etf.py 切东方财富 push2 JSON — 1663只/17页 4线程并发~2s ③ index_mod.py 国内指数切东方财富 push2 JSON + 全球保持 AkShare ④ predict daemon 只预测 stock+etf（移除 index）⑤ main.py stock shard 11→8。**已封版** |
| V2.1.0 | 2026-06-28 | **美股秒级 + 分类筛选**（4 文件 / ~55 行）：① `us.py` 切腾讯 qt.gtimg.cn 为主源（白名单 164 只全干净代码，串行 3 批/< 3s）② 加分类字段 + `_US_CATEGORY` 字典（中概股/全球龙头/中概ETF/港股ADR）③ `main.py` US roller 从 11/600s→3/5s ④ 前端加分类下拉筛选器（`core.js` render 分支 + `index.html` select + `main.css` 样式 + `us.js` categoryFilter 配置）。**已封版** |

### V1.7.0 Step 4.5 UA 测试修复（2026-06-26~27，9 commits，8/8 全过）

| 版本 | 日期 | 做了什么 |
|------|------|----------|
| V1.6.0.18 | 2026-06-26 | 文档同步：CLAUDE.md/设计师入门指南更新 Step 4.5 状态 |
| V1.6.0.19 | 2026-06-26 | dblclick 名称传入改用共享变量 `MV._klineIncoming`（替代四层传参） |
| V1.6.0.20 | 2026-06-26 | 分时图标题用真实名称 `_currentDisplayName`（替代 API 硬编码默认名） |
| V1.6.0.21 | 2026-06-26 | `inferCode` 防双前缀：stock/etf/index/hk/us 四个模块加前缀前先检查已有前缀 |
| V1.6.0.22 | 2026-06-26 | `_lookupName` 从 spot 缓存查名称，消除所有传参变量（`_currentDisplayName`/`MV._klineIncoming`），core.js 删名称提取 |
| V1.6.0.23 | 2026-06-26 | K线后端排序修复：`_fetch_tencent` + `_fetch_tencent_minute` 比较首尾日期，降序则反转（替代盲目 reverse） |
| V1.6.0.24 | 2026-06-26 | `_lookupName` 加模糊匹配：数字部分 fallback（解决北交所前缀不匹配） |
| V1.6.0.25 | 2026-06-26 | 副图加 Y 轴标签：VOL 面板显示"VOL"，MACD 面板显示"MACD" |
| V1.6.0.26 | 2026-06-27 | 三联图/分时图左上+右上标注：graphic 左上角标注 + yAxis.name 右上标注 K线/VOL/MACD/价格 |

> **UA 测试结果**（2026-06-27，8 项全过）：A. dblclick 名称 ✅ B. 1m/5m→分时 ✅ C. ≥15m→K线 ✅ D. MACD 三联图+Y轴标注 ✅ E. 图例点击显隐MA/BOLL ✅ F. 首页↔行情切换 ✅ G. 缩放拖拽 ✅ H. 三图标注 ✅

### V1.7.0 Step 5 实施记录（2026-06-27，44040f5，已封版）

> **港股 2min 预热 fire-and-forget**：港股 AkShare 冷启动 ~2min，已在 [`main.py:124-150`](#) `_initial_load()` 中以 daemon 线程 fire-and-forget 执行（不阻塞启动）。Step 5 K线 SSE handler 的 `asyncio.to_thread(fetch_fn, ...)` 同样 fire-and-forget：每次循环的 fetch 在线程池中执行，不阻塞 asyncio event loop。两处均无阻塞风险。

#### 决策点

| 决策 | 选项 | 理由 |
|------|------|------|
| SSE vs 轮询 | **SSE** | 与 spot 模块 [`main.py:232-247`](#) SSE 架构一致 |
| 推送粒度 | **只推最新一根** | 每 5s ~100B vs 轮询 ~50KB |
| 后端架构 | **每连接独立轮询** | per-(code,period)，无需全局 queue + `_cache_lock` |
| 前端更新 | **setOption 无动画** | 避免 5s 闪一次 |
| 指标校准 | **每 30s（1m 周期 60s）全量 fetch** | SSE 只推蜡烛，MA/BOLL/MACD 定期重算；1m 周期 60s 防漏蜡烛 |

#### 改动清单（含文件:行号）

**A. `backend/main.py`** — 在 [`main.py:231`](#) 之后（`kline_endpoint` 结束，`# ── SSE 分片推送 ──` 之前）插入 K线 SSE 端点（~45 行）：

- `@app.get('/api/stream/kline/{module}/{code}')` + `stream_kline(module, code, period='1d')`
- `async gen()` 内部：`await asyncio.to_thread(fn, code, period, 5)` fire-and-forget 取最新 5 根 → hash 比较 → 推送 `{candle: [date,O,C,H,L,V,Amt], ts}` 或 `{heartbeat: true, ts}` → `await asyncio.sleep(5)` → loop
- `StreamingResponse` + header `Cache-Control: no-cache` + `X-Accel-Buffering: no`（与 spot SSE [`main.py:247`](#) 一致）

**B. `frontend/js/kline.js`** — 8 处改动：

| # | 位置 | 改动 |
|---|------|------|
| 1 | [`kline.js:54`](#) `_resizeHandler` 之后 | 加 3 变量：`_klineSSE`, `_klineSSERetry`, `_calibrateTimer` |
| 2 | [`kline.js:565`](#) `render(resp)` | 签名改为 `render(resp, noAnimation)`，`noAnimation` 时关动画 |
| 3 | [`kline.js:710`](#) `switchPeriod` 之后 | 新增 `_connectKlineSSE()` 函数（close 旧连接→new EventSource→onmessage 更新 lastResp→onerror 5s 重连） |
| 4 | [`kline.js:611`](#) `show()` 末尾 | 加 `_connectKlineSSE()` + 动态 `setInterval` 全量校准（1m→60s，其他→30s） |
| 5 | [`kline.js:614-621`](#) `_hide()` | 加 close SSE + clear 重连/校准定时器 |
| 6 | [`kline.js:709`](#) `switchPeriod()` 末尾 | 加 `_connectKlineSSE()` 重连（period 已变） |
| 7 | [`kline.js:820`](#) `selectCode()` 末尾 | 加 `_connectKlineSSE()` 重连（code 已变） |
| 8 | [`kline.js:635-638+675-684`](#) `toggleMinute()` | 切分时关 SSE + 校准；切回 K线重连 SSE |

**C. 技术文档**（执行者同步）：

- `docs/API文档.md` — 新增 §9.1 K线 SSE 端点字段表
- `docs/故障排查.md` — SSE 断连 / K线 SSE 返空 案例

#### 验收命令

```bash
# 后端：SSE 连接
curl -N -m 6 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | head -10
# 前端语法
node -c frontend/js/kline.js
```

#### 风险

| # | 风险 | 应对 |
|---|------|------|
| 1 | 腾讯 API 限流 | 每连接 5s 一次，单用户 ~1 QPS，安全 |
| 2 | setOption 重渲染性能 | 750 根 < 50ms，5s 间隔充裕 |
| 3 | SSE 连接泄漏 | `_connectKlineSSE()` 开头先 close 旧连接 |
| 4 | 非交易时段空转 | 心跳模式，前端跳过不渲染 |
| 5 | 港股冷启动误以为阻塞 | 已明示 fire-and-forget，不阻塞 event loop |

#### 回滚

```bash
git revert <commit-hash>
curl -s 'http://localhost:8000/openapi.json' | python3 -c "import sys,json; paths=json.load(sys.stdin).get('paths',{}); print('stream_kline' if '/api/stream/kline/{module}/{code}' in paths else 'OK: removed')"
sudo systemctl restart marketview
```

> 完整设计稿见 `.claude/plans/dazzling-wiggling-fern.md`
