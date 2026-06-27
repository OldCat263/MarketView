# MarketView API 文档

**Base URL**: `https://oldcat.site`
**响应格式**: `{"data": ..., "time": "HH:MM:SS"}`
**缓存策略**: 服务端分片内存缓存 + 滚动daemon刷新 + SSE实时推送（含 3s 心跳）；客户端 sessionStorage 15s

> **设计师注意**：修改任何接口前，请先读 [设计师入门指南 §0 同步更新规则](./设计师入门指南.md)，按流程更新本文档 + CLAUDE.md + 开发手册。
>
> **执行者注意**：实施任何接口前，请先读 [执行者入门指南 §0 同步更新规则](./执行者入门指南.md) + §8 验收清单。
>
> **审批员注意**：复审接口改动时，请按 [审批员入门指南 §6 复审清单 §1.2 字段一致性](./审批员入门指南.md) 检查字段是否与代码一致。

---

## 1. 健康检查

```
GET /api/health
```

**V1.8.6 起**：返回每模块缓存就绪状态，前端据此显示卡片明亮/半透明。

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| status | string | "ok" |
| stock | bool | A股缓存是否就绪 |
| etf | bool | ETF缓存是否就绪 |
| hk | bool | 港股缓存是否就绪 |
| us | bool | 美股缓存是否就绪 |
| index | bool | 指数缓存是否就绪 |
| crypto | bool | 加密货币缓存是否就绪 |
| news | bool | 新闻缓存是否就绪 |

---

## 2. 加密货币 — Binance

### 2.1 代理状态检测

```
GET /api/crypto/status?proxy=http://127.0.0.1:7897
```

| 参数 | 必须 | 说明 |
|------|------|------|
| proxy | 否 | 手动指定代理地址 |

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| available | bool | 代理是否可用 |
| message | string | 状态描述 |
| proxy | string\|null | 发现的代理地址 |

### 2.2 实时行情

```
GET /api/crypto/spot
```

**数据源**: Binance `api.binance.com/api/v3/ticker/24hr`
**需代理**: 是（设置 `CRYPTO_PROXY` 环境变量，或自动扫描 7897/7890/10809/10808/1080/8118/8888；无代理时返回 200 + `available: false`）

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| 交易对 | string | BTC/ETH/USDC... |
| 价格(USD) | float | 最新价 |
| 24h涨跌 | float | 涨跌幅 % |
| 24h最高 | float | 24h最高价 |
| 24h最低 | float | 24h最低价 |
| 成交量 | float | 24h成交量 |
| 成交额(USD) | float | 24h成交额 |

---

## 3. A股 — 腾讯 qt.gtimg.cn

```
GET /api/stock/spot
```

**数据源**: 腾讯 qt.gtimg.cn（优先）→ 东财 → 新浪
**缓存**: 服务端分片缓存 + 滚动刷新（~60s 首轮预热，后续毫秒级）

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| 代码 | string | 600519 |
| 名称 | string | 贵州茅台 |
| 最新价 | float | 当前价 |
| 昨收 | float | 昨日收盘 |
| 今开 | float | 今日开盘 |
| 涨跌额 | float | 价格变动 |
| 涨跌幅 | float | 涨跌幅 % |
| 最高 | float | 今日最高 |
| 最低 | float | 今日最低 |
| 成交量 | float | 成交量(手) |
| 成交额 | float | 成交额(万元) |
| 振幅 | float | 振幅 % |
| 换手率 | float | 换手率 % |
| 量比 | float | 量比 |

---

## 4. ETF — 东财 fund_etf_spot_em

```
GET /api/etf/spot
```

**数据源**: 东财 → 同花顺
**缓存**: 服务端分片缓存 + 滚动刷新

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| 代码 | string | 510050 |
| 名称 | string | 上证50ETF |
| 最新价 | float | 当前价 |
| IOPV实时估值 | float | 盘中净值 |
| 涨跌额 | float | 价格变动 |
| 涨跌幅 | float | 涨跌幅 % |
| 成交量 | float | 成交量 |
| 成交额 | float | 成交额 |
| 开盘价 | float | 今开 |
| 最高价 | float | 最高 |
| 最低价 | float | 最低 |
| 振幅 | float | 振幅 % |
| 换手率 | float | 换手率 % |
| 量比 | float | 量比 |
| 流通市值 | float | 流通市值 |
| 总市值 | float | 总市值 |

> ETF 返回 37 个字段，上表仅列常用字段

---

## 5. 港股 — 腾讯/东财/新浪

```
GET /api/hk/spot
```

