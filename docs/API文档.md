# MarketView API 文档

**Base URL**: `https://oldcat.site`
**响应格式**: `{"data": ..., "time": "HH:MM:SS"}`
**缓存策略**: 服务端 RAM 缓存 5s + 客户端 sessionStorage 15s

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
**需代理**: 是（自动扫描 7897/7890/10809/10808/1080/8118/8888）

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
**缓存**: 服务端 5s，首次 47s，后续 2s

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
**缓存**: 服务端 5s，首次 57s，后续 <1s

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
**缓存**: 服务端 5s

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

## 6. 美股 — 东财/sina

```
GET /api/us/spot
```

**数据源**: 东财 → 新浪
**缓存**: 服务端 5s

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

## 7. 指数 — 东财/sina

```
GET /api/index/spot
```

**数据源**: 东财 → 新浪
**缓存**: 服务端 5s

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

## 通用说明

- 所有接口返回 **中文 JSON**，字段名即中文
- 响应头 `Cache-Control: no-store`（服务端控制，客户端禁用 HTTP 缓存）
- 时间戳字段 `time` 为服务器当地时间(HH:MM:SS)
- 空数据返回 `[]` 或 `{}`
- 服务端重启后首次请求较慢（需重建缓存），后续毫秒级响应
