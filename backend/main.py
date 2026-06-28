"""
MarketView — FastAPI 入口 V2.0.2
数据全部来自免费公开 API（腾讯/Binance/新浪）
内存/磁盘缓存仅用于性能优化，非主数据源
分片内存缓存 + 滚动daemon刷新 + SSE推送 + 磁盘持久化缓存（V2.0.2）
"""

from contextlib import asynccontextmanager
from datetime import datetime
import json, threading, time, queue, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fetcher import (crypto_status, get_crypto_json,
    get_stock_json, get_etf_json, get_hk_json, get_us_json, get_index_json,
    get_news_json,
    fetch_stock_shard, fetch_etf_shard, fetch_hk_shard,
    fetch_us_shard, fetch_index_shard, fetch_crypto_shard, fetch_news_shard)
from fetcher import kline, indicators
from fetcher import chanlun, backtest, scorer, fundamentals, ai_analyzer

# ── 分片配置 ──
SHARD_CFG = {
    # V2.0.3 分时错峰：start_delay 秒后再启动 roller，避免冷启动全挤
    'crypto':  {'n': 1,  'interval': 5,   'start_delay': 0},
    'stock':   {'n': 8,  'interval': 5,   'start_delay': 0},    # V2.2.0 东财 push2 8 片/5s
    'etf':     {'n': 5,  'interval': 5,   'start_delay': 5},    # 5s 后启动
    'hk':      {'n': 6,  'interval': 5,   'start_delay': 10},   # 10s 后
    'us':      {'n': 3,  'interval': 5,   'start_delay': 15},   # V2.1.0: 腾讯 3 片/5s（150只/50=3批）
    'index':   {'n': 1,  'interval': 5,   'start_delay': 20},
    'news':    {'n': 1,  'interval': 60,  'start_delay': 0},
    'predict': {'n': 1,  'interval': 300, 'start_delay': 45},  # 5min，等前面跑完
}
SHARD_FN = {
    'stock': fetch_stock_shard, 'etf': fetch_etf_shard,
    'hk': fetch_hk_shard, 'us': fetch_us_shard,
    'index': fetch_index_shard, 'crypto': fetch_crypto_shard,
    'news': fetch_news_shard,
}

# ── 分片缓存（V2.0.2: 启动时从磁盘恢复）──
_cache = {}        # key → {'shards': {i:{'data':[],'ts':0}}, 'cols':[]}
_cache_lock = threading.Lock()
_sse_queues = {m: [] for m in SHARD_CFG}  # list of per-client queues
_sse_lock = threading.Lock()
# V2.0.2: 磁盘持久化缓存路径
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
_SPOT_CACHE_FILE = os.path.join(_CACHE_DIR, 'spot_cache.json')
_WATCHLIST_FILE = os.path.join(_CACHE_DIR, 'watchlist.json')  # V2.0.3 自选列表
# V2.0.1: 共享 K 线缓存（从 utils.py 绝对导入，与 scorer 共用）
# V2.0.2: 改用 set_kline_cache / get_kline_cache（含磁盘持久化 + LRU）
# 注意：用绝对导入（非 .fetcher），因为 uvicorn 把 main 当 __main__ 运行
from fetcher.utils import get_kline_cache, set_kline_cache

# V2.0.1-hotfix: spot 代码转 K线前缀（腾讯 API 需 sh/sz/hk/us 前缀）
_CODE_PREFIX = {
    'stock': lambda c: _stock_prefix(c),
    'etf':   lambda c: _stock_prefix(c),
    'hk':    lambda c: 'hk' + c if not c.startswith('hk') else c,
    'us':    lambda c: 'us' + c if not c.startswith('us') else c,
    'index': lambda c: 'sh' + c if c.isdigit() else c,
}