**数据源**: 腾讯 → 东财 → 新浪
**缓存**: 服务端分片缓存 + 滚动刷新（首次 ~2 分钟 AkShare 冷启，后续秒级）

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| 代码 | string | 00700 |
| 名称 | string | 腾讯控股 |
| 最新价 | float | 当前价(HKD) |
| 涨跌幅 | float | 涨跌幅 % |
| 涨跌额 | float | 价格变动 |
| 成交量 | float | 成交量 |
| 成交额 | float | 成交额 |
| 最高 | float | 今日最高 |
| 最低 | float | 今日最低 |
| 今开 | float | 今日开盘 |
| 昨收 | float | 昨日收盘 |

---

## 6. 美股 — 腾讯 qt.gtimg.cn（us前缀）→ 东财 → 新浪

```
GET /api/us/spot
```

**数据源**: 腾讯 qt.gtimg.cn（us前缀，优先）→ 东财 → 新浪
**缓存**: 服务端分片缓存 + 滚动刷新（首次预热 ~8 分钟，17636 条）
**注意**: 首次启动需从 AkShare 拉取代码列表（1 天缓存），后续秒级响应

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| 代码 | string | AAPL |
| 名称 | string | 苹果 |
| 最新价 | float | 当前价(USD) |
| 涨跌幅 | float | 涨跌幅 % |
| 涨跌额 | float | 价格变动 |
| 成交量 | float | 成交量 |
| 成交额 | float | 成交额 |
| 最高 | float | 今日最高 |
| 最低 | float | 今日最低 |
| 今开 | float | 今日开盘 |
| 昨收 | float | 昨日收盘 |

---

## 7. 指数 — 东财/新浪（global 需海外网络）

```
GET /api/index/spot
```

**数据源**: 东财 → 新浪（global 字段需海外网络，限流/无代理时为空）
**缓存**: 服务端分片缓存 + 滚动刷新

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| china | array | 中国指数列表(562条) |
| global | array | 全球指数列表 |

**china 子字段**:

| 字段 | 说明 |
|------|------|
| 代码 | sh000001 |
| 名称 | 上证指数 |
| 最新价 | 当前点位 |
| 涨跌幅 | 涨跌幅 % |
| 涨跌额 | 点位变动 |
| 成交量 | 成交量 |
| 成交额 | 成交额 |

---

## 8. SSE 实时推送

### 8.1 行情实时推送

```
GET /api/stream/{module}
```

**支持的 module**: stock / etf / hk / us / index / crypto / news

**说明**: Server-Sent Events，每个分片刷新时推送增量数据。前端 EventSource 连接后自动接收 `data:` 事件，包含 `shard`（分片编号）、`data`（行列表）、`ts`（时间戳）。

**V1.6.0.6 心跳**（关键）: 后端每 3s 推一条 `{"shard": -1, "data": [], "ts": ...}` 作为心跳，客户端用其刷新 `fetchTime`，维持 liveStatus 绿点。即使数据没变化，绿点也不会变红。

**示例**:
```
data: {"shard": 0, "data": [{"代码":"sh000001","名称":"上证指数",...}], "ts": 1719345678.123}
data: {"shard": -1, "data": [], "ts": 1719345681.456}
```

**注意**: 每模块独立 SSE 通道，连接断开会自动重建（前端 EventSource 内置重连）。

**V1.8.5 多客户端广播**（关键）: `_sse_queues` 采用 per-client list 模式——每个 SSE 连接创建独立 `Queue`，roller 和数据心跳线程广播到所有连接。多标签页同时打开同一模块时，每个标签都收到实时数据更新。

### 8.2 K线实时推送（V1.7.0）

```
GET /api/stream/kline/{module}/{code}?period=1d
```

**支持**: 6 模块（stock/etf/hk/us/index/crypto）+ 8 周期（1m/5m/15m/30m/60m/1d/1w/1M）

**说明**: 每 5s 推一次当前最新 K线（仅 1 根），前端 ECharts 更新最后一根。

**示例**:
```
data: {"shard": -1, "data": [["2026-06-26", 1680, 1675, 1665, 1685, 12345, 2067890]], "ts": 1719345681.456}
```

---

## 9. K线数据（V1.7.0）

```
GET /api/kline/{module}/{code}?period=1d&count=750
```

| 参数 | 必须 | 默认 | 说明 |
|------|------|------|------|
| module | 是 | — | stock/etf/hk/us/index/crypto |
| code | 是 | — | 股票代码（带市场前缀，如 sh600519 / usAAPL / BTCUSDT）|
| period | 否 | 1d | 1m/5m/15m/30m/60m/1d/1w/1M |
| count | 否 | 750 | 拉取根数（B 中等：日 K 3年 ≈ 750 根）|

