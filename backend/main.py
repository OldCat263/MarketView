"""
MarketView — FastAPI 入口
数据全部实时获取，零磁盘存储
服务端内存缓存（RAM变量，重启清空）用于加速高频读取
"""

from contextlib import asynccontextmanager
from datetime import datetime
import json, threading, time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fetcher import (crypto_status, get_crypto_json,
    get_stock_json, get_etf_json, get_hk_json, get_us_json, get_index_json)

# ── 内存缓存层（纯RAM，不落盘，不违铁律）──
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 5  # 缓存5秒，读取秒级响应

def _cached_get(key, fetcher_fn):
    """读缓存：命中返回，未命中返回空（预加载填充）"""
    with _cache_lock:
        entry = _cache.get(key)
        if entry:
            return entry['data']
    return '[]'

def _bg_refresh():
    """后台预刷新：持续更新缓存"""
    while True:
        time.sleep(CACHE_TTL)
        for key, fn in [('stock', get_stock_json), ('etf', get_etf_json),
                        ('hk', get_hk_json), ('us', get_us_json), ('index', get_index_json)]:
            try:
                data = fn()
                with _cache_lock:
                    _cache[key] = {'data': data, 'ts': time.time()}
            except Exception:
                pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    await crypto_status()  # 启动时检测代理
    # 启动时立即预加载一次，然后后台持续刷新
    def _initial_load():
        for key, fn in [('stock', get_stock_json), ('etf', get_etf_json),
                        ('hk', get_hk_json), ('us', get_us_json),
                        ('index', get_index_json)]:
            try:
                data = fn()
                with _cache_lock:
                    _cache[key] = {'data': data, 'ts': time.time()}
                print(f'[Preload] {key} OK')
            except Exception as e:
                print(f'[Preload] {key} FAIL: {e}')
    threading.Thread(target=_initial_load, daemon=True).start()
    threading.Thread(target=_bg_refresh, daemon=True).start()
    yield

app = FastAPI(title='MarketView', version='1.5.1', docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
def _ok_json_str(json_str):
    return JSONResponse({'data': json.loads(json_str), 'time': datetime.now().strftime('%H:%M:%S')})

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api/crypto/status')
async def crypto_status_endpoint(proxy: str = None):
    return JSONResponse(await crypto_status(proxy))

@app.get('/api/crypto/spot')
async def crypto_spot():
    import asyncio
    return _ok_json_str(await get_crypto_json())

@app.get('/api/stock/spot')
def stock_spot():
    """A股秒级读取：缓存5秒，首次47s，后续<0.01s"""
    return _ok_json_str(_cached_get('stock', get_stock_json))

@app.get('/api/etf/spot')
def etf_spot():
    return _ok_json_str(_cached_get('etf', get_etf_json))

@app.get('/api/hk/spot')
def hk_spot():
    return _ok_json_str(_cached_get('hk', get_hk_json))

@app.get('/api/us/spot')
def us_spot():
    return _ok_json_str(_cached_get('us', get_us_json))

@app.get('/api/index/spot')
def index_spot():
    return _ok_json_str(_cached_get('index', get_index_json))

# ── SSE 推送 ──
from fastapi.responses import StreamingResponse

@app.get('/api/stream/{module}')
async def stream_module(module: str):
    """SSE 实时推送：每5秒推送当前模块的全量数据"""
    if module not in ('stock','etf','hk','us','index','crypto'):
        return StreamingResponse(iter(['event: error\ndata: unknown\n\n']), media_type='text/event-stream')
    async def gen():
        import asyncio as _aio
        while True:
            try:
                raw = _cached_get(module, lambda: '[]')
                yield f'event: update\ndata: {raw}\n\n'
            except Exception:
                yield ': heartbeat\n\n'
            await _aio.sleep(5)
    return StreamingResponse(gen(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
