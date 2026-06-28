---
name: "mv-validator"
description: "MarketView 验收工具。跑模块数据量检查/铁律自检/SSE 心跳验证/核心文件 diff/预测端点。Invoke when user 说'跑验收/验证模块/检查'或交付前。"
---

# MarketView 验收工具

> 自动化跑 [执行者指南 §8 验收清单](../../执行者入门指南.md)
> 0 token 消耗：调脚本即可，无需 AI 介入
> **项目状态**：V2.2.7 生产错误修复（美股降级+SSE抑制+卡片就绪同步+重试退避+加密说明）— 9 模块 + 智能预测（V1.9.0+）
> V2.0+ 集成：磁盘缓存 / 首屏快照 / 错峰 / 预测加速

## 必读

| 文档 | 路径 |
|------|------|
| 执行者指南 §8 | [../../执行者入门指南.md](../../执行者入门指南.md) |
| 故障排查 | [../../故障排查.md](../../故障排查.md) |
| API 文档 | [../../API文档.md](../../API文档.md) |
| 部署文档 | [../../部署文档.md](../../部署文档.md) |
| 开发手册 §八 | [../../开发手册.md](../../开发手册.md)（V2.0+ 缓存策略）|

## 工具

| 命令 | 作用 |
|------|------|
| `python .trae/skills/mv-validator/scripts/mv_validate.py all` | 9 模块数据量 + SSE 心跳 + K线接口 + 铁律自检 + 新闻检查 + 预测端点 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py modules` | 9 模块数据量（6 业务模块 + crypto 单独计 + 新闻 + 预测）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py sse` | 9 模块 SSE 心跳测试（6s 窗口，应收 1~2 个 shard:-1）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py kline` | V1.7.0+ K线接口（6 模块 MA/BOLL/MACD）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py predict` | V2.0.0+ 智能预测端点（analyze + batch + rank + fundamental）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py rules` | 铁律自检（无本地存储 / 无收费 API / 核心文件 diff）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py diff` | 等价于 rules（保留别名）|

## 触发

- "跑验收" / "验证" / "检查模块" / 交付前 / 复审时

## 必背

- 8 条铁律（脚本 check 1+3+4）
- **9 模块**默认顺序：stock / etf / hk / us / index / crypto / news / predict / kline
- crypto 0 行 = 无代理 = 预期（不计入通过率）
- V1.6.0.6 心跳：每 3s 一个 `shard:-1`
- V1.6.0.8 viewTime：客户端实时时间（每秒跳）
- V1.7.0+ K线：5 个默认代码 + 8 周期
- V1.8.0+ 新闻：check_news（REST 50 条 + SSE）+ source 返回实际媒体名
- V1.8.6+ 健康检查：9 模块就绪状态（crypto 无代理也返 true）
- V2.0.0+ 预测：analyze 返回 chanlun/buy_points + 10 因子 + AI source 三级 fallback
- **V2.0.2+ 磁盘缓存**：验证 `.cache/spot_cache.json` 存在 + 可解析
- **V2.2.0+ 数据源**：stock/etf/index 必为东财 push2 主源（> 5000 条为正常）

## 输出

- ✅ 全部通过 → 验收完成
- ❌ 某项失败 → 列出失败项 + 建议（参考 [故障排查](../../故障排查.md)）
