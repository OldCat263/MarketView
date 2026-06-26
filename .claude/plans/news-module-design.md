# V1.8.0 设计稿：新闻模块（模块 8）

---

## 需求

新增第 8 个模块「📰 新闻」，展示实时财经新闻资讯流，补齐 MarketView 信息维度（行情 + K线 + 新闻）。

---

## 背景

- **当前版本**：V1.6.0.17 封版 / V1.7.0 Step 1~5 全部完成（25 commits，K线+分时图+SSE 封版）
- **涉及模块**：新闻（模块 8，从 🚧 预留 → ✅ 全量实时）
- **涉及文件**：
  - 核心文件：`backend/main.py`、`frontend/js/core.js`、`frontend/css/main.css`、`frontend/index.html`、`backend/fetcher/__init__.py`
  - 业务文件（新增）：`backend/fetcher/news.py`
  - 业务文件（改）：`frontend/js/modules/news.js`（从 placeholder 改为真模块）
- **涉及铁律**：#1（核心文件变动需审批，本次仅扩展现有文件不新建核心文件）、#2（先改 CLAUDE.md 再写代码）、#3（零本地存储）、#4（免费公开 API）、#6（模块独立封装）、#7（同步文档）、#8（设计师审批技术文档）

---

## 决策点

### 决策 1：新闻数据源（修订）

> **原选 A（AKShare js_news → 金十数据）已失效**：`akshare` 当前版本已移除 `js_news` 函数（`AttributeError`），设计稿决策前提不成立。

| 选项 | 描述 | 优劣 |
|------|------|------|
| ~~A~~ | ~~AKShare `js_news` → 金十数据~~ | ❌ 已从 AKShare 移除 |
| B | AKShare `news_cctv(date=...)` — 央视财经 | ❌ 仅每日汇总，非实时 |
| C | 东方财富 `stock_news_em` — 个股新闻 | ❌ 需指定股票代码 |
| **D（新推荐）** | **新浪财经 HTTP（主源）+ 财新头条（fallback）** | ✅ 免费无需 Key ✅ 实时 ✅ 有精确时间 ✅ 双源 fallback ❌ 需维护 HTTP 请求+解析 |
| E | 直接爬金十数据 jin10.com | ❌ 反爬风险高 |

**选 D**。新浪财经 HTTP 为免费公开 API，实时财经新闻，有精确时间戳。财新头条作为 fallback 提高可用性。双源 fallback 与港股 3 源策略一致。

### 决策 2：新闻拉取频率

| 选项 | 描述 |
|------|------|
| **A（推荐）** | 60s — 新闻不需要秒级更新 |
| B | 5s — 过于频繁，金十可能限流 |
| C | 300s — 太长，失去"实时"意义 |

**选 A**。60s 是新闻模块的合理刷频。与 spot 模块（1~5s）区分开。

### 决策 3：SSE vs 纯轮询

| 选项 | 描述 |
|------|------|
| **A（推荐）** | SSE 推送（60s 间隔），与现有 spot/K线 SSE 架构一致 |
| B | 前端 setInterval 轮询 REST API |

**选 A**。与项目 SSE 架构一致，且未来其他模块可能也走更长间隔的 SSE。

### 决策 4：前端渲染模式

| 选项 | 描述 |
|------|------|
| **A（推荐）** | 新闻独立渲染（卡片流），core.js 加 `renderMode: 'news'` 委托渲染 |
| B | 复用现有表格渲染 | ❌ 新闻不适合表格 |
| C | 新闻完全独立，不经过 core.js | ❌ 破坏模块注册模式 |

**选 A**。在 core.js 的 render() 中加 1 个分支：如果模块有自定义 `renderFn`，则委托给它。新闻模块提供自己的 `renderNews()` 实现卡片流布局。

### 决策 5：新闻卡片展示字段

| 字段 | 来源 | 说明 |
|------|------|------|
| 时间 | `datetime` | 金十发布时间 |
| 内容 | `content` | 新闻正文（可能含 【标签】） |
| 来源 | 固定 `金十数据` | 标注数据来源 |

