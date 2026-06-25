"""MarketView 数据获取层 — 每模块独立文件"""
from . import crypto, stock, etf, hk, us, index_mod

# ── 加密货币 ──
crypto_status = crypto.status
get_crypto_json = crypto.get_json
fetch_crypto_shard = crypto.fetch_shard

# ── A股 ──
get_stock_json = stock.get_json
fetch_stock_shard = stock.fetch_shard

# ── ETF ──
get_etf_json = etf.get_json
fetch_etf_shard = etf.fetch_shard

# ── 港股 ──
get_hk_json = hk.get_json
fetch_hk_shard = hk.fetch_shard

# ── 美股 ──
get_us_json = us.get_json
fetch_us_shard = us.fetch_shard

# ── 指数 ──
get_index_json = index_mod.get_json
fetch_index_shard = index_mod.fetch_shard
