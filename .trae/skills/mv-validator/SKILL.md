---
name: "mv-validator"
description: "MarketView 验收工具。跑模块数据量检查/铁律自检/SSE 心跳验证/核心文件 diff。Invoke when user 说'跑验收/验证模块/检查'或交付前。"
---

# MarketView 验收工具

> 自动化跑 [执行者指南 §8 验收清单](../../执行者入门指南.md)
> 0 token 消耗：调脚本即可，无需 AI 介入

## 必读

| 文档 | 路径 |
|------|------|
| 执行者指南 §8 | [../../执行者入门指南.md](../../执行者入门指南.md) |
| 故障排查 | [../../故障排查.md](../../故障排查.md) |
| API 文档 | [../../API文档.md](../../API文档.md) |
| 部署文档 | [../../部署文档.md](../../部署文档.md) |

## 工具

| 命令 | 作用 |
|------|------|
| `python .trae/skills/mv-validator/scripts/mv_validate.py all` | 6 模块数据量 + SSE 心跳 + K线接口 + 铁律自检 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py modules` | 6 模块数据量（5 业务模块 + crypto 单独计）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py sse` | 6 模块 SSE 心跳测试（6s 窗口，应收 1~2 个 shard:-1）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py kline` | V1.7.0+ K线接口（6 模块 MA/BOLL/MACD）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py rules` | 铁律自检（无本地存储 / 无收费 API / 核心文件 diff）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py diff` | 等价于 rules（保留别名）|

## 触发

- "跑验收" / "验证" / "检查模块" / 交付前 / 复审时

## 必背

- 8 条铁律（脚本 check 1+3+4）
- 6 模块默认顺序：stock / etf / hk / us / index / crypto
- crypto 0 行 = 无代理 = 预期（不计入通过率）
- V1.6.0.6 心跳：每 3s 一个 `shard:-1`
- V1.6.0.8 viewTime：客户端实时时间（每秒跳）
- V1.7.0+ K线：5 个默认代码 + 8 周期

## 输出

- ✅ 全部通过 → 验收完成
- ❌ 某项失败 → 列出失败项 + 建议（参考 [故障排查](../../故障排查.md)）