不需要排序/翻页（新闻是时间流），但支持搜索（前端 `filter`）。

### 决策 6：新闻数据量

| 选项 | 描述 |
|------|------|
| **A（推荐）** | 全量（金十最近 4h，约 50~200 条） |
| B | 截断到固定数量（如 50 条） |

**选 A**。4 小时窗口内全量展示，数据量可控（通常 < 200 条）。

---

## 架构

```
新浪财经 HTTP（主源）
    │
    ▼
财新头条（fallback）        ← 后端 fetcher/news.py
    │
    ▼
_cache['news']              ← 1 分片，60s 滚动刷新
    │
    ├── /api/news/spot       ← REST 全量
    └── /api/stream/news     ← SSE 每 60s 推增量
            │
            ▼
       core.js _connectSSE('news')
            │  → renderMode==='news' → 全量替换（非 diff）
            ▼
       news.js renderNews()  ← 卡片流 UI
```

### 与 spot 模块的差异

| 维度 | spot 模块 | 新闻模块 |
|------|----------|----------|
| 刷新频率 | 1~5s | 60s |
| 分片数 | 1~11 | 1 |
| 渲染方式 | 表格（core.js render） | 卡片流（news.js renderNews） |
| 排序 | 可按列排序 | 固定时间倒序 |
| 翻页 | 50 条/页 | 无限滚动（简化版：全量展示，前端滚动） |
| 搜索 | 全字段模糊 | 内容模糊 |
| SSE 心跳 | 3s（独立线程） | **3s（独立线程，不受 roller interval 影响）** |

---

## 实施步骤（5 步分开发）

### Step 1：后端数据层 `backend/fetcher/news.py`

**新文件**，提供：

```python
def get_news_json():
    """拉全量：新浪财经 HTTP（主源）+ 财新头条（fallback）→ JSON
    新浪财经：HTTP 请求获取实时财经新闻
    财新头条：fallback，新浪失败时启用
    返回字段：datetime（时间）、content（内容）、source（'新浪财经' 或 '财新头条'）
    异常处理：两个源都失败 → 返回 '[]' + 日志
    """

def fetch_news_shard(shard_id, total_shards):
    """分片拉取（新闻只有 1 个分片，直接返回全量）"""
```

**数据源**：新浪财经 HTTP（主源）+ 财新头条（fallback）
**返回字段**：`datetime`（时间）、`content`（内容）、`source`（'新浪财经' 或 '财新头条'）
**异常处理**：主源失败 → fallback；两个都失败 → 返回 `[]` + 日志

### Step 2：后端集成 `backend/main.py` + `backend/fetcher/__init__.py`

改动清单：

| # | 文件 | 位置 | 改动 |
|---|------|------|------|
| 1 | `backend/fetcher/__init__.py:1-2` | import 行 + 导出 | 加 `from . import news` + 导出 `get_news_json` / `fetch_news_shard` |
| 2 | `backend/main.py:13-16` | import 行 | 加 `get_news_json, fetch_news_shard` |
| 3 | `backend/main.py:21-27` | `SHARD_CFG` | 加 `'news': {'n': 1, 'interval': 60}` |
| 4 | `backend/main.py:28-31` | `SHARD_FN` | 加 `'news': fetch_news_shard` |
| 5 | `backend/main.py:37` | `_sse_queues` | 加 `'news': queue.Queue()` |
| 6 | `backend/main.py:108` | lifespan roller 启动 | news 在 `SHARD_CFG` 循环中自动启动 |
| 7 | `backend/main.py:117` | lifespan heartbeat 启动 | news 在 `SHARD_CFG` 循环中自动启动 |
| 8 | `backend/main.py:124-150` | `_initial_load` | 加 `('news', get_news_json)` 到预加载列表 |
| 9 | `backend/main.py:189` 之后 | 新路由 | 加 `@app.get('/api/news/spot')` → `_ok(_cached_get('news'))` |

