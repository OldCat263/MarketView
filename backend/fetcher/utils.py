"""工具函数：安全转换 + DataFrame处理 + fallback + 分片"""
import json, time, logging

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
