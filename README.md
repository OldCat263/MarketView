# MarketView — 全市场数据展示平台

一站式展示全球金融市场实时行情（A 股 / ETF / 港股 / 美股 / 指数 / 加密货币）+ K 线图。

## 特性

- ⚡ **实时**：分片 SSE 推送 + 3s 心跳，数据延迟 < 5s
- 📈 **K 线**：6 模块全支持，8 周期，MA/BOLL/MACD 指标
- 🤖 **智能预测**：缠论 + 10 因子 + 回测 + AI 分析（V2.0.1）
- 🆓 **零成本**：仅用免费公开 API（腾讯/Binance/AkShare/新浪）
- 🚫 **零存储**：纯内存 + 客户端 sessionStorage
- 📱 **响应式**：手机/平板/桌面自适应

## 按场景找文档

| 我想... | 看这个 |
|---------|--------|
| 快速了解项目 | 👉 你正在看（README） |
| 知道项目状态/版本/已完成 | [CLAUDE.md](./CLAUDE.md) |
| 写代码/改模块/遵循设计原则 | [开发手册](./docs/开发手册.md) |
| **新接手设计师 / 学习如何出方案** | **[设计师入门指南](./docs/设计师入门指南.md)** ⭐ |
| **新接手执行者 / 接收实施指令** | **[执行者入门指南](./docs/执行者入门指南.md)** ⭐ |
| **新接手审批员 / 复审 + 标级** | **[审批员入门指南](./docs/审批员入门指南.md)** ⭐ |
| 调 API/查接口字段 | [API 文档](./docs/API文档.md) |
| 部署到服务器 | [部署文档](./docs/部署文档.md) |
| 排障/找 bug/查常见问题 | [故障排查](./docs/故障排查.md) |

## 快速开始

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --workers 1
# 浏览器打开 frontend/index.html
```

## 部署

详见 [部署文档](./docs/部署文档.md)。

## 数据源

| 模块 | 数据源（优先级从左到右） |
|------|------------------------|
| A股 | 腾讯 qt.gtimg.cn → 东财 → 新浪 |
| ETF | 腾讯 qt.gtimg.cn → 东财 fund_etf_spot_em → 同花顺 |
| 港股 | 腾讯 → 东财 → 新浪 |
| 美股 | 腾讯 qt.gtimg.cn（us 前缀）→ 东财 → 新浪 |
| 指数 | 东财 → 新浪 |
| 加密 | Binance API（需 `CRYPTO_PROXY`）|
| K线 | 腾讯 K线 + Binance klines（V1.7.0+）|
| 智能预测 | 缠论 + 回测 + 10因子 + AI分析（V2.0.1+）|

## ⭐ AI Skill（按角色触发，节省 token）

4 个 Skill 在 [`.trae/skills/`](./.trae/skills/)：设计师 / 执行者 / 审批员 / 验收工具。

```bash
python .trae/skills/mv-validator/scripts/mv_validate.py all  # 一键跑 6 模块 + SSE + K线 + 铁律
```

详见 [CLAUDE.md §AI Skill](./CLAUDE.md)。

---

**版本**：V2.0.0→V2.0.1 智能预测加载加速➕MCP（已封版）/ V2.0.0 智能预测系统（缠论+10因子+AI）/ V1.9.0 P0 修复（7项）/ V1.8.6 秒开体验（5项）
