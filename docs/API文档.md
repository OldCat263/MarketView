# MarketView API 文档

**Base URL**: `https://oldcat.site`
**响应格式**: `{"data": ..., "time": "HH:MM:SS"}`
**缓存策略**: 服务端分片内存缓存 + 滚动daemon刷新 + SSE实时推送；客户端 sessionStorage 10s

---

## 1. 健康检查

```
GET /api/health
```

| 响应字段 | 类型 | 说明 |
|----------|------|------|
| status | string | "ok" |

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

## 5. 港股 — 东财/sina

```
GET /api/hk/spot
```

**数据源**: 东财 → 新浪
**缓存**: 服务端分片缓存 + 滚动刷新

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

```
GET /api/stream/{module}
```

**支持的 module**: stock / etf / hk / us / index / crypto

**说明**: Server-Sent Events，每个分片刷新时推送增量数据。前端 EventSource 连接后自动接收 `data:` 事件，包含 `shard`（分片编号）、`data`（行列表）、`ts`（时间戳）。

**示例**:
```
data: {"shard": 0, "data": [{"代码":"sh000001","名称":"上证指数",...}], "ts": 1719345678.123}
```

**注意**: 每模块独立 SSE 通道，连接断开会自动重建（前端 EventSource 内置重连）。

---

## 通用说明

- 所有接口返回 **中文 JSON**，字段名即中文
- 响应头 `Cache-Control: no-store`（服务端控制，客户端禁用 HTTP 缓存）
- 时间戳字段 `time` 为服务器当地时间(HH:MM:SS)
- 空数据返回 `[]` 或 `{}`
- 服务端重启后首次请求需等滚动线程预热分片（~1-8 分钟取决于模块），后续毫秒级响应
- 美股首次启动从 AkShare 拉取代码列表（1 天缓存），预热需 ~8 分钟
- 加密货币需配置 `CRYPTO_PROXY` 环境变量或自动扫描代理端口
