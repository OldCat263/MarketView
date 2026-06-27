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
    get_news_json,
    fetch_stock_shard, fetch_etf_shard, fetch_hk_shard,
    fetch_us_shard, fetch_index_shard, fetch_crypto_shard, fetch_news_shard)
from fetcher import kline, indicators

# ── 分片配置 ──
SHARD_CFG = {
    'crypto':  {'n': 1,  'interval': 5},
    'stock':   {'n': 11, 'interval': 1},
    'etf':     {'n': 5,  'interval': 3},
    'hk':      {'n': 6,  'interval': 2.5},
    'us':      {'n': 11, 'interval': 1},
    'index':   {'n': 1,  'interval': 3},
    'news':    {'n': 1,  'interval': 60},
}
SHARD_FN = {
    'stock': fetch_stock_shard, 'etf': fetch_etf_shard,
    'hk': fetch_hk_shard, 'us': fetch_us_shard,
    'index': fetch_index_shard, 'crypto': fetch_crypto_shard,
    'news': fetch_news_shard,
}

# ── 分片缓存（纯RAM，不落盘）──
_cache = {}        # key → {'shards': {i:{'data':[],'ts':0}}, 'cols':[]}
_cache_lock = threading.Lock()
_sse_queues = {m: [] for m in SHARD_CFG}  # list of per-client queues
_sse_lock = threading.Lock()
_kline_cache = {}
_kline_lock = threading.Lock()

def _cached_get(key):
    """读缓存：合并分片返回全量；支持 list 和 dict 两种数据结构"""
    with _cache_lock:
        c = _cache.get(key)
        if c and c.get('shards'):
            # 取第一个非空 shard 判断数据类型
            first = None
            for i in sorted(c['shards'].keys()):
                d = c['shards'][i].get('data')
                if d is not None and d != []:
                    first = d
                    break
            if first is None:
                return '[]'
            if isinstance(first, dict):
                # dict 数据（如 index china/global）— 返回 shard 0 完整结构
                for i in sorted(c['shards'].keys()):
                    sd = c['shards'][i].get('data')
                    if isinstance(sd, dict) and sd:
                        return json.dumps(sd, ensure_ascii=False)
                return '{}'
            # list 数据 — 合并所有分片
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
    print(f'[roller] {key} thread started, shards={cfg["n"]}, interval={cfg["interval"]}s')
    while True:
        try:
            data = fetch_shard_fn(i, cfg['n'])
            with _cache_lock:
                c = _cache.setdefault(key, {'shards': {}, 'cols': []})
                c['shards'][i] = {'data': data, 'ts': time.time()}
            with _sse_lock:
                for q in _sse_queues[key]:
                    try:
                        q.put_nowait({'shard': i, 'data': data, 'ts': time.time()})
                    except queue.Full:
                        pass
        except Exception as e:
            print(f'[{key}] shard {i} err: {e}')
        i = (i + 1) % cfg['n']
        time.sleep(cfg['interval'])

def _heartbeat(key, interval=3):
    """心跳推送：每 interval 秒推 {shard:-1} 维持客户端活性显示"""
    print(f'[heartbeat] {key} started, interval={interval}s')
    while True:
        try:
            time.sleep(interval)
            with _sse_lock:
                for q in _sse_queues[key]:
                    try:
                        q.put_nowait({'shard': -1, 'data': [], 'ts': time.time()})
                    except queue.Full:
                        pass
        except Exception as e:
            print(f'[heartbeat] {key}: {e}')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('[lifespan] start')
    # fire-and-forget：代理检测不阻塞启动（crypto 模块首次请求时也会自检）
    import asyncio as _aio
    _aio.ensure_future(crypto_status())
    print('[lifespan] crypto_status dispatched (non-blocking)')
    # 启动滚动刷新线程（每模块一个）
    for m in SHARD_CFG:
        if m in SHARD_FN:
            print(f'[lifespan] starting roller: {m}')
            try:
                threading.Thread(target=_roller, args=(m, SHARD_FN[m]), daemon=True).start()
                print(f'[lifespan] roller {m} started OK')
            except Exception as e:
                print(f'[lifespan] roller {m} FAIL: {e}')
    # 启动心跳推送线程（每模块一个）
    for m in SHARD_CFG:
        try:
            threading.Thread(target=_heartbeat, args=(m,), daemon=True).start()
            print(f'[lifespan] heartbeat {m} started')
        except Exception as e:
            print(f'[lifespan] heartbeat {m} FAIL: {e}')
    # 启动首轮全量预加载（加速首次访问）— 并行拉取，写分片 schema 与 _cached_get 一致
    def _initial_load():
        import concurrent.futures
        def _load_one(key, fn):
            try:
                raw = fn()
                data = json.loads(raw) if isinstance(raw, str) else raw
                n = SHARD_CFG[key]['n']
                if isinstance(data, list) and not data:
                    print(f'[Preload] {key} empty, skipped')
                    return
                if isinstance(data, dict) and not data:
                    print(f'[Preload] {key} empty dict, skipped')
                    return
                with _cache_lock:
                    c = _cache.setdefault(key, {'shards': {}, 'cols': []})
                    if isinstance(data, list):
                        chunk = max(1, len(data) // n)
                        for i in range(n):
                            shard_data = data[i*chunk:(i+1)*chunk] if i < n-1 else data[i*chunk:]
                            c['shards'][i] = {'data': shard_data, 'ts': time.time()}
                    else:
                        c['shards'][0] = {'data': data, 'ts': time.time()}
                print(f'[Preload] {key} OK')
            except Exception as e:
                print(f'[Preload] {key}: {e}')

        modules = [
            ('news', get_news_json),
            ('index', get_index_json),
            ('etf', get_etf_json),       # 小模块优先
            ('hk', get_hk_json),
            ('stock', get_stock_json),
            ('us', get_us_json),         # 大模块最后
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(_load_one, key, fn): key for key, fn in modules}
            concurrent.futures.wait(futures)

        # V1.8.6: 并行预加载完成后写首屏快照（wait 之后确保 6 模块全部就绪）
        def _write_snapshot():
            import os
            snapshot = {}
            for key in SHARD_CFG:
                data = _cached_get(key)
                if data != '[]' and data != '{}':
                    snapshot[key] = json.loads(data)
            snapshot['ts'] = time.time()
            snapshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'snapshot.json')
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False)
            print('[snapshot] updated')
        _write_snapshot()
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
    return _ok(_cached_get('stock'))

