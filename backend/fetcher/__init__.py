"""MarketView 数据获取层 — 每模块独立文件"""
from . import crypto, stock, etf, hk, us, index_mod

# ── 加密货币 ──
crypto_status = crypto.status
get_crypto_json = crypto.get_json

# ── A股 ──
get_stock_json = stock.get_json

# ── ETF ──
get_etf_json = etf.get_json

# ── 港股 ──
get_hk_json = hk.get_json

# ── 美股 ──
get_us_json = us.get_json

# ── 指数 ──
get_index_json = index_mod.get_json