**数据源**:
- A股/ETF/指数: 腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`
- 港股: 腾讯 `appstock/app/hkfqkline/get`（主源）→ 东财 `stock_hk_hist` → 新浪 `stock_hk_spot`（兜底，V1.7.0 Step 2）
- 美股: 腾讯 `appstock/app/usfqkline/get`（us 前缀）
- 加密: Binance `/api/v3/klines`

**响应**:

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 股票代码 |
| name | string | 股票名称 |
| module | string | 模块标识 |
| period | string | 周期 |
| data | array | K线数组 `[[date, o, c, h, l, v, amt], ...]` |
| ma | object | MA5/10/20/60/120/250（纯 Python 计算）|
| boll | object | BOLL(20/2) 的 UP/MID/LOW 三轨 |
| macd | object | MACD(12/26/9) 的 DIF/DEA/HIST |
| ts | float | 时间戳 |

**data 数组列索引**（每行 7 列）：

| 索引 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0 | date | string | 日期，格式 YYYY-MM-DD |
| 1 | open | float | 开盘价 |
| 2 | close | float | 收盘价 |
| 3 | high | float | 最高价 |
| 4 | low | float | 最低价 |
| 5 | volume | float | 成交量 |
| 6 | amount | float | 成交额 |

**指标数组说明**：
- MA5/10/20/60/120/250: 简单移动平均，前 N-1 个为 `null`（如 MA5 前 4 个 null，MA250 前 249 个 null）
- BOLL(20/2): MID=MA20, UP=MID+2\*STDEV20, LOW=MID-2\*STDEV20。前 19 个为 `null`。STDEV 用样本标准差（n-1 分母）
- MACD(12/26/9): DIF=EMA12-EMA26（前 25 个 null，EMA26-1=25），DEA=EMA9(DIF)（前 33 个 null，25+9-1），HIST=(DIF-DEA)\*2

**验证命令**（6 模块全量 + 8 周期示例）：

```bash
# 6 模块日K（各 10 根）
curl -s 'http://localhost:8000/api/kline/stock/sh600519?period=1d&count=10'
curl -s 'http://localhost:8000/api/kline/etf/sh510300?period=1d&count=10'
curl -s 'http://localhost:8000/api/kline/hk/hk00700?period=1d&count=10'
curl -s 'http://localhost:8000/api/kline/us/usAAPL?period=1d&count=10'
curl -s 'http://localhost:8000/api/kline/index/sh000001?period=1d&count=10'
curl -s 'http://localhost:8000/api/kline/crypto/BTCUSDT?period=1d&count=10'

# 8 周期示例（A股 茅台）
for p in 1m 5m 15m 30m 60m 1d 1w 1M; do
  echo -n "$p: "
  curl -s "http://localhost:8000/api/kline/stock/sh600519?period=$p&count=10" | python -c "import sys,json; print(len(json.load(sys.stdin)['data']),'rows')"
done
```

**示例**（生产环境）:
```bash
curl 'https://oldcat.site/api/kline/stock/sh600519?period=1d&count=10'
```

### 9.1 K线 SSE 实时推送（V1.7.0 Step 5）

```
GET /api/stream/kline/{module}/{code}?period=1d
```

**端点**：`/api/stream/kline/{module}/{code}`

| 参数 | 必须 | 默认 | 说明 |
|------|------|------|------|
| module | 是 | — | stock/etf/hk/us/index/crypto |
| code | 是 | — | 股票代码（带市场前缀，如 sh600519）|
| period | 否 | 1d | 1m/5m/15m/30m/60m/1d/1w/1M |

**SSE 消息格式**（text/event-stream，每 5s 推送一次）：

| 字段 | 类型 | 说明 |
|------|------|------|
| candle | array | 最新一根 K线 `[date, O, C, H, L, V, Amt]`（蜡烛变化时推送）|
| heartbeat | bool | `true` 表示心跳（蜡烛无变化时推送）|
| error | string | 错误信息（fetch 异常时推送）|
| ts | float | 服务端时间戳 |

**行为**：
- 每 5s 在线程池中 fetch 最新 5 根 K线，比较最新一根 hash
- 蜡烛变化 → 推 `{candle: [date,O,C,H,L,V,Amt], ts}`
- 蜡烛不变 → 推 `{heartbeat: true, ts}`（心跳模式）
- 前端收到 candle → 更新 `lastResp.data` 最后一根 → `chart.setOption({notMerge: true}, animation: false)`
- 前端收到 heartbeat → 跳过（不渲染）
- SSE 断连 → 5s 自动重连

**验证命令**：
```bash
# SSE 连接（6s 窗口，预期收到 candle 或 heartbeat）
curl -N -m 6 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | head -10

