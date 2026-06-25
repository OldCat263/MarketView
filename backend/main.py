"""
MarketView — FastAPI 入口 V1.6.0
数据全部实时获取，零磁盘存储
分片内存缓存 + 滚动daemon刷新 + SSE推送
"""

from contextlib import asynccontextmanager
from datetime import datetime
import json, threading, time, queue
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fetcher import (crypto_status, get_crypto_json,
    get_stock_json, get_etf_json, get_hk_json, get_us_json, get_index_json,
    fetch_stock_shard, fetch_etf_shard, fetch_hk_shard,
    fetch_us_shard, fetch_index_shard, fetch_crypto_shard)

# ── 分片配置 ──
SHARD_CFG = {
    'crypto':  {'n': 1,  'interval': 5},
    'stock':   {'n': 11, 'interval': 1},
    'etf':     {'n': 5,  'interval': 3},
    'hk':      {'n': 6,  'interval': 2.5},
    'us':      {'n': 11, 'interval': 1},
    'index':   {'n': 1,  'interval': 3},
}
SHARD_FN = {
    'stock': fetch_stock_shard, 'etf': fetch_etf_shard,
    'hk': fetch_hk_shard, 'us': fetch_us_shard,
    'index': fetch_index_shard, 'crypto': fetch_crypto_shard,
}

# ── 分片缓存（纯RAM，不落盘）──
_cache = {}        # key → {'shards': {i:{'data':[],'ts':0}}, 'cols':[]}
_cache_lock = threading.Lock()
_sse_queues = {m: queue.Queue() for m in SHARD_CFG}

def _cached_get(key, fetcher_fn):
    """读缓存：合并分片返回全量；未命中拉取回填"""
    with _cache_lock:
        c = _cache.get(key)
        if c and c.get('shards'):
            data = []
            for i in sorted(c['shards'].keys()):
                data.extend(c['shards'][i].get('data', []))
            return json.dumps(data, ensure_ascii=False) if data else '[]'
    # 未命中：等滚动线程预热（不阻塞worker）
    return '[]'

def _roller(key, fetch_shard_fn):
    """滚动刷新线程：轮转每个分片"""
    cfg = SHARD_CFG[key]
    i = 0
    while True:
        try:
            data = fetch_shard_fn(i, cfg['n'])
            with _cache_lock:
                c = _cache.setdefault(key, {'shards': {}, 'cols': []})
                c['shards'][i] = {'data': data, 'ts': time.time()}
            try:
                _sse_queues[key].put_nowait({'shard': i, 'data': data, 'ts': time.time()})
            except queue.Full:
                pass
        except Exception as e:
            print(f'[{key}] shard {i} err: {e}')
        i = (i + 1) % cfg['n']
        time.sleep(cfg['interval'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    await crypto_status()
    # 启动滚动刷新线程（每模块一个）
    for m in SHARD_CFG:
        if m in SHARD_FN:
            threading.Thread(target=_roller, args=(m, SHARD_FN[m]), daemon=True).start()
    # 启动首轮全量预加载（加速首次访问）
    def _initial_load():
        for key, fn in [('stock', get_stock_json), ('etf', get_etf_json),
                        ('hk', get_hk_json), ('us', get_us_json), ('index', get_index_json)]:
            try:
                data = fn()
                with _cache_lock:
                    _cache.setdefault(key, {})
                    _cache[key]['data'] = data
                    _cache[key]['ts'] = time.time()
                print(f'[Preload] {key} OK')
            except Exception as e:
                print(f'[Preload] {key}: {e}')
    threading.Thread(target=_initial_load, daemon=True).start()
    yield

app = FastAPI(title='MarketView', version='1.6.0', docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

def _ok(json_str):
    return JSONResponse({'data': json.loads(json_str) if isinstance(json_str, str) else json_str,
                         'time': datetime.now().strftime('%H:%M:%S')})

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api/crypto/status')
async def crypto_status_endpoint(proxy: str = None):
    return JSONResponse(await crypto_status(proxy))

@app.get('/api/crypto/spot')
async def crypto_spot():
    import asyncio as _aio
    return _ok(await get_crypto_json())

@app.get('/api/stock/spot')
def stock_spot():
    return _ok(_cached_get('stock', get_stock_json))

@app.get('/api/etf/spot')
def etf_spot():
    return _ok(_cached_get('etf', get_etf_json))

@app.get('/api/hk/spot')
def hk_spot():
    return _ok(_cached_get('hk', get_hk_json))

@app.get('/api/us/spot')
def us_spot():
    return _ok(_cached_get('us', get_us_json))

@app.get('/api/index/spot')
def index_spot():
    return _ok(_cached_get('index', get_index_json))

# ── SSE 分片推送 ──
@app.get('/api/stream/{module}')
async def stream_module(module: str):
    if module not in _sse_queues:
        return StreamingResponse(iter(['event: error\ndata: unknown\n\n']), media_type='text/event-stream')
    q = _sse_queues[module]
    async def gen():
        import asyncio as _aio
        while True:
            try:
                msg = await _aio.to_thread(q.get, True, 30)
                yield f'data: {json.dumps(msg)}\n\n'
            except queue.Empty:
                yield ': ping\n\n'
    return StreamingResponse(gen(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
