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

## 工具

| 命令 | 作用 |
|------|------|
| `python .trae/skills/mv-validator/scripts/mv_validate.py all` | 6 模块数据量 + 核心文件 diff + 铁律自检 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py stock` | 单模块数据量 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py sse` | SSE 6 模块心跳测试 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py kline` | V1.7.0+ K线接口验证 |
| `python .trae/skills/mv-validator/scripts/mv_validate.py rules` | 铁律自检（无本地存储/无收费API/核心文件 diff）|
| `python .trae/skills/mv-validator/scripts/mv_validate.py diff` | 核心文件改动 diff（main.py/core.js/index.html）|

## 触发

- "跑验收" / "验证" / "检查模块" / 交付前

## 输出

- ✅ 全部通过 → 验收完成
- ❌ 某项失败 → 列出失败项 + 建议（参考 [故障排查](../../故障排查.md)）
