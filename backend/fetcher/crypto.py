"""模块一：加密货币 — Binance 公开 API"""
import json, os, httpx

_found_proxy = None
_PROXY_PORTS = ['7897','7890','10809','10808','1080','8118','8888']
_PROXY_HOSTS = ['127.0.0.1', 'localhost']

_detect_done = False

async def status(proxy_override: str = None) -> dict:
    global _found_proxy
    if proxy_override and await _test(proxy_override):
        _found_proxy = proxy_override
        return {'available': True, 'message': '代理连接正常', 'proxy': proxy_override}
    proxy = os.environ.get('CRYPTO_PROXY')
    if proxy and await _test(proxy):
        _found_proxy = proxy
        return {'available': True, 'message': '代理连接正常', 'proxy': proxy}
    for host in _PROXY_HOSTS:
        for port in _PROXY_PORTS:
            p = f'http://{host}:{port}'
            if await _test(p):
                _found_proxy = p
                return {'available': True, 'message': f'自动发现: {p}', 'proxy': p}
    _found_proxy = None
    return {'available': False, 'message': '未检测到网络代理', 'proxy': None}

async def _test(proxy: str | None) -> bool:
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=5) as c:
            resp = await c.get('https://api.binance.com/api/v3/ping')
            return resp.status_code == 200
    except Exception as e:
        print(f'[crypto] _test err: {e}')
        return False

def fetch_shard(shard_idx, total_shards):
    import asyncio
    return json.loads(asyncio.run(get_json()))

async def get_json():
    global _found_proxy
    proxy = os.environ.get('CRYPTO_PROXY') or _found_proxy
    if not proxy or not await _test(proxy):
        await status()
        proxy = os.environ.get('CRYPTO_PROXY') or _found_proxy
    if not proxy: return '[]'
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=15) as c:
            resp = await c.get('https://api.binance.com/api/v3/ticker/24hr')
            raw = resp.json()
        usdt_pairs = [r for r in raw if r['symbol'].endswith('USDT')]
        usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        result = []
        for r in usdt_pairs:
            result.append({
                '交易对': r['symbol'].replace('USDT', ''),
                '价格(USD)': float(r['lastPrice']),
                '24h涨跌': round(float(r['priceChangePercent']), 2),
                '24h最高': float(r['highPrice']),
                '24h最低': float(r['lowPrice']),
                '成交量': float(r['volume']),
                '成交额(USD)': float(r['quoteVolume']),
            })
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        print(f'[crypto] spot err: {e}')
        return '[]'
