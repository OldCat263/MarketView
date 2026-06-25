# CLAUDE.md — MarketView 全市场数据展示平台

> **写给后来者**：无论你是人类还是 AI，先读完这个再动手。

---

## 项目概览

- **名称**：MarketView
- **干什么**：一站式展示全球金融市场实时数据
- **架构**：FastAPI 后端 + 单文件 HTML 前端 + 客户端 sessionStorage 缓存
- **数据源**：AkShare + 腾讯 qt.gtimg.cn + Binance + 新浪（全部免费公开 API，无需注册）

## 固定文件清单

| 文件 | 职责 |
|------|------|
| `CLAUDE.md` | 📖 项目手册 |
| `backend/main.py` | FastAPI 入口，分片缓存 + SSE推送 |
| `backend/fetcher/` | 数据获取模块(7独立文件) |
| `backend/requirements.txt` | Python 依赖 |
| `frontend/index.html` | 前端入口 | 纯HTML骨架，加载CSS/JS模块 |
| `frontend/css/main.css` | 样式 | 暗色主题，响应式 |
| `frontend/js/core.js` | 核心引擎 | 状态管理/渲染/SSE/模块切换 |
| `frontend/js/modules/*.js` | 7模块 | 每模块独立注册 |
| `chanlun/` | 参考资料（只读） |

## 模块清单

| # | 模块 | 数据源（优先级从左到右） | 数量 | 状态 |
|---|------|------------------------|------|------|
| 1 | 🪙 加密货币 | Binance API（需代理，服务器无代理时显示未检测） | 全量实时 | ✅ |
| 2 | 📈 A股 | 腾讯 qt.gtimg.cn → 东财 → 新浪 | 全量实时 | ✅ |
| 3 | 📊 ETF | 东财 fund_etf_spot_em → 同花顺 | 全量实时 | ✅ |
| 4 | 🌏 港股 | 东财 stock_hk_spot_em → 新浪 stock_hk_spot | 全量实时 | ✅ |
| 5 | 🇺🇸 美股 | 腾讯 qt.gtimg.cn（us前缀）→ 东财 → 新浪 | 全量实时 | ✅ |
| 6 | 📉 指数 | 东财 → 新浪（global需海外网络，限流时为空） | 全量实时 | ✅ |
| 7 | 📰 新闻 | 预留 | — | 🚧 |

## 数据源详解

### A股：腾讯 qt.gtimg.cn（主要）
- 批量查询：50 只/请求，自动分批拉取全量
- 字段：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、最高、最低、今开、昨收、**振幅、换手率、量比**
- 自动回退：东财 → 新浪

### 加密货币：Binance API
- 端点：`api.binance.com/api/v3/ticker/24hr`
- 自动扫描代理端口：7897/7890/10809/10808/1080/8118/8888
- 用户也可手动设置 `CRYPTO_PROXY` 环境变量
- 每次点击重新检测代理连通性

### ETF/港股/美股/指数：AkShare 自动切换
- 所有模块均含数据源缓存，首次找到可用源后直接复用

## 前端架构

- **首页**：7 张卡片网格（3×3），首次访问显示进度条+加载时间
- **数据视图**：表格 + 搜索 + 排序 + 翻页（50条/页）
- **缓存**：sessionStorage 10 秒 TTL，后台 10 秒静默刷新
- **模块隔离**：ST 对象独立存储每模块的 rows/cols/page/sort/search，互不干扰

## 🔴 铁律

| # | 铁律 |
|---|------|
| 1 | 核心文件不变，不许随意加文件 |
| 2 | 先改 CLAUDE.md 再写代码 |
| 3 | 零本地存储 |
| 4 | 数据源仅限免费公开 API |
| 5 | 做完记录版本历史 |
| 6 | 每个模块完全独立封装 |

## 模块加载速度（服务器实测 2026-06-25）

| 模块 | 耗时 | 数据量 | 数据源 |
|------|------|--------|--------|
| 🪙 加密货币 | 0.5s | 需代理 | Binance |
| 📈 A股 | 51s | 5528 条 | 腾讯 qt.gtimg.cn |
| 📊 ETF | 38s | 1516 条 | 东财 fund_etf_spot_em |
| 🌏 港股 | 35s | 2773 条 | 新浪 stock_hk_spot |
| 🇺🇸 美股 | 60s(超时) | 0 | 新浪超时 |
| 📉 指数 | <1s | 562 条 | 新浪 index_spot_sina |

> 首次加载约 51 秒（并行取最慢模块）。刷新秒开（sessionStorage）。

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
- [ ] 数据时间戳是否在最近交易时段内
- [ ] 非交易时段数据是否为最近交易日收盘数据
- [ ] 后台静默刷新（10 秒）是否正常更新缓存

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
uvicorn main:app --workers 4
# 浏览器打开 frontend/index.html
```

## 待清理清单（V1.6.0 执行，不实际删除仅记录）

### A. 垃圾文件（12 个，建议删除）

| 文件 | 说明 |
|------|------|
| `nul` | PowerShell `curl -o NUL` 误创建的空文件 |
| `t.json` (1.3MB) | A股测试输出 |
| `te.json` `th.json` `ti.json` `ts.json` `tu.json` | ETF/港股/指数/A股/美股 测试输出 |
| `etf_test.json` `stock_test.json` | 测试输出 |
| `A股模块API测试报告.md` `ETF模块API测试报告.md` | 测试报告（速度已记入版本历史） |
| `oldcat-realtime-upgrade.html` | 旧实时化方案展示页（Trae 生成，已被 V1.6.0 设计取代） |

### B. 代码冗余（4 处，建议清理）

| 位置 | 问题 | 处理 |
|------|------|------|
| `backend/main.py:21` | `_cached_get(key, fetcher_fn)` 的 `fetcher_fn` 参数从未被调用 | 删参数 |
| `backend/main.py:62` | `NO_CACHE = {}` 空字典当 headers 传等于没传，命名误导 | 删变量 |
| `backend/fetcher/crypto.py:8-15` | `detect()` 与 `status()` 功能重叠，仅 print 不设 `_found_proxy` | 合并进 `status()` |
| `frontend/js/core.js:51` | `let totalModules` 定义后从未使用（preloadAll 用 `totalMods`） | 删死变量 |

### C. 文档过时（保留，V1.6.0 同步更新）

| 文件 | 过时点 |
|------|--------|
| `docs/API文档.md` | base URL、美股源（改腾讯）、缓存策略描述 |
| `CLAUDE.md` 固定文件清单 | `fetcher.py`→`fetcher/` 目录、`index.html`→`core.js+7模块+main.css` |

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
