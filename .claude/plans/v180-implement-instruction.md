# V1.8.0 实施指令：新闻模块（模块 8）— 修订版

> **修订说明**：原 AKShare `js_news` → 金十数据方案已失效（`AttributeError`），数据源改为新浪财经 HTTP + 财新头条 fallback。补 SSE 全量替换分支（设计稿遗漏）。审批员已签字通过原版，修订部分设计师已审批。
> **实施策略**：5 步分开发，Step 1~4 设计师轻量验收，Step 5 完整复审
> **设计稿**：[news-module-design.md](./news-module-design.md)

---

## 背景

- **当前版本**：V1.7.0 封版
- **目标版本**：V1.8.0
- **改动**：新增新闻模块（模块 8），从 🚧 placeholder → ✅ 全量实时
- **涉及铁律**：#1（核心文件仅扩展不新建）、#2（先改 CLAUDE.md）、#3（零本地存储）、#4（免费 API）、#6（模块独立）、#7（同步文档）、#8（审批技术文档）

---

## Step 1：后端数据层 `backend/fetcher/news.py`

**新建文件** `backend/fetcher/news.py`，提供 2 个函数。

### 文件头注释（必填）

```python
"""模块八：新闻 — 新浪财经 HTTP（主源）+ 财新头条（fallback）
数据源：新浪财经 HTTP（免费公开，实时，~50 条，有精确时间戳）→ 财新头条（fallback）
返回字段：datetime（时间）、content（内容）、source（'新浪财经' 或 '财新头条'）
异常处理：主源失败 → fallback；两个都失败 → 返回 '[]' + 日志，不抛异常阻塞主流程
刷新频率：60s（SHARD_CFG 控制）
"""
```

### 函数说明

```python
def get_news_json():
    """拉全量：新浪财经 HTTP（主源）+ 财新头条（fallback）→ JSON
    返回字段：datetime、content、source
    """

def fetch_news_shard(shard_id, total_shards):
    """分片拉取（新闻只有 1 个分片，直接返回全量）"""
```

### ⚠️ 执行者需补充

执行者已实现此文件（~99 行），**需补充**：
- [ ] 文件头注释改为上述模板（标注数据源 + 字段 + fallback）
- [ ] 确认新浪财经 HTTP 请求 URL + 响应格式（写入注释）
- [ ] 确认财新头条 fallback 的请求方式（写入注释）
- [ ] 确认 60s 低频策略（限流保护）

### 验收命令

```bash
cd backend
python -c "from fetcher.news import get_news_json; print('OK')"
python -c "from fetcher.news import get_news_json; import json; d=json.loads(get_news_json()); print(len(d),'条新闻'); print(d[0] if d else 'EMPTY')"
```

### 回报模板

```
Step 1 完成（修订版）：
- [ ] 文件头注释已标注：数据源 + 字段 + fallback
- [ ] 新浪财经 HTTP URL: ___
- [ ] 财新头条 fallback 方式: ___
- [ ] 模块导入 OK
- [ ] 数据拉取：___ 条新闻，首条 datetime=___ content=___ source=___
- [ ] 异常测试：主源失败时 fallback 是否 OK；两个都失败时是否返回 []
```

---

## Step 2：后端集成 `backend/main.py` + `backend/fetcher/__init__.py`

### 改动清单（9 处）

| # | 文件 | 位置 | 改动 |
|---|------|------|------|
| 1 | `backend/fetcher/__init__.py` | 末尾追加 | `from . import news` + 导出 `get_news_json` / `fetch_news_shard` |
| 2 | `backend/main.py:13-16` | import 行 | 加 `get_news_json, fetch_news_shard` |
| 3 | `backend/main.py:21-27` | `SHARD_CFG` | 加 `'news': {'n': 1, 'interval': 60}` |
| 4 | `backend/main.py:28-31` | `SHARD_FN` | 加 `'news': fetch_news_shard` |
| 5 | `backend/main.py:37` | `_sse_queues` | 确认 SHARD_CFG 加后自动覆盖 |
| 6 | `backend/main.py:108` | lifespan roller | news 自动启动 |
| 7 | `backend/main.py:117` | lifespan heartbeat | news 自动启动 |
| 8 | `backend/main.py:124-150` | `_initial_load` | 加 `('news', get_news_json)` |
| 9 | `backend/main.py:189` 之后 | 新路由 | `@app.get('/api/news/spot')` → `_ok(_cached_get('news'))` |

### 回报模板