### Step 3：前端渲染 `frontend/js/modules/news.js`

**从 placeholder 改为真实模块**：

```javascript
MV.register({
  id: 'news',
  icon: '📰', name: '新闻',
  endpoint: '/api/news/spot',
  columns: ['datetime', 'content', 'source'],
  sortCol: 'datetime',
  renderMode: 'news',         // 自定义渲染
  renderFn: renderNews,       // 卡片流渲染函数
});
```

`renderNews(rows, cols)` 实现：
- 时间倒序排列
- 每条新闻一张卡片：`时间 | 内容 | 来源`
- 搜索过滤：前端 `filter` 按内容模糊匹配
- 不做翻页（全量展示，面板内滚动）

### Step 4：核心引擎适配 `frontend/js/core.js`

最小化改动（~20 行），五处：

| # | 位置 | 改动 |
|---|------|------|
| 1 | `render()` 函数开头 | 检查 `cfg.renderFn`，有则委托 `cfg.renderFn(rows, cols)` 并 return |
| 2 | `openModule()` | 新闻模块进入时 panel 布局适配（隐藏 thead/tbody，显示新闻容器） |
| 3 | `preloadAll()` | 去掉 news 的 `placeholder` 跳过逻辑（news 现在有真实 endpoint） |
| 4 | `doFilter()` | 加 `renderFn` 分支：如果当前模块有 `cfg.renderFn`，调用 `cfg.renderFn(rows, cols)` 后 return，跳过 page 重置等表格逻辑 |
| 5 | `_connectSSE()` onmessage | 加新闻模块全量替换分支：`if (registry[m].renderMode === 'news') { st.rows = shardRows; ... return; }`。原因：新闻无"代码"字段，byCode diff 索引永远空，SSE 推的数据静默丢弃。守卫条件仅命中新闻模块，不影响其他 6 模块。 |

### Step 5：CSS + HTML 适配 + 验收

| # | 文件 | 改动 |
|---|------|------|
| 1 | `frontend/css/main.css` | 加 `.news-card` / `.news-list` 样式（与 existing 暗色主题一致） |
| 2 | `frontend/index.html` | 在 `#panel` 内加 `<div id="newsPanel" style="display:none">` 容器 |

**DOM 互斥规则**（`openModule()` 中实现）：
- 进入新闻模块：`#thead/#tbody/#empty/#pager` 隐藏，`#newsPanel` 显示
- 进入非新闻模块：`#newsPanel` 隐藏，`#thead/#tbody/#empty/#pager` 显示
- 逻辑与 K线 `#kline-view` 一致：`display:none/block` 互斥

---

## 验收

### 后端验收

```bash
# 1. 模块导入检查
cd backend && python -c "from fetcher.news import get_news_json; print('OK')"

# 2. 数据拉取（AKShare 调用，预期返回 JSON 数组）
python -c "from fetcher.news import get_news_json; import json; d=json.loads(get_news_json()); print(len(d),'条新闻'); print(d[0] if d else 'EMPTY')"

# 3. REST 接口
curl -s http://localhost:8000/api/news/spot | python -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])),'条')"

# 4a. SSE 心跳验证（6s 窗口，确认 SSE 连接正常 + 3s 心跳）
curl -N -m 6 'http://localhost:8000/api/stream/news' 2>&1 | grep -c 'shard.-1'
# 预期输出: ≥1（3s 心跳，6s 内应收到 1~2 个心跳）

# 4b. SSE 数据推送验证（65s 窗口，确认包含新闻数据推送）
timeout 65 curl -N 'http://localhost:8000/api/stream/news' 2>&1 | grep -c '"shard":0'
# 预期输出: ≥1（60s 刷新一次，65s 内应收到 1 次数据推送）

# 5. OpenAPI schema 确认
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; p=json.load(sys.stdin)['paths']; print([k for k in p if 'news' in k])"
```

### 前端验收

```bash
node -c frontend/js/core.js
node -c frontend/js/modules/news.js
```