def _load_cache():
    """V2.0.2: 从磁盘加载 spot 缓存 + predict 缓存（启动时调用一次）"""
    try:
        if os.path.exists(_SPOT_CACHE_FILE):
            with open(_SPOT_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 恢复 spot 缓存（JSON keys 变字符串，转换回 int）
            for key in ('stock', 'etf', 'hk', 'us', 'index', 'news'):
                if key in data:
                    mod = data[key]
                    # 修复 JSON 序列化后 shard key 从 int → str
                    if 'shards' in mod:
                        mod['shards'] = {int(k): v for k, v in mod['shards'].items()}
                    _cache[key] = mod
            # 恢复 predict 缓存
            if 'predict' in data:
                for pk, pv in data['predict'].items():
                    _predict_cache[pk] = pv
                # 恢复 predict_status（显示 done 而非 not started）
                for pk in data['predict']:
                    _predict_status[pk] = {'progress': 0, 'total': 0, 'status': 'done'}
            print(f'[cache] loaded {len(data)} modules from disk ({_SPOT_CACHE_FILE})', flush=True)
    except (json.JSONDecodeError, Exception) as e:
        print(f'[cache] load failed (fallback to empty): {e}', flush=True)

def _save_cache():
    """V2.0.2: 序列化 _cache + _predict_cache 到磁盘（原子写入）"""
    try:
        data = {}
        with _cache_lock:  # shallow copy 后释放锁
            for key in ('stock', 'etf', 'hk', 'us', 'index', 'news'):
                if key in _cache:
                    data[key] = _cache[key]
        with _predict_lock:  # shallow copy predict
            predict_data = dict(_predict_cache)
        data['predict'] = predict_data
        data['ts'] = time.time()
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _SPOT_CACHE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, _SPOT_CACHE_FILE)
    except Exception as e:
        print(f'[cache] save error: {e}', flush=True)

def _save_cache_task():
    """V2.0.2: 每 30s dump 一次磁盘"""
    while True:
        time.sleep(30)
        _save_cache()

def _get_codes_from_cache(module, pool_size=50):
    """V2.0.2: 从 spot 缓存取代码列表（复用 _do_batch 的逻辑）"""
    raw = _cached_get(module)
    if raw == '[]' or raw == '{}':
        return []
    spot_data = json.loads(raw)
    items = spot_data.get('data', spot_data) if isinstance(spot_data, dict) else spot_data
    codes = []
    if isinstance(items, list):
        for r in items[:pool_size]:
            if not isinstance(r, dict):
                continue
            c = r.get('代码', r.get('交易对', ''))
            if c:
                pf = _CODE_PREFIX.get(module)
                codes.append(pf(c) if pf else c)
    return codes