```
Step 2 完成：
- [ ] 启动日志含 [roller] news + [heartbeat] news
- [ ] REST 接口：___ 条新闻
- [ ] SSE 心跳：___ 个（预期 ≥1）
- [ ] SSE 数据：___ 个（预期 ≥1，需等 65s）
- [ ] OpenAPI 含 news 路径
- [ ] 技术文档同步：
  - [ ] docs/API文档.md 新增 §10 新闻接口（source 字段改为 '新浪财经' 或 '财新头条'）
  - [ ] docs/故障排查.md 新增新闻模块坑位
```

---

## Step 3：前端渲染 `frontend/js/modules/news.js`

**替换** `frontend/js/modules/news.js`（从 placeholder 改为真实模块）。

### 完整代码

```javascript
// 模块八：新闻 — 新浪财经 HTTP + 财新头条 fallback（V1.8.0）

function renderNews(rows, cols) {
  let panel = document.getElementById('newsPanel');
  if (!panel) return;

  // 搜索过滤
  let q = document.getElementById('search').value.trim().toLowerCase();
  let filtered = rows;
  if (q) filtered = rows.filter(r => String(r['content'] || '').toLowerCase().includes(q));

  // 时间倒序
  filtered = [...filtered].sort((a, b) => (b['datetime'] || '').localeCompare(a['datetime'] || ''));

  // 计数
  document.getElementById('count').textContent = filtered.length + ' 条';

  // 渲染卡片
  if (!filtered.length) {
    panel.innerHTML = '<div class="empty">暂无新闻</div>';
    return;
  }
  panel.innerHTML = filtered.map(r => {
    let dt = r['datetime'] || '';
    let content = r['content'] || '';
    let src = r['source'] || '';
    return '<div class="news-card">' +
      '<div class="news-card-time">' + dt + '</div>' +
      '<div class="news-card-content">' + content + '</div>' +
      '<div class="news-card-source">来源：' + src + '</div>' +
    '</div>';
  }).join('');
}

MV.register({
  id: 'news',
  icon: '📰', name: '新闻',
  endpoint: '/api/news/spot',
  columns: ['datetime', 'content', 'source'],
  sortCol: 'datetime',
  renderMode: 'news',
  renderFn: renderNews,
  format: function(v, col) {
    return String(v);  // 新闻不做数字格式化
  },
});
```

### 回报模板

```
Step 3 完成：
- [ ] node -c 语法通过
- [ ] renderNews 函数存在
- [ ] MV.register 包含 renderFn: renderNews
- [ ] 搜索过滤按 content 模糊匹配
- [ ] 时间倒序排列
```

---

## Step 4：核心引擎适配 `frontend/js/core.js`

5 处改动，共 ~20 行。

### #1 `render()` 函数开头（`core.js:54`）

```javascript
function render() {
  // --- V1.8.0: renderFn 委托渲染 ---
  let cfg = registry[tab];
  if (cfg && cfg.renderFn) { cfg.renderFn(rows, cols); return; }
  let r = rows;
  ...
```

### #2 `openModule()` 中布局适配（`core.js:118` 附近）

```javascript
    // --- V1.8.0: 新闻面板 / 表格面板 互斥 ---
    let isNews = cfg && cfg.renderFn;
    document.getElementById('newsPanel').style.display = isNews ? 'block' : 'none';
    document.getElementById('thead').style.display = isNews ? 'none' : '';
    document.getElementById('tbody').style.display = isNews ? 'none' : '';
    document.getElementById('empty').style.display = isNews ? 'none' : '';
    document.getElementById('pager').style.display = 'none';
```

### #3 `preloadAll()` 去 news placeholder 跳过（`core.js:168`）

```javascript
// 原：if (m.id === 'crypto' || m.id === 'news' || m.placeholder) return;
// 改：
if (m.id === 'crypto' || m.placeholder) return;
```

### #4 `doFilter()` 加 renderFn 分支（`core.js:306`）

```javascript
function doFilter() {
  page = 1;
  // --- V1.8.0: 新闻搜索不走 page 重置 ---
  let cfg = registry[tab];
  if (cfg && cfg.renderFn) { cfg.renderFn(rows, cols); return; }
  render();
}
```

### #5 `_connectSSE()` onmessage 加新闻全量替换分支（设计稿补遗）

在 `_sse.onmessage` 中、原有 `byCode` diff 逻辑之前插入：

```javascript
        // --- V1.8.0: 新闻模块全量替换（无"代码"字段，diff 不生效）---
        if (registry[m] && registry[m].renderMode === 'news') {
          st.rows = shardRows;
          st.fetchTime = Date.now();
          st.updateTime = new Date().toLocaleTimeString();
          if (tab === m) { rows = st.rows; updateTime = st.updateTime; render(); }
          let card = document.getElementById('card_' + m);
          if (card) card.querySelector('.card-count').textContent = st.rows.length + ' 条';
          let ls = document.getElementById('liveStatus');
          if (ls) ls.innerHTML = '<span class="conn-dot on"></span>实时';
          return;  // 提前返回，不进入 byCode diff 逻辑
        }
```

