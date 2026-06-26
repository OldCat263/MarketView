# CLAUDE.md — MarketView 全市场数据展示平台

> **写给后来者**：无论你是人类还是 AI，先读完这个再动手。

---

## 项目概览

- **名称**：MarketView
- **干什么**：一站式展示全球金融市场实时数据 + K线图
- **架构**：FastAPI 后端 + 多文件 HTML 前端（HTML骨架+CSS+核心引擎+模块注册） + 客户端 sessionStorage 缓存
- **数据源**：AkShare + 腾讯 qt.gtimg.cn + Binance + 新浪（全部免费公开 API，无需注册）
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
| `backend/fetcher/` | 数据获取模块（每模块独立文件，详见模块清单） |
| `backend/requirements.txt` | Python 依赖 |
| `frontend/index.html` | 前端入口 | 纯HTML骨架，加载CSS/JS模块 |
| `frontend/css/main.css` | 样式 | 暗色主题，响应式 |
| `frontend/js/core.js` | 核心引擎 | 状态管理/渲染/SSE/模块切换 |
| `frontend/js/modules/*.js` | 7模块 | 每模块独立注册 |
| `chanlun/` | 参考资料（只读） |
| `.trae/skills/` | ⭐ 4 个 AI Skill（designer/executor/reviewer/validator），按角色触发节省 token |

## 模块清单

| # | 模块 | 数据源（优先级从左到右） | 数量 | 状态 |
|---|------|------------------------|------|------|
| 1 | 🪙 加密货币 | Binance API（需代理，服务器无代理时显示未检测） | 全量实时 | ✅ |
| 2 | 📈 A股 | 腾讯 qt.gtimg.cn → 东财 → 新浪 | 全量实时 | ✅ |
| 3 | 📊 ETF | 东财 fund_etf_spot_em → 同花顺 | 全量实时 | ✅ |
| 4 | 🌏 港股 | 腾讯 → 东财 stock_hk_spot_em → 新浪 stock_hk_spot | 全量实时 | ✅ |
| 5 | 🇺🇸 美股 | 腾讯 qt.gtimg.cn（us前缀）→ 东财 → 新浪 | 全量实时 | ✅ |
| 6 | 📉 指数 | 东财 → 新浪（global需海外网络，限流时为空） | 全量实时 | ✅ |
| 7 | 📈 K线 | 6 模块全支持 + ECharts 三联图 + 分时图（V1.7.0 Step 1+2 ✅ / Step 3 ✅ / Step 4 ✅ / Step 4.5 ✅ 分时图+K线美化） | 全量实时 | ✅ |
| 8 | 📰 新闻 | 预留 | — | 🚧 |

## 数据源详解

### A股：腾讯 qt.gtimg.cn（主要）
- 批量查询：50 只/请求，自动分批拉取全量
- 字段：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、最高、最低、今开、昨收、**振幅、换手率、量比**
- 自动回退：东财 → 新浪

### 港股：腾讯 → 东财 → 新浪（V1.6.0.1 改）
- 腾讯为主源（10 只/请求）
- 东财 AkShare `stock_hk_spot_em` 冷启动 ~2 分钟
- 新浪 `stock_hk_spot` 兜底
- 多源 fallback 解决 RemoteDisconnected 导致 0 行

### 加密货币：Binance API
- 端点：`api.binance.com/api/v3/ticker/24hr`
- 自动扫描代理端口：7897/7890/10809/10808/1080/8118/8888
- 用户也可手动设置 `CRYPTO_PROXY` 环境变量
- 每次点击重新检测代理连通性

### ETF/美股/指数：AkShare 自动切换
- 所有模块均含数据源缓存，首次找到可用源后直接复用
- ETF：东财 fund_etf_spot_em → 同花顺
- 美股：腾讯 qt.gtimg.cn（us 前缀，17209 条）→ 东财 → 新浪
- 指数：东财 index_global_spot_em → 新浪（global 字段需海外网络，限流时为空）