def _load_watchlist():
    """V2.0.3: 加载自选列表"""
    try:
        if os.path.exists(_WATCHLIST_FILE):
            with open(_WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {'stock': [], 'etf': [], 'index': []}

def _save_watchlist(wl):
    """V2.0.3: 持久化自选列表"""
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp = _WATCHLIST_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(wl, f, ensure_ascii=False)
        os.replace(tmp, _WATCHLIST_FILE)
    except Exception as e:
        print(f'[watchlist] save err: {e}', flush=True)

# 全局自选列表
_watchlist = {}

# V2.0.3: daemon 启动信号（stock+etf preload 完成后触发）
_predict_ready = threading.Event()

def _predict_daemon():
    """V2.0.2+BUG10: 独立线程，等 stock+etf 就绪即启动，5min 重算。
    优先用自选列表，无自选则取缓存前 20 只。从内存缓存读代码列表（roller 已拉完 spot），不重复调 akshare。"""
    global _watchlist
    _watchlist = _load_watchlist()
    print('[predict_daemon] waiting for stock+etf preload...', flush=True)
    _predict_ready.wait()  # 等 _initial_load 调用 _predict_ready.set()
    print('[predict_daemon] stock+etf ready, starting', flush=True)
    while True:
        for m in ('stock', 'etf'):
            try:
                # V2.2.0: 只预测 stock+etf（不再预测 index）
                # 从 roller 已写好的内存缓存读代码（不调 fetcher，0 akshare 竞争）
                spot = _cached_get(m)
                data = json.loads(spot) if isinstance(spot, str) else spot
                codes = []
                if isinstance(data, list):
                    # 直接列表格式（stock/etf 合并后）
                    codes = [r.get('代码','') for r in data[:50] if isinstance(r, dict) and r.get('代码')]
                else:
                    items = data if isinstance(data, list) else data.get('shards', {})
                    if not isinstance(items, list):
                        # shards 格式: {'0': {'data': [...]}, '1': {'data': [...]}}
                        for sdata in items.values():
                            sd = sdata.get('data', []) if isinstance(sdata, dict) else []
                            for r in sd:
                                if isinstance(r, dict):
                                    c = r.get('代码','') or r.get('交易对','')
                                    if c:
                                        pf = _CODE_PREFIX.get(m)
                                        codes.append(pf(c) if pf else c)
                            if len(codes) >= 50:
                                break
                if not codes:
                    # V2.0.3: 优先用自选列表
                    codes_wl = _watchlist.get(m, [])
                    if codes_wl:
                        codes = codes_wl[:50]
                        print(f'[predict_daemon] {m} using watchlist: {len(codes)} codes', flush=True)
                    else:
                        print(f'[predict_daemon] {m} no codes in cache, skip', flush=True)
                        continue
                cache_key = f'rank_{m}_1d'
                results = scorer.rank_batch(m, codes, '1d', 'quick', max_workers=5)
                with _predict_lock:
                    _predict_cache[cache_key] = {'data': results, 'ts': time.time()}
                _predict_status[cache_key] = {'progress': len(results), 'total': len(codes), 'status': 'done'}
                with _sse_lock:
                    for q in _sse_queues.get('predict', []):
                        try:
                            q.put_nowait({'type': 'rank_update', 'data': results[:50], 'ts': time.time()})
                        except queue.Full:
                            pass
                print(f'[predict_daemon] {m} done: {len(results)} items', flush=True)
            except Exception as e:
                import traceback
                print(f'[predict_daemon] {m} error: {e}', flush=True)
                traceback.print_exc()
        _save_cache()
        time.sleep(300)  # 5min


def _stock_prefix(code):
    """A股代码前缀：bj（北交所92xx）/ sh（5xxx、6xxx）/ sz（其他）"""
    if not code or not code.isdigit():
        return code
    if code[:2] == '92':
        return 'bj' + code
    if code[0] in ('5', '6'):
        return 'sh' + code
    return 'sz' + code

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

def _roller(key, fetch_shard_fn, start_delay=0):
    """滚动刷新线程：轮转每个分片"""
    cfg = SHARD_CFG[key]
    if start_delay > 0:
        print(f'[roller] {key} waiting {start_delay}s before first fetch...')
        time.sleep(start_delay)
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
    # V2.0.2: 从磁盘恢复缓存（在 rollers 启动前）
    _load_cache()
    # V2.0.2: 启动磁盘持久化 daemon（每 30s dump）
    threading.Thread(target=_save_cache_task, daemon=True).start()
    # V2.0.2: 启动 predict daemon（延迟 30s，5min 重算）
    threading.Thread(target=_predict_daemon, daemon=True).start()
    # fire-and-forget：代理检测不阻塞启动（crypto 模块首次请求时也会自检）
    import asyncio as _aio
    _aio.ensure_future(crypto_status())
    print('[lifespan] crypto_status dispatched (non-blocking)')
    # 启动滚动刷新线程（每模块一个，分时错峰）
    for m in SHARD_CFG:
        if m in SHARD_FN:
            delay = SHARD_CFG[m].get('start_delay', 0)
            print(f'[lifespan] starting roller: {m} (delay={delay}s)')
            try:
                threading.Thread(target=_roller, args=(m, SHARD_FN[m], delay), daemon=True).start()
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
        def _load_one(key, fn):
            try:
                # V2.0.1-hotfix: crypto 是 async，跳过预加载（roller 5s 内覆盖）
                if key == 'crypto':
                    return
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
            ('stock', get_stock_json),
            ('etf', get_etf_json),
            # ↑ predict daemon 等 etf 加载完成即触发，不等待后续模块
            ('hk', get_hk_json),
            ('news', get_news_json),
            ('us', get_us_json),
            ('index', get_index_json),
        ]
        # V2.0.3 分时错峰：串行预加载，stock→etf→predict触发→后续模块
        for key, fn in modules:
            _load_one(key, fn)
            # etf 加载完成后通知 daemon 可以开始打分
            if key == 'etf':
                _predict_ready.set()
                print('[Preload] stock+etf done, predict daemon notified', flush=True)

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
    status = {'status': 'ok'}
    for key in SHARD_CFG:
        data = _cached_get(key)
        status[key] = (data != '[]' and data != '{}')
    return status

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
    cache_key = f'{module}_{code}_{period}'  # V2.0.2: 不含 count，不同 count 请求共享缓存
    # 读缓存（5min TTL）
    cached = get_kline_cache(cache_key)
    if cached and time.time() - cached['ts'] < 300:
        # 缓存中有数据，取所需数量返回（count 可能不同）
        resp = cached['data']
        if 'data' in resp and len(resp['data']) > count:
            resp = dict(resp)
            resp['data'] = resp['data'][-count:]
        return JSONResponse(resp)
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
        # 写缓存（V2.0.2: 内存+磁盘，含 LRU）
        set_kline_cache(cache_key, {'data': resp_data, 'ts': time.time()})
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