| # | 操作 | 预期 |
|---|------|------|
| 1 | 首页 → 新闻卡片 | 显示 🚧 → ✅ 状态，显示新闻条数 |
| 2 | 点击新闻卡片 | 面板打开，显示新闻卡片流（时间倒序） |
| 3 | 搜索框输入关键词 | 过滤匹配新闻 |
| 4 | 每 60s | 新新闻自动出现（SSE 推送） |
| 5 | 切到其他模块再切回 | 新闻状态保持，不串台 |
| 6 | 返回首页 → 再进新闻 | 数据仍在 |
| 7 | F12 Network EventStream | `/api/stream/news` 持续连接 |
| 8 | 移动端 | 新闻卡片响应式适配 |

---

## 技术文档改动范围（必填）

按 [执行者入门指南 §0.1 分工表](./docs/执行者入门指南.md)，本次改动**执行者要同步更新的技术文档**：

- [ ] `backend/fetcher/news.py` 文件头注释（新增文件，必须标注数据源+字段+fallback）
- [ ] `docs/API文档.md` — 新增 §10 新闻接口（REST + SSE），含字段表
- [ ] `docs/故障排查.md` — 新增新闻模块坑位（AKShare js_news 返回空 / 金十限流 / 新闻不更新）

> **设计师维护的文档**（执行者不改）：CLAUDE.md、设计师入门指南、开发手册、API 文档 §8 SSE 通用说明（如需要）。

---

## 风险

| # | 风险 | 应对 |
|---|------|------|
| 1 | 新浪财经 HTTP 请求阻塞 ~1-3s | 放在 `asyncio.to_thread` 中执行，不阻塞 event loop |
| 2 | 新浪/财新反爬/限流 | 60s 低频 + 异常返回空数组 + 日志告警，不崩主流程。双源 fallback 提高可用性 |
| 3 | 新闻面板与表格面板共享 DOM | 用 `#newsPanel` 独立容器 + `display:none` 互斥，类似 K线 `#kline-view` |
| 4 | core.js 改动扩散 | 仅 5 处 ~20 行（render + openModule + preloadAll + doFilter + SSE 全量替换分支） |
| 5 | 非交易时段新闻少 | 正常现象，前端不做特殊处理 |
| 6 | 新闻 SSE diff 不生效（无"代码"字段） | `_connectSSE` 加 `renderMode==='news'` 全量替换分支，守卫条件仅命中新闻模块 |

---

## 回滚

```bash
# 1. 回滚到上一版本
git revert <commit-hash>

# 2. 验证新闻端点已移除
curl -s 'http://localhost:8000/openapi.json' | python3 -c "import sys,json; paths=json.load(sys.stdin).get('paths',{}); print([k for k in paths if 'news' in k])"
# 预期输出: []（空列表）

# 3. 重启服务
sudo systemctl restart marketview

# 4. 快速验证（应 404）
curl -s -o /dev/null -w '%{http_code}' 'http://localhost:8000/api/news/spot'
```

回退后状态：新闻模块回到 🚧 placeholder 状态，其余 7 模块不受影响。

---

## 附录：API 字段表（Step 2 实施后写入 API 文档 §10）

### 10. 新闻 — AKShare 金十数据

```
GET /api/news/spot
```

**数据源**: 新浪财经 HTTP（主源）+ 财新头条（fallback）
**缓存**: 服务端分片缓存 + 60s 滚动刷新
**数据量**: 最近 4 小时，通常 50~200 条

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| datetime | string | 发布时间，格式 YYYY-MM-DD HH:MM:SS |
| content | string | 新闻内容 |
| source | string | 实际媒体来源名称（新浪 API 返回 media_name，如"环球市场播报"）或 "财新头条" |

### 10.1 新闻 SSE 实时推送

```
GET /api/stream/news
```

**间隔**: 每 60s 推一次增量数据（与数据刷新同频）
**消息格式**: `{shard: 0, data: [...], ts}` / `{shard: -1, data: [], ts}`（心跳）