@app.get('/api/etf/spot')
def etf_spot():
    return _ok(_cached_get('etf'))

@app.get('/api/hk/spot')
def hk_spot():
    return _ok(_cached_get('hk'))

@app.get('/api/us/spot')
def us_spot():
    return _ok(_cached_get('us'))

@app.get('/api/index/spot')
def index_spot():
    return _ok(_cached_get('index'))

@app.get('/api/news/spot')
def news_spot():
    return _ok(_cached_get('news'))

# ── K线（V1.7.0）──
KL_FN = {
    'stock': kline.fetch_kline_stock, 'etf': kline.fetch_kline_etf,
    'hk': kline.fetch_kline_hk, 'us': kline.fetch_kline_us,
    'index': kline.fetch_kline_index, 'crypto': kline.fetch_kline_crypto,
}

KL_NAMES = {
    'stock': ('sh600519', '贵州茅台'), 'etf': ('sh510300', '沪深300ETF'),
    'hk': ('hk00700', '腾讯控股'), 'us': ('usAAPL', '苹果'),
    'index': ('sh000001', '上证指数'), 'crypto': ('BTCUSDT', 'BTC/USDT'),
}

@app.get('/api/kline/{module}/{code}')
def kline_endpoint(module: str, code: str, period: str = '1d', count: int = 750):
    cache_key = f'{module}_{code}_{period}_{count}'
    # 读缓存（5min TTL）
    with _kline_lock:
        cached = _kline_cache.get(cache_key)
        if cached and time.time() - cached['ts'] < 300:
            return JSONResponse(cached['data'])
    # 未命中 → 正常计算
    fn = KL_FN.get(module)
    if not fn:
        return JSONResponse({'error': f'unknown module: {module}'}, status_code=404)
    try:
        rows = fn(code, period, count)
        if not rows:
            return JSONResponse({'data': [], 'ma': {}, 'boll': {}, 'macd': {}, 'ts': time.time()})
        closes = [r[2] for r in rows]  # 收盘价列
        ma = indicators.calc_ma(closes)
        boll = indicators.calc_boll(closes)
        macd = indicators.calc_macd(closes)
        # 推断 name
        name = ''
        for key, (def_code, def_name) in KL_NAMES.items():
            if key == module:
                name = def_name
                break
        resp_data = {
            'code': code, 'name': name, 'module': module, 'period': period,
            'data': rows, 'ma': ma, 'boll': boll, 'macd': macd, 'ts': time.time(),
        }
        # 写缓存
        with _kline_lock:
            _kline_cache[cache_key] = {'data': resp_data, 'ts': time.time()}
        return JSONResponse(resp_data)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

# ── K线 SSE 实时推送（V1.7.0 Step 5）──
@app.get('/api/stream/kline/{module}/{code}')
async def stream_kline(module: str, code: str, period: str = '1d'):
    """K线 SSE：每 5s 推送最新一根蜡烛（或心跳）。
    fire-and-forget 模式：asyncio.to_thread 在线程池执行 fetch，不阻塞 event loop。
    """
    fn = KL_FN.get(module)
    if not fn:
        return JSONResponse({'error': f'unknown module: {module}'}, status_code=404)

    async def gen():
        import asyncio as _aio
        last_hash = None
        while True:
            try:
                # fire-and-forget：在线程池执行 fetch，不阻塞 event loop
                rows = await _aio.to_thread(fn, code, period, 5)
                if rows and len(rows) > 0:
                    last = rows[-1]
                    h = hash(str(last))
                    if h != last_hash:
                        last_hash = h
                        yield f'data: {json.dumps({"candle": last, "ts": time.time()})}\n\n'
                    else:
                        yield f'data: {json.dumps({"heartbeat": True, "ts": time.time()})}\n\n'
                else:
                    yield f'data: {json.dumps({"heartbeat": True, "ts": time.time()})}\n\n'
            except Exception as e:
                yield f'data: {json.dumps({"error": str(e), "ts": time.time()})}\n\n'
            await _aio.sleep(5)

    return StreamingResponse(gen(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

# ── SSE 分片推送 ──
@app.get('/api/stream/{module}')
async def stream_module(module: str):
    if module not in _sse_queues:
        return StreamingResponse(iter(['event: error\ndata: unknown\n\n']), media_type='text/event-stream')
    async def gen():
        import asyncio as _aio
        q = queue.Queue(maxsize=50)
        with _sse_lock:
            _sse_queues[module].append(q)
        try:
            while True:
                try:
                    msg = await _aio.to_thread(q.get, True, 30)
                    yield f'data: {json.dumps(msg)}\n\n'
                except queue.Empty:
                    yield ': ping\n\n'
        finally:
            with _sse_lock:
                _sse_queues[module].remove(q)
    return StreamingResponse(gen(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