# ── V1.9.0 智能预测 API ──

_predict_cache = {}
_predict_lock = threading.Lock()
_predict_status = {}


@app.get('/api/predict/analyze/{module}/{code}')
def predict_analyze(module: str, code: str, period: str = '1d', count: int = 100, with_ai: bool = False):
    """完整流水线单票分析。GET /api/predict/analyze/stock/sh600519?with_ai=true"""
    fn = KL_FN.get(module)
    if not fn:
        return JSONResponse({'error': f'unknown module: {module}'}, status_code=404)
    try:
        rows = fn(code, period, count)
        if not rows or len(rows) < 30:
            return JSONResponse({'error': 'insufficient K-line data'}, status_code=400)
        mode = 'full' if with_ai else 'quick'
        result = scorer.score_single(module, code, rows, period, mode)
        if with_ai:
            result['ai'] = ai_analyzer.analyze(result)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.get('/api/fundamental/{module}/{code}')
def fundamental_endpoint(module: str, code: str):
    """基本面数据。GET /api/fundamental/stock/sh600519"""
    data = fundamentals.get_fundamentals(module, code)
    return JSONResponse(data)


@app.get('/api/predict/rank/{module}')
def predict_rank(module: str, period: str = '1d', limit: int = 50):
    """读缓存排行。GET /api/predict/rank/stock?limit=50"""
    cache_key = f'rank_{module}_{period}'
    with _predict_lock:
        cached = _predict_cache.get(cache_key)
    if cached:
        data = cached['data'][:limit]
        return JSONResponse({'data': data, 'cached_at': cached['ts'], 'ts': time.time()})
    return JSONResponse({'data': [], 'message': 'no cached rank, POST /api/predict/batch first'})

# ── V2.0.3 自选列表 API ──

@app.get('/api/watchlist')
def get_watchlist():
    """获取自选列表"""
    return JSONResponse(_watchlist)