**为什么需要**：新闻数据字段是 `datetime/content/source`，没有"代码"字段。原有 `byCode` 按 `r['代码'] || r['交易对']` 建索引，新闻数据索引永远空 → diff 静默跳过 → SSE 推的新闻数据永远不更新 UI。

**不影响其他 6 模块**：`renderMode === 'news'` 守卫条件仅新闻模块为 true，其余模块 `renderMode` 为 undefined。

### 回报模板

```
Step 4 完成：
- [ ] node -c 语法通过
- [ ] render() 开头有 renderFn 分支
- [ ] openModule() 有新闻/表格互斥逻辑
- [ ] preloadAll() 已去掉 news placeholder 跳过
- [ ] doFilter() 有 renderFn 分支
- [ ] _connectSSE() 有 renderMode==='news' 全量替换分支
- [ ] git diff core.js 改动 ≤30 行
```

---

## Step 5：CSS + HTML + 验收

### #1 `frontend/css/main.css` 末尾追加

```css
/* ─── 新闻卡片（V1.8.0）── */
.news-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:10px;transition:border-color .2s}
.news-card:hover{border-color:var(--gold)}
.news-card-time{font-size:12px;color:var(--dim);margin-bottom:6px}
.news-card-content{font-size:14px;line-height:1.6;color:var(--text)}
.news-card-source{font-size:11px;color:var(--dim);margin-top:6px;text-align:right}
```

### #2 `frontend/index.html` 加 `#newsPanel` 容器

在 `#panel` 内、`<div class="wrap">` 之前插入：

```html
    <div id="newsPanel" style="display:none"></div>
```

### #3 `frontend/index.html` 首页新闻卡片文案

将新闻卡片的 🚧 硬编码去掉：
```javascript
// 原：
'<div class="card-status"><span class="status">'+((m.id==='news')?'🚧':'⏳')+'</span></div>'+
'<div class="card-count">'+((m.id==='news')?'即将上线':'等待加载')+'</div>'+
// 改：
'<div class="card-status"><span class="status">⏳</span></div>'+
'<div class="card-count">等待加载</div>'+
```

### 验收命令

```bash
# 语法检查
node -c frontend/js/core.js
node -c frontend/js/modules/news.js

# 后端全链路
curl -s http://localhost:8000/api/news/spot | python -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])),'条新闻')"

# 浏览器实测 8 项（手测）
```

| # | 操作 | 预期 |
|---|------|------|
| 1 | 首页 → 新闻卡片 | ✅ + 条数 |
| 2 | 点击新闻卡片 | 卡片流，时间倒序 |
| 3 | 搜索框输入关键词 | 过滤匹配 |
| 4 | 等 60s | 新新闻出现 |
| 5 | 切到 A股再切回 | 不串台 |
| 6 | 返回首页 → 再进新闻 | 数据仍在 |
| 7 | F12 Network EventStream | `/api/stream/news` 持续连接 |
| 8 | 移动端 | 响应式 |

### 回报模板

```
Step 5 完成：
- [ ] CSS 语法正确
- [ ] #newsPanel 容器存在
- [ ] 首页新闻卡片不再显示 🚧
- [ ] 浏览器实测 1~8 项全过
- [ ] 技术文档同步（4 检查点）：
  - [ ] 字段名/类型与代码一致
  - [ ] fetcher 注释反映数据源+fallback
  - [ ] 故障排查有完整复现+修复
  - [ ] 改动与设计稿一致无扩边界
```

---

## 技术文档改动范围（执行者必改）

- [ ] `backend/fetcher/news.py` 文件头注释（数据源+字段+fallback）
- [ ] `docs/API文档.md` — 新增 §10 新闻接口（source 字段：'新浪财经' 或 '财新头条'）
- [ ] `docs/故障排查.md` — 新增新闻模块坑位

## 设计师维护的文档（执行者不改）

- `CLAUDE.md` — 版本历史 + 模块清单 🚧→✅ + 数据源更新
- `docs/设计师入门指南.md` — §0 + 版本记录
- `docs/开发手册.md` — 如需

---

## 完成后

执行者按回报模板回报，包含：
1. 每 Step 验收命令实际输出
2. git diff 统计
3. 技术文档同步清单 + 4 检查点自检
4. commit hash

Step 1~4 → 设计师轻量验收。Step 5 → 设计师验收 + 审批员完整复审 → 封版 V1.8.0。
