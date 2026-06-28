"""工具函数：安全转换 + DataFrame处理 + fallback + 分片 + 共享K线缓存（V2.0.2）"""
import json, time, logging, threading, os

_log = logging.getLogger('marketview')

def _safe_float(value) -> float:
    try: return float(value) if value else 0.0
    except (ValueError, TypeError): return 0.0

def _to_records(df) -> list:
    if df is None or len(df) == 0: return []
    for col in df.columns:
        d = str(df[col].dtype)
        if any(k in d for k in ('datetime', 'timestamp', 'period', 'timedelta')):
            df[col] = df[col].astype(str)
        elif d == 'object' or d == 'str':
            df[col] = df[col].fillna('')
        else:
            df[col] = df[col].fillna(0)
    return df.to_dict('records')

def _to_json(df) -> str:
    return json.dumps(_to_records(df), ensure_ascii=False)


# ── O1: 多源 fallback ──
def _fallback(sources, log_tag=''):
    """依次尝试数据源函数列表，返回第一个非空/非异常结果。
    Args:
        sources: [(name, callable), ...] 每个 callable 返回数据
        log_tag: 日志前缀（如 '[fundamental]'）
    Returns:
        (data, source_name)
    全部失败返回 (None, None)。
    """
    for name, fn in sources:
        try:
            t0 = time.time()
            data = fn()
            if data is not None and data != [] and data != {}:
                if log_tag:
                    _log.info(f'{log_tag} {name} OK ({time.time()-t0:.1f}s)')
                return data, name
            if log_tag:
                _log.warning(f'{log_tag} {name} returned empty')
        except Exception as e:
            if log_tag:
                _log.warning(f'{log_tag} {name} failed: {e}')
            continue
    return None, None


# ── O2: 通用分片 ──
def _shard(data, total_shards, shard_idx):
    """将列表均分为 total_shards 片，返回第 shard_idx 片（0-based）。"""
    if not data or total_shards <= 0:
        return []
    n = len(data)
    chunk = max(1, n // total_shards)
    start = shard_idx * chunk
    if shard_idx >= total_shards - 1:
        return data[start:]
    return data[start:start + chunk]

# ── V2.0.2: 共享 K 线缓存 + 磁盘持久化 ──
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.cache')
_KLINE_CACHE_FILE = os.path.join(_CACHE_DIR, 'kline_cache.json')

def _load_kline_cache():
    """从磁盘加载 K 线缓存，异常时静默返回空 dict"""
    try:
        if os.path.exists(_KLINE_CACHE_FILE):
            with open(_KLINE_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, Exception):
        pass
    return {}

def _save_kline_cache(cache):
    """保存 K 线缓存到磁盘（原子写入：tmp + os.replace）"""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    tmp = _KLINE_CACHE_FILE + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        os.replace(tmp, _KLINE_CACHE_FILE)
    except Exception:
        pass

# 启动时从磁盘恢复 K 线缓存
_kline_cache = _load_kline_cache()
_kline_lock = threading.Lock()

def get_kline_cache(key):
    """读 K 线缓存（仅内存，磁盘已在启动时加载一次）"""
    with _kline_lock:
        return _kline_cache.get(key)

def set_kline_cache(key, value):
    """写 K 线缓存（内存+磁盘），含 LRU 淘汰（最大 500 key）"""
    with _kline_lock:
        _kline_cache.pop(key, None)  # 先删后插 → 标记为 MRU
        _kline_cache[key] = value
        # LRU：超过 500 key 淘汰最久未插入的
        while len(_kline_cache) > 500:
            _kline_cache.pop(next(iter(_kline_cache)))
        cache_snapshot = dict(_kline_cache)  # shallow copy 后释放锁
    _save_kline_cache(cache_snapshot)