@app.post('/api/watchlist/{module}/{code}')
def add_watchlist(module: str, code: str):
    """添加自选 POST /api/watchlist/stock/sh600519"""
    global _watchlist
    if module not in _watchlist:
        _watchlist[module] = []
    if code not in _watchlist[module]:
        _watchlist[module].append(code)
        _save_watchlist(_watchlist)
    return JSONResponse({'ok': True, 'watchlist': _watchlist})

@app.delete('/api/watchlist/{module}/{code}')
def del_watchlist(module: str, code: str):
    """删除自选 DELETE /api/watchlist/stock/sh600519"""
    global _watchlist
    if module in _watchlist and code in _watchlist[module]:
        _watchlist[module].remove(code)
        _save_watchlist(_watchlist)
    return JSONResponse({'ok': True, 'watchlist': _watchlist})


@app.post('/api/predict/batch/{module}')
def predict_batch(module: str, period: str = '1d', pool_size: int = 200):
    """触发批量计算。POST /api/predict/batch/stock?pool_size=200"""
    import concurrent.futures
    cache_key = f'rank_{module}_{period}'
    _predict_status[cache_key] = {'progress': 0, 'total': min(pool_size, 200), 'status': 'running'}

    def _do_batch():
        try:
            # 从 spot 缓存取代码列表
            raw = _cached_get(module)
            if raw == '[]':
                _predict_status[cache_key] = {'progress': 0, 'total': 0, 'status': 'no_data'}
                return
            spot_data = json.loads(raw)
            # V2.0.1-hotfix: _cached_get 返回裸 JSON 字符串，json.loads 后为 list（stock/etf/hk/us）或 dict（index）
            # index 模块返回 {'china': [...], 'global': [...]} → isinstance(list)=False → 跳过
            items = spot_data.get('data', spot_data) if isinstance(spot_data, dict) else spot_data
            codes = []
            if isinstance(items, list):
                for r in items[:pool_size]:
                    if not isinstance(r, dict):
                        continue
                    c = r.get('代码', r.get('交易对', ''))
                    if c:
                        pf = _CODE_PREFIX.get(module)
                        codes.append(pf(c) if pf else c)
            print(f'[batch/{module}] codes={len(codes)} items_type={type(items).__name__}', flush=True)
            results = scorer.rank_batch(module, codes, period, 'quick', max_workers=5) if codes else []
            with _predict_lock:
                _predict_cache[cache_key] = {'data': results, 'ts': time.time()}
            _predict_status[cache_key] = {'progress': len(results), 'total': len(codes), 'status': 'done'}

            # SSE 推送
            with _sse_lock:
                for q in _sse_queues.get('predict', []):
                    try:
                        q.put_nowait({'type': 'rank_update', 'data': results[:50], 'ts': time.time()})
                    except queue.Full:
                        pass
        except Exception as e:
            _predict_status[cache_key] = {'progress': 0, 'total': 0, 'status': f'error: {e}'}

    threading.Thread(target=_do_batch, daemon=True).start()
    return JSONResponse({'message': 'batch started', 'cache_key': cache_key})


@app.get('/api/predict/status/{module}')
def predict_status(module: str, period: str = '1d'):
    """批量进度。GET /api/predict/status/stock"""
    cache_key = f'rank_{module}_{period}'
    return JSONResponse(_predict_status.get(cache_key, {'status': 'not started'}))


@app.get('/api/stream/predict/{module}')
async def stream_predict(module: str):
    """预测 SSE 推送。GET /api/stream/predict/stock"""
    async def gen():
        import asyncio as _aio
        q = queue.Queue(maxsize=50)
        with _sse_lock:
            _sse_queues.setdefault('predict', []).append(q)
        try:
            while True:
                try:
                    msg = await _aio.to_thread(q.get, True, 30)
                    yield f'data: {json.dumps(msg)}\n\n'
                except queue.Empty:
                    yield ': ping\n\n'
        finally:
            with _sse_lock:
                if q in _sse_queues.get('predict', []):
                    _sse_queues['predict'].remove(q)
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