### K线（V1.7.0+）：腾讯 K线接口 + Binance Klines
- A股/ETF/指数：腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`（日/周/月）+ `ifzq.gtimg.cn/appstock/app/kline/mkline`（分钟 1m/5m/15m/30m/60m，不带 web 前缀）
- 港股：腾讯 `appstock/app/hfqkline/get`（hk 前缀）
- 美股：腾讯 `appstock/app/usfqkline/get`（us 前缀）
- 加密：Binance `/api/v3/klines`
- 8 周期：1m/5m/15m/30m/60m/1d/1w/1M
- 指标计算：纯 Python（MA5/10/20/60/120/250 + BOLL(20/2) + MACD(12/26/9)）
- 分钟K线注意：fqkline 不支持分钟周期（返回空），自动切换 mkline；mkline 不返回成交额（amount=0）
- **分时图**（V1.7.0 Step 4.5）：分钟周期（1m/5m）自动切分时折线图（价格线+昨收虚线+VOL柱）；"分时"按钮手动切换；昨收并行 fetch 日K倒数第二根 close，失败静默降级

## 前端架构
- **首页**：8 张卡片网格（3×3），首次访问显示进度条+加载时间
- **数据视图**：表格 + 搜索 + 排序 + 翻页（50条/页）
- **K线视图**（V1.7.0）：独立行情页（顶部导航"行情"入口） + ECharts 三联图（主+VOL+MACD）+ 分时图（价格折线+昨收虚线+VOL柱） + 8周期切换 + 搜索（spot数据索引+6模块跨搜）+ ECharts 原生图例点击显隐 MA/BOLL
- **实时推送**：SSE (`/api/stream/{module}`) + 分片滚动刷新，单元格 diff 闪动
- **心跳机制**（V1.6.0.6）：后端每 3s 推 `shard=-1` 空数据，前端刷新 `fetchTime` 维持绿点
- **客户端缓存**：sessionStorage（前端状态恢复，**非实时数据源**，TTL 15s）
- **模块隔离**：ST 对象独立存储每模块的 rows/cols/page/sort/search，互不干扰
- **时间显示三件套**：globalStamp（UI 时钟，每秒跳）+ viewTime（客户端实时时间，V1.6.0.8 回滚到 V1.6.0.3 行为，每秒跳）+ liveStatus（数据新鲜度，SSE 推时"实时"绿点，断连时"离线"红点）

## 🔴 铁律

| # | 铁律 |
|---|------|
| 1 | 核心文件不变，不许随意加文件 |
| 2 | 先改 CLAUDE.md 再写代码 |
| 3 | 零本地存储 |
| 4 | 数据源仅限免费公开 API |
| 5 | 做完记录版本历史 |
| 6 | 每个模块完全独立封装 |
| 7 | **每次新需求必须同步更新 [设计师入门指南 §0](./docs/设计师入门指南.md) 的同步更新规则** |
| 8 | **设计师：改完代码必须审批执行者改的技术文档（见 [设计师入门指南 §7.1](./docs/设计师入门指南.md) 4 检查点）** |

## 模块加载速度（V1.6.0.1 实测 2026-06-25 / V1.6.0.6 心跳已加）

| 模块 | 首启 | 稳态滚动 | 数据量 | 数据源 |
|------|------|----------|--------|--------|
| 🪙 加密货币 | 0.5s（需代理） | — | 0（无代理） | Binance |
| 📈 A股 | 63ms（并发） | 3s diff 闪动 + 3s 心跳 | 5528 条 | 腾讯 qt.gtimg.cn |
| 📊 ETF | ~5s | 5s diff 闪动 + 3s 心跳 | 1516 条 | 东财 fund_etf_spot_em |
| 🌏 港股 | ~2min（AkShare 冷启） | 5s diff 闪动 + 3s 心跳 | 2773 条 | 腾讯 + 东财/新浪 fallback |
| 🇺🇸 美股 | ~8min（首拉代码列表） | 5s diff 闪动 + 3s 心跳 | 17209 条 | 腾讯 qt.gtimg.cn（us 前缀）|
| 📉 指数 | <1s | 3s diff 闪动 + 3s 心跳 | 562 条 | 新浪 index_spot_sina |
| 📈 K线（V1.7.0） | 计划 < 2s | 5s 推最新 K线 | 750 根（日K） | 腾讯 K线 + Binance klines |

> V1.6.0 起：分片缓存 + SSE 实时推送，浏览器侧看到的是**持续跳动**的实时行情，不再是 10s 静默刷新。
> V1.6.0.6 起：每 3s 心跳维持客户端 liveStatus 绿点（即使数据静止也不变红）。
> US 首次 ~8min 是 `_load_us_codes()` 下载 17636 条代码的一次性成本，后续秒级。
> HK 首次 ~2min 是 AkShare `stock_hk_spot()` 冷启动一次成本，后续秒级。

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

### 3.5 K线专项检查（V1.7.0+）
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
| V1.7.0 | 2026-06-26 | 🔄 **K线图**（P2 体验优化）：**Step 1 ✅**（后端 kline.py+indicators.py+路由，2f1494e，6 模块 + MA/BOLL/MACD 指标 + MA5 对账 manual=1267.536=API）；**Step 2 ✅**（港股 K线 3 源 fallback tencent→eastmoney→sina + API 文档 §9 K线字段表补 4 处 + 故障排查 §5.6.1 港股 K线 0 行案例，8043d69，4 检查点全过）；**Step 3 ✅**（K线前端骨架 ECharts 接入 — index.html + main.css + kline.js，导航栏+容器+三联图+MA/BOLL/MACD+8周期+显隐矩阵+dispose重建策略，验收 5/5 K线接口全过）；**Step 4 ✅ 分钟K线数据源修复**（`_fetch_tencent_minute` — 换用 `ifzq.gtimg.cn` mkline 接口 [HTTPS 无 web 前缀]，解析路径 `data[code][m5]` 6 列格式，datetime YYYYMMDDHHmm→标准格式，amount 填 0；`_fetch_tencent` 加点判断自动分流分钟→mkline）；**Step 4.5 ✅ 分时图 + K线美化**（a296607~fb3c25e，11 commits）：① 分时图 `buildMinuteOption()` 价格折线+昨收虚线 markLine+VOL 柱+涨跌区域半透明填充 ② "分时"按钮 `toggleMinute()` 手动切换，并行 fetch 1m+1d 取昨收，失败静默降级 ③ 周期联动 1m/5m→分时，≥15m→K线 ④ K线美化 barMaxWidth:20/min:4 + grid splitLine opacity 0.12 + yAxis 右置 ⑤ ECharts 原生图例点击显隐 MA/BOLL 各线（替代 checkbox）⑥ dataZoom 默认最近 10%（start:90）⑦ 搜索 spot 数据索引+6模块跨搜+回车+当前模块优先 ⑧ tooltip ECharts 5.5 5 元素兼容 + MACD 合并一行 + 中文标签 ⑨ 昨收价显示在标题栏金色数字 ⑩ dblclick 表格→K线传递代码+名称 ⑪ sessionStorage 缓存（交易时段 60s TTL，非交易时段无限）；**Step 5 计划**（K线 SSE 5s 推最新K线 + 完整联调）。独立行情页（顶部导航"行情"入口）+ ECharts 三联图（主+VOL+MACD）+ 分时图 + 6模块全支持 + 8周期 + MA5/10/20/60/120/250 + BOLL(20/2) + MACD(12/26/9)。VOL 副图必开、MACD 默认关。指标纯 Python 计算（不引 pandas）。**附带发现 P1**：验收脚本 mv_validate.py 在 Windows GBK 终端 emoji 编码崩溃（V1.6.0.15 ✅ 已修） |
