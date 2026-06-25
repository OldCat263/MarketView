# MarketView — 全市场数据展示平台

一站式展示全球金融市场实时数据。

## 快速开始

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --workers 1
# 浏览器打开 frontend/index.html
```

## 模块

| 模块 | 数据源 |
|------|--------|
| 加密货币 | Binance（需代理，设 CRYPTO_PROXY）|
| A股 | 腾讯 qt.gtimg.cn → 东财 → 新浪 |
| ETF | 东财 → 同花顺 |
| 港股 | 东财 → 新浪 |
| 美股 | 腾讯 → 东财 → 新浪 |
| 指数 | 新浪 |

## 部署

```bash
# 服务端
cp marketview.service /etc/systemd/system/
systemctl enable --now marketview

# nginx（需配 SSE 关闭缓冲）
# proxy_buffering off;
# proxy_read_timeout 86400s;
```

详见 `docs/API文档.md` 和 `CLAUDE.md`。