# 心跳（10s 窗口内应 ≥ 1 个 heartbeat）
curl -N -m 10 'http://localhost:8000/api/stream/kline/stock/sh600519?period=1d' 2>&1 | grep -c heartbeat
```

---

## 10. 新闻 — 新浪财经 + 财新头条（V1.8.0+）

```
GET /api/news/spot
```

**数据源**: 新浪财经 `feed.mix.sina.com.cn`（主）→ 财新头条 `stock_news_main_cx`（备）
**缓存**: 服务端分片缓存 + 60s 滚动刷新
**数据量**: 新浪 50 条实时财经要闻（4h 窗口），主源为空时 fallback 到财新 100 条

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| datetime | string | 发布时间，格式 YYYY-MM-DD HH:MM:SS（主源有精确时间，备源为空）|
| content | string | 新闻内容（标题+摘要，格式："标题：摘要"）|
| source | string | 来源媒体（如"环球市场播报"、"财新头条"等）|

> 原设计数据源为 AKShare `js_news` → 金十数据，因当前 AKShare 版本（1.18.64）无此函数，改用新浪财经直接 HTTP + 财新头条 fallback。

### 10.1 新闻 SSE 实时推送

```
GET /api/stream/news
```

**间隔**: 每 60s 推一次全量数据（新闻滚动刷新周期），3s 心跳维持连接
**消息格式**: `{shard: 0, data: [...], ts}` / `{shard: -1, data: [], ts}`（心跳）
**前端处理**: 新闻模块无"代码"索引，SSE 推送时全量替换 `st.rows`，委托 `renderNews()` 重新渲染卡片流

**验证命令**：
```bash
# REST 接口
curl -s http://localhost:8000/api/news/spot | python -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])),'条新闻')"

# SSE 心跳（6s 窗口，预期 1~2 个心跳）
curl -N -m 6 'http://localhost:8000/api/stream/news' 2>&1 | grep -c 'shard.-1'
```

---

## 通用说明

- 所有接口返回 **中文 JSON**，字段名即中文
- 响应头 `Cache-Control: no-store`（服务端控制，客户端禁用 HTTP 缓存）
- 时间戳字段 `time` 为服务器当地时间(HH:MM:SS)
- 空数据返回 `[]` 或 `{}`
- 服务端重启后首次请求需等滚动线程预热分片，后续毫秒级响应
- **V1.8.5 起**: 启动并行预加载（6 线程），最快 10s 可访问新闻/指数/ETF；美股代码列表磁盘缓存 `.cache/us_codes.json`，重启 30s 恢复
- 加密货币需配置 `CRYPTO_PROXY` 环境变量或自动扫描代理端口
- **V1.6.0.6 起**: 行情 SSE 每 3s 心跳推 `shard: -1`，保证客户端 liveStatus 绿点不因数据静止而变红
- **V1.7.0 起**: K线 API 走 `/api/kline/{module}/{code}`，实时推送走 `/api/stream/kline/{module}/{code}`（5s 间隔推最新 K线）
- **V1.8.5 起**: SSE 多客户端广播——每个连接独立 Queue，多标签页同模块均收到实时数据
- **V1.8.6 起**: K线服务端缓存 TTL 5min，同股票同周期二次请求 < 50ms；`/api/health` 返回每模块就绪状态
- **V2.0.0 起**: 智能预测系统——6 个预测端点，详见 §11

---

## 11. 智能预测（V2.0.0）

### 11.1 完整流水线

```
GET /api/predict/analyze/{module}/{code}?period=1d&count=200&with_ai=false
```

| 参数 | 必须 | 默认 | 说明 |
|------|------|------|------|
| period | 否 | 1d | K线周期 |
| count | 否 | 200 | K线根数 |
| with_ai | 否 | false | 是否启用AI分析 |

返回: chanlun(买卖点/中枢/走势/背驰) + backtest(9指标) + score(七维) + quant_factors(10因子) + similar_setups + multi_period + AI

### 11.2 基本面

```
GET /api/fundamental/{module}/{code}
```

### 11.3 批量排行

```
GET /api/predict/rank/{module}?period=1d&limit=50
POST /api/predict/batch/{module}?pool_size=300  # 触发计算
GET /api/predict/status/{module}               # 进度
GET /api/stream/predict/{module}               # SSE
```

> 快速档(4维)<100ms, 完整档(7维+AI)~5s

---

## 相关文档

- 部署相关问题 → [部署文档](./部署文档.md)
- 故障排查 → [故障排查](./故障排查.md)
- 项目设计哲学 → [开发手册](./开发手册.md)
- 项目状态 → [CLAUDE.md](../CLAUDE.md)
- **设计师上手 / 设计稿模板** → [设计师入门指南](./设计师入门指南.md)
- **执行者上手 / 回报模板** → [执行者入门指南](./执行者入门指南.md)
- **审批员上手 / 标级模板** → [审批员入门指南](./审批员入门指南.md)
