# V1.7.0 Step 5 设计稿：K线 SSE 实时推送

---

## 需求

K线图每 5s 自动更新最新一根蜡烛，无需手动刷新。与现有 spot 模块 SSE 实时推送架构一致。

---

## 背景

- **当前版本**：V1.6.0.17 封版 / V1.7.0 Step 1~4.5 已完成（20 commits，UA 测试 8/8 全过）
- **涉及模块**：K线（模块 7）
- **涉及铁律**：#1（核心文件不变，仅改已有文件 `backend/main.py` + `frontend/js/kline.js`）、#2（先改 CLAUDE.md 再写代码）、#6（模块独立，K线 SSE 不触及 spot 模块）、#7（同步技术文档：API 文档 + 故障排查）

> **港股 2min 预热说明**：港股 AkShare `stock_hk_spot()` 首次冷启动 ~2min，该预热在 [`backend/main.py:124-150`](backend/main.py#L124-L150) `_initial_load()` 中以 **daemon 线程 fire-and-forget** 执行（不阻塞启动 + 不阻塞其他模块请求）。Step 5 K线 SSE handler 中的 `asyncio.to_thread(fetch_fn, ...)` 同样 **fire-and-forget**：每次 SSE 循环的 fetch 在线程池中执行，不阻塞 asyncio event loop。两处均无阻塞风险，K线 SSE 不需要等港股预热完成即可工作。

---

## 决策点

### 决策 1：SSE vs 轮询

| 选项 | 描述 |
|------|------|
| **A（推荐）** | SSE 长连接：后端每 5s 推送最新一根蜡烛 |
| B | 前端 setInterval 轮询 REST API |

**选 A**。与 spot 模块 SSE 架构一致（[`backend/main.py:232-247`](backend/main.py#L232-L247) `stream_module` 模式），避免无意义的 HTTP 轮询。

### 决策 2：推送粒度

| 选项 | 描述 |
|------|------|
| **A（推荐）** | 只推最新一根蜡烛（或心跳） |
| B | 推全量 750 根 + 指标 |

**选 A**。每 5s 推 ~100 字节 vs 推 ~50KB，带宽差 500 倍。MA/BOLL/MACD 指标由前端定时全量刷新异步校准：日K/周K/月K 等长周期每 30s，1m 周期每 60s（避免 1m K线 30s 校准漏 30 根新蜡烛）。

### 决策 3：后端架构

| 选项 | 描述 |
|------|------|
| **A（推荐）** | 每连接独立轮询：SSE handler 内 `asyncio.to_thread → fetch → push → sleep(5) → loop` |
| B | 全局 roller+queue（类似 spot 模块 [`backend/main.py:68-86`](backend/main.py#L68-L86) `_roller`） |

**选 A**。K线是 per-(code, period) 的，不同用户看不同股票，全局 roller 要管理 N 个 queue 太复杂。每连接独立轮询对单用户场景足够，且无需 `_cache_lock` 等共享状态。

### 决策 4：前端更新策略

| 方式 | 间隔 | 更新内容 | animation |
|------|------|----------|-----------|
| SSE 推送 | 每 5s | 最新一根蜡烛 → `chart.setOption({notMerge: true})` | `false`（避免每 5s 闪一次） |
| 全量刷新 | 每 30s（1m 周期 60s） | 完整 fetch → 更新 MA/BOLL/MACD → 全量 render | `true` |

### 决策 5：SSE 生命周期（前端）

| 事件 | 动作 | 代码位置 |
|------|------|----------|
| `show()` 显示 K线视图 | `_connectKlineSSE()` 建立连接 | [`kline.js:611`](frontend/js/kline.js#L611) |
| `_hide()` 返回首页 | 关闭 `_klineSSE` | [`kline.js:614-621`](frontend/js/kline.js#L614-L621) |
| `switchPeriod()` 切周期 | 关闭旧 SSE → `_connectKlineSSE()` | [`kline.js:709`](frontend/js/kline.js#L709) |
| `selectCode()` 搜代码 | 关闭旧 SSE → `_connectKlineSSE()` | [`kline.js:820`](frontend/js/kline.js#L820) |
| SSE `onerror` | 5s 后自动重连 | `_connectKlineSSE` 内部 setTimeout |

---

## 架构

```
浏览器                          FastAPI 后端                腾讯 K线 API
  │                                │                          │
  │── SSE connect ────────────────>│                          │
  │   /api/stream/kline/stock/     │                          │
  │   sh600519?period=1d           │                          │
  │                                │── asyncio.to_thread ────>│
  │                                │   fetch latest 5         │
  │<── {candle: [date,O,C,H,L,V]}  │<── last candle ──────────│
  │                                │                          │
  │   ... 5s later ...             │── asyncio.to_thread ────>│
  │<── {heartbeat: true, ts}       │  (same hash → 心跳)       │
  │                                │                          │
  │   ... 5s later ...             │── asyncio.to_thread ────>│
  │<── {candle: [new date,O,... ]} │  (new candle → push)     │
  │                                │                          │
  │ kline.js onmessage:            │                          │
  │   candle → 更新 lastResp.data  │                          │
  │   最后一根 → render(无动画)    │                          │
```

---

## 实施步骤（含文件:行号）

### Step 5a：后端 SSE 端点

**文件**：[`backend/main.py`](backend/main.py)

**改动位置**：[`backend/main.py:231`](backend/main.py#L231) 之后（`kline_endpoint` 函数结束的空白行，`# ── SSE 分片推送 ──` 注释之前）

**新增代码**（~45 行）：

```python
# ── K线 SSE 实时推送（V1.7.0 Step 5）──
@app.get('/api/stream/kline/{module}/{code}')
async def stream_kline(module: str, code: str, period: str = '1d'):
    """K线 SSE：每 5s 推送最新一根蜡烛（或心跳）。
    fire-and-forget 模式：asyncio.to_thread 在线程池执行 fetch，不阻塞 event loop。
    """
    fn = KL_FN.get(module)
    if not fn:
        return StreamingResponse(
            iter(['event: error\ndata: {"error":"unknown module"}\n\n']),
            media_type='text/event-stream')

    async def gen():
        import asyncio as _aio
        last_hash = None
        while True:
            try:
                # fire-and-forget：在线程池执行 fetch，不阻塞 event loop
                rows = await _aio.to_thread(fn, code, period, 5)
                if rows and len(rows) > 0:
                    last = rows[-1]
                    h = hash(str(last))
                    if h != last_hash:
                        last_hash = h
                        yield f'data: {json.dumps({"candle": last, "ts": time.time()})}\n\n'
                    else:
                        yield f'data: {json.dumps({"heartbeat": True, "ts": time.time()})}\n\n'
                else:
                    yield f'data: {json.dumps({"heartbeat": True, "ts": time.time()})}\n\n'
            except Exception as e:
                yield f'data: {json.dumps({"error": str(e), "ts": time.time()})}\n\n'
            await _aio.sleep(5)

    return StreamingResponse(gen(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
```

**设计要点**：
- `asyncio.to_thread(fn, code, period, 5)` — fire-and-forget，不阻塞 asyncio event loop（与 [`backend/main.py:104`](backend/main.py#L104) `crypto_status` 的 `_aio.ensure_future` 同模式）
- `period` 默认 `1d`，前端切周期时重连 SSE 带新 period
- hash 比较判断蜡烛是否变化，相同则只推心跳
- SSE header 与 spot SSE（[`backend/main.py:247`](backend/main.py#L247)）完全一致

---

### Step 5b：前端 SSE 连接

**文件**：[`frontend/js/kline.js`](frontend/js/kline.js)

#### 改动 1：新增状态变量

**位置**：[`frontend/js/kline.js:54`](frontend/js/kline.js#L54)（`var _resizeHandler = null;` 之后，`// ─── 交易时段判断` 之前）

```javascript
var _klineSSE = null;        // K线 SSE EventSource
var _klineSSERetry = null;   // SSE 重连定时器
var _calibrateTimer = null;  // 30s 全量校准定时器
```

#### 改动 2：`render()` 加 animation 控制

**位置**：[`frontend/js/kline.js:565`](frontend/js/kline.js#L565)（`function render(resp)` 函数签名 + 函数体首行）

```javascript
// 改前：function render(resp) {
// 改后：
function render(resp, noAnimation) {
  if (!chart) initChart();
  if (!chart) return;
  var option = showMinute ? buildMinuteOption(resp, _yesterdayClose) : buildOption(resp);
  if (noAnimation) { option.animation = false; option.animationDuration = 0; }
  chart.setOption(option, { notMerge: true });
}
```

#### 改动 3：新增 `_connectKlineSSE()` 函数

**位置**：[`frontend/js/kline.js:710`](frontend/js/kline.js#L710) 之后（`switchPeriod()` 函数之后，`toggleMinuteLoad()` 之前）

```javascript
// ─── K线 SSE 连接（V1.7.0 Step 5）───
function _connectKlineSSE() {
  // 先关闭已有连接（防泄漏）
  if (_klineSSE) { _klineSSE.close(); _klineSSE = null; }
  if (_klineSSERetry) { clearTimeout(_klineSSERetry); _klineSSERetry = null; }

  if (!currentModule || !currentCode) return;

  var url = MV.API + '/api/stream/kline/' + currentModule + '/' + currentCode +
            '?period=' + currentPeriod;
  _klineSSE = new EventSource(url);

  _klineSSE.onmessage = function(e) {
    try {
      var msg = JSON.parse(e.data);
      if (msg.heartbeat) return;  // 心跳跳过
      if (msg.error) { console.warn('Kline SSE error:', msg.error); return; }
      if (msg.candle && lastResp && lastResp.data) {
        var candle = msg.candle;
        var data = lastResp.data;
        // 同日期 → 替换最后一根；新日期 → 追加
        if (data.length > 0 && data[data.length - 1][0] === candle[0]) {
          data[data.length - 1] = candle;
        } else {
          data.push(candle);
        }
        render(lastResp, true);  // noAnimation=true（避免每 5s 闪）
      }
    } catch(err) {}
  };

  _klineSSE.onerror = function() {
    if (_klineSSE) { _klineSSE.close(); _klineSSE = null; }
    _klineSSERetry = setTimeout(_connectKlineSSE, 5000);  // 5s 自动重连
  };
}
```

#### 改动 4：`show()` 末尾加 SSE + 30s 校准

**位置**：[`frontend/js/kline.js:611`](frontend/js/kline.js#L611)（`loadData(currentModule, code, false, name);` 之后，`show()` 函数结束 `}` 之前）

```javascript
  _connectKlineSSE();
  // 全量校准 MA/BOLL/MACD（SSE 只推蜡烛，指标需定期重算）
  // 1m 周期 60s（避免 30s 校准漏 30 根新K线），其他周期 30s
  if (_calibrateTimer) clearInterval(_calibrateTimer);
  _calibrateTimer = setInterval(function() {
    if (currentModule && currentCode && !showMinute) {
      loadData(currentModule, currentCode, true);
    }
  }, currentPeriod === '1m' ? 60000 : 30000);
```

#### 改动 5：`_hide()` 加 SSE + 定时器关闭

**位置**：[`frontend/js/kline.js:614-621`](frontend/js/kline.js#L614-L621)（`function _hide()` 函数体首部）

```javascript
function _hide() {
  // 关闭 SSE + 定时器
  if (_klineSSE) { _klineSSE.close(); _klineSSE = null; }
  if (_klineSSERetry) { clearTimeout(_klineSSERetry); _klineSSERetry = null; }
  if (_calibrateTimer) { clearInterval(_calibrateTimer); _calibrateTimer = null; }
  // 原有逻辑
  if (chart) { chart.dispose(); chart = null; }
  if (_resizeHandler) { ... }
  document.getElementById('kline-view').style.display = 'none';
}
```

#### 改动 6：`switchPeriod()` 加 SSE 重连

**位置**：[`frontend/js/kline.js:709`](frontend/js/kline.js#L709)（`loadData(currentModule, currentCode, true);` 之后，`switchPeriod()` 函数末尾）

```javascript
  _connectKlineSSE();  // 重连 SSE（period 已变）
```

注意：分时模式切换路径（`toggleMinuteLoad` 分支，[`frontend/js/kline.js:713`](frontend/js/kline.js#L713)）不需要 SSE 重连，分时图不接 SSE。

#### 改动 7：`selectCode()` 加 SSE 重连

**位置**：[`frontend/js/kline.js:820`](frontend/js/kline.js#L820)（`loadData(module, code, true, name);` 之后，`selectCode()` 函数末尾）

```javascript
  _connectKlineSSE();  // 重连 SSE（code 已变）
```

#### 改动 8：`toggleMinute()` K线→分时关闭 SSE，分时→K线开启 SSE

**位置**：[`frontend/js/kline.js:675-684`](frontend/js/kline.js#L675-L684)（`toggleMinute()` 的 `else` 分支——从分时切回 K线）

在 `loadData(currentModule, currentCode, true);` 之后加：
```javascript
  _connectKlineSSE();  // 从分时切回 K线，重连 SSE
```

**位置**：[`frontend/js/kline.js:635-638`](frontend/js/kline.js#L635-L638)（`toggleMinute()` 的 `if(showMinute)` 分支——切到分时）

在 `toggleMinuteLoad();` 调用之前加：
```javascript
  // 分时图不接 SSE
  if (_klineSSE) { _klineSSE.close(); _klineSSE = null; }
  if (_calibrateTimer) { clearInterval(_calibrateTimer); _calibrateTimer = null; }
```

---

### Step 5c：全量校准（动态间隔）

已在上方改动 4 中实现（`show()` 末尾的 `setInterval` + `_hide()` 的 `clearInterval`）。无需额外代码。行为如下：

- **K线模式**：定时全量 fetch 重算 MA/BOLL/MACD
  - 1m 周期：每 60s（1m K线每分钟产 1 根，30s 校准时前一次 fetch 的蜡烛还在 SSR 中没更新，实际只间隔 30s 拉一次 → 会漏 30 根。60s 确保至少跨过 1 根完整蜡烛）
  - 其他周期：每 30s（日K/周K/月K 等长周期不需要频繁校准）
- **分时模式**：不启动校准（分时不接 SSE，用户手动刷新）
- **返回首页**：清除校准定时器
- **SSE 推送间隙**：SSE 只更新蜡烛数据，MA/BOLL/MACD 数组不变 → 定时校准确保指标与蜡烛对齐

---

## 验收

### 后端验收

```bash
# 1. SSE 连接 + 收到数据（6s 窗口，预期收到 1~2 条 data: 行）
curl -N -m 6 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | head -10

# 2. 验证 candle 字段格式（7 元素数组：[date,O,C,H,L,V,Amt]）
curl -N -m 6 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | grep 'candle'

# 3. 验证心跳（非交易时段应收到 heartbeat）
curl -N -m 6 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | grep 'heartbeat'
```

### 前端验收

```bash
# 语法检查
node -c frontend/js/kline.js
```

| # | 操作 | 预期 |
|---|------|------|
| 1 | 交易时段打开行情 → 日K | 5s 内最后一根蜡烛高/低/收可能变化，无闪烁 |
| 2 | 切到 1m → 看 30s | 每分钟第 0 秒形成新蜡烛，SSE 推送 |
| 3 | 切换到另只股票 | SSE 自动重连到新股，旧连接关闭 |
| 4 | 点"首页"→ 再点"行情" | SSE 断开→重连，图表正常 |
| 5 | 非交易时段 | 只收心跳，蜡烛不变 |
| 6 | 切周期（1d→1w→1m） | SSE 自动重连，period 参数正确 |
| 7 | F12 Network EventStream | 持续收到 `data:` 行，无 CORS 错误 |
| 8 | F12 Network 标签 | 切到首页时 EventStream 关闭（无泄漏） |

---

## 技术文档改动范围（必填）

按 [执行者入门指南 §0.1 分工表](docs/执行者入门指南.md)，本次改动**执行者要同步更新的技术文档**：

- [ ] **`docs/API文档.md`** — 在 §9 K线接口 之后新增 §9.1 K线 SSE 实时推送：
  - 端点：`GET /api/stream/kline/{module}/{code}?period=1d`
  - SSE 消息格式：`{candle: [date,O,C,H,L,V,Amt], ts}` 或 `{heartbeat: true, ts}`
  - period 参数默认值 `1d`，支持 8 周期（1m/5m/15m/30m/60m/1d/1w/1M）
- [ ] **`docs/故障排查.md`** — 如有新坑（如 SSE 频繁断连 → 检查 Nginx `proxy_read_timeout`；K线 SSE 返回空 → 检查 period 参数是否正确）

> **设计师维护的文档**（执行者不改）：CLAUDE.md、设计师入门指南、开发手册。

---

## 风险

| # | 风险 | 应对 |
|---|------|------|
| 1 | 腾讯 K线 API 限流 | 每连接 5s 一次请求，单用户最多 ~1 QPS，远低于免费 API 阈值 |
| 2 | `notMerge: true` 每次重渲染性能 | 750 根蜡烛 setOption < 50ms，5s 间隔完全够 |
| 3 | 分钟线 mkline API 延迟（可能晚 1-2 分钟） | 非代码问题，已知限制，在故障排查文档中注明 |
| 4 | SSE 连接泄漏（切代码/周期时旧连接未关） | `_connectKlineSSE()` 开头先 close 旧连接（改动 3），双重保险 |
| 5 | 非交易时段 SSE 空转 | 心跳模式（push `{heartbeat: true}`），前端直接跳过，不消耗渲染资源 |
| 6 | 港股 2min 冷启动误以为阻塞 K线 | 已明示 fire-and-forget（见背景），K线 SSE handler 的 `asyncio.to_thread` 同样在线程池执行，不阻塞 event loop |

---

## 回滚

```bash
# 1. 回滚到上一版本
git revert <commit-hash>

# 2. 验证 K线 SSE 端点已移除（应返回 404 或无 stream_kline）
curl -s 'http://localhost:8000/openapi.json' | python3 -c "import sys,json; paths=json.load(sys.stdin).get('paths',{}); print('stream_kline' if '/api/stream/kline/{module}/{code}' in paths else 'OK: removed')"

# 3. 重启服务
sudo systemctl restart marketview

# 4. 快速验证（应 404）
curl -s -o /dev/null -w '%{http_code}' 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d'
```

回退后状态：纯手动刷新（Step 4.5 封版），K线 REST API 正常，无 SSE 实时推送。
