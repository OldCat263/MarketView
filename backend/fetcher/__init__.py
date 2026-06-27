"""MarketView 数据获取层 — 每模块独立文件"""

def _safe_import(mod_name):
    """逐模块导入，单模块失败不影响其他"""
    import importlib
    try:
        return importlib.import_module('.' + mod_name, __package__)
    except Exception as e:
        print(f'[fetcher] WARN: {mod_name} import failed: {e}')
        return None

# ── 加密货币 ──
_crypto = _safe_import('crypto')
crypto_status = _crypto.status if _crypto else (lambda: {'available': False, 'message': '模块加载失败'})
get_crypto_json = _crypto.get_json if _crypto else (lambda: '[]')
fetch_crypto_shard = _crypto.fetch_shard if _crypto else (lambda i,n: [])

# ── A股 ──
_stock = _safe_import('stock')
get_stock_json = _stock.get_json if _stock else (lambda: '[]')
fetch_stock_shard = _stock.fetch_shard if _stock else (lambda i,n: [])

# ── ETF ──
_etf = _safe_import('etf')
get_etf_json = _etf.get_json if _etf else (lambda: '[]')
fetch_etf_shard = _etf.fetch_shard if _etf else (lambda i,n: [])

# ── 港股 ──
_hk = _safe_import('hk')
get_hk_json = _hk.get_json if _hk else (lambda: '[]')
fetch_hk_shard = _hk.fetch_shard if _hk else (lambda i,n: [])

# ── 美股 ──
_us = _safe_import('us')
get_us_json = _us.get_json if _us else (lambda: '[]')
fetch_us_shard = _us.fetch_shard if _us else (lambda i,n: [])

# ── 指数 ──
_index = _safe_import('index_mod')
get_index_json = _index.get_json if _index else (lambda: '[]')
fetch_index_shard = _index.fetch_shard if _index else (lambda i,n: [])

# ── 新闻（V1.8.0）──
_news = _safe_import('news')
get_news_json = _news.get_news_json if _news else (lambda: '[]')
fetch_news_shard = _news.fetch_news_shard if _news else (lambda i,n: [])
