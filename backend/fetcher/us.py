"""模块五：美股 — 腾讯 qt.gtimg.cn 为主源（白名单全干净代码，无dot-suffix，腾讯完全支持）
V2.0.3: 白名单过滤，仅保留中概股+全球龙头+中概ETF ~150只
V2.1.0: 切腾讯源（从akshare全量13538只→腾讯直接查白名单150只）+ 加分类字段 + 3分片/5s
"""
import json, time, os, httpx
from .utils import _safe_float

_US_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.cache', 'us_codes.json')

# V2.1.0 白名单 + 分类（与中国联动密切的美股）
_US_CATEGORY = {
    # ── 中概股 ADR（与中国资产联动最紧）──
    'BABA': '中概股','JD': '中概股','PDD': '中概股','BIDU': '中概股','NIO': '中概股',
    'XPEV': '中概股','LI': '中概股','BILI': '中概股','TME': '中概股','NTES': '中概股',
    'ZTO': '中概股','TAL': '中概股','VIPS': '中概股','IQ': '中概股','BZ': '中概股',
    'BEKE': '中概股','YMM': '中概股','TCOM': '中概股','DADA': '中概股','GDS': '中概股',
    'HUYA': '中概股','DOYU': '中概股','RLX': '中概股','MNSO': '中概股','HSAI': '中概股',
    'ZLAB': '中概股','BGNE': '中概股','FUTU': '中概股','TIGR': '中概股','ATHM': '中概股',
    'BEDU': '中概股','QFIN': '中概股','LU': '中概股','YUMC': '中概股','HCM': '中概股',
    'KC': '中概股','TUYA': '中概股','NOAH': '中概股','CAN': '中概股','JKS': '中概股',
    'CSIQ': '中概股','DQ': '中概股','GSX': '中概股','YI': '中概股','ZH': '中概股',
    'WB': '中概股','SOHU': '中概股','YY': '中概股','MOGU': '中概股','NIU': '中概股',
    'WDH': '中概股','FINV': '中概股','LX': '中概股','EH': '中概股','EDU': '中概股',
    'GOTU': '中概股','VNET': '中概股','SMI': '中概股','JFIN': '中概股','XNET': '中概股',
    'API': '中概股','CCM': '中概股','DDL': '中概股',
    # ── 全球科技龙头 ──
    'AAPL': '全球龙头','MSFT': '全球龙头','NVDA': '全球龙头','GOOGL': '全球龙头',
    'AMZN': '全球龙头','META': '全球龙头','TSLA': '全球龙头','NFLX': '全球龙头',
    'CRM': '全球龙头','ORCL': '全球龙头','ADBE': '全球龙头','AMD': '全球龙头',
    'INTC': '全球龙头','QCOM': '全球龙头','AVGO': '全球龙头','TXN': '全球龙头',
    'MU': '全球龙头','AMAT': '全球龙头','LRCX': '全球龙头','ASML': '全球龙头',
    'TSM': '全球龙头','ARM': '全球龙头','SNOW': '全球龙头','PLTR': '全球龙头','NOW': '全球龙头',
    # ── 金融/消费/医疗巨头（全球风向标）──
    'JPM': '全球龙头','GS': '全球龙头','V': '全球龙头','MA': '全球龙头','BAC': '全球龙头',
    'C': '全球龙头','WFC': '全球龙头','MS': '全球龙头','AXP': '全球龙头','BLK': '全球龙头',
    'JNJ': '全球龙头','PFE': '全球龙头','MRK': '全球龙头','ABBV': '全球龙头','BMY': '全球龙头',
    'LLY': '全球龙头','UNH': '全球龙头','MRNA': '全球龙头',
    'XOM': '全球龙头','CVX': '全球龙头','WMT': '全球龙头','COST': '全球龙头','DIS': '全球龙头',
    'NKE': '全球龙头','SBUX': '全球龙头','MCD': '全球龙头','KO': '全球龙头','PEP': '全球龙头',
    'PG': '全球龙头','HD': '全球龙头','LOW': '全球龙头',
    'BA': '全球龙头','CAT': '全球龙头','GE': '全球龙头','UBER': '全球龙头','PYPL': '全球龙头',
    'SQ': '全球龙头','COIN': '全球龙头','MSTR': '全球龙头','RIVN': '全球龙头','LCID': '全球龙头',
    # ── 中概相关 ETF ──
    'FXI': '中概ETF','KWEB': '中概ETF','MCHI': '中概ETF','ASHR': '中概ETF','CQQQ': '中概ETF',
    'KBA': '中概ETF','KALL': '中概ETF','PGJ': '中概ETF','CXSE': '中概ETF','CHIQ': '中概ETF',
    'CHAU': '中概ETF','YINN': '中概ETF','YANG': '中概ETF',
    'TQQQ': '中概ETF','SQQQ': '中概ETF','SPY': '中概ETF','QQQ': '中概ETF','IWM': '中概ETF',
    'DIA': '中概ETF','EEM': '中概ETF','VWO': '中概ETF','XLF': '中概ETF','XLE': '中概ETF',
    'XLK': '中概ETF','XLV': '中概ETF',
    # ── 港股二次上市 ADR ──
    'TCEHY': '港股ADR','NTDOY': '港股ADR','NSRGY': '港股ADR','RHHBY': '港股ADR',
    'UL': '港股ADR','NVS': '港股ADR','HSBC': '港股ADR','SONY': '港股ADR','TM': '港股ADR',
    'BUD': '港股ADR',
}

_US_WHITELIST = set(_US_CATEGORY.keys())
_US_CODES_SORTED = None
# V2.2.7: 降级占位符 — 连续失败/空数据时禁用 roller
_us_disabled = False
_us_fail_count = 0
_US_DISABLED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.cache', 'us_disabled.json')


def _load_us_disabled():
    """V2.2.7: 加载持久化降级状态（避免重启后立即重新打数据源）"""
    global _us_disabled
    try:
        if os.path.exists(_US_DISABLED_FILE):
            with open(_US_DISABLED_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                _us_disabled = bool(d.get('disabled', False))
                if _us_disabled:
                    print(f'[us] PERSISTENT DISABLED (上次启动发现持续无数据，已自动降级)', flush=True)
    except Exception:
        pass


def _save_us_disabled(disabled):
    """V2.2.7: 持久化降级状态"""
    try:
        os.makedirs(os.path.dirname(_US_DISABLED_FILE), exist_ok=True)
        with open(_US_DISABLED_FILE, 'w', encoding='utf-8') as f:
            json.dump({'disabled': disabled, 'ts': time.time()}, f)
    except Exception:
        pass


def _load_us_codes():
    """加载白名单代码列表"""
    global _US_CODES_SORTED
    if _US_CODES_SORTED:
        return _US_CODES_SORTED
    try:
        with open(_US_CODES_FILE, 'r', encoding='utf-8') as f:
            _US_CODES_SORTED = json.load(f)
        return _US_CODES_SORTED
    except Exception:
        pass
    _US_CODES_SORTED = sorted(_US_WHITELIST)
    try:
        os.makedirs(os.path.dirname(_US_CODES_FILE), exist_ok=True)
        with open(_US_CODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(_US_CODES_SORTED, f)
    except Exception:
        pass
    return _US_CODES_SORTED


def _parse_tencent_us(line):
    """解析腾讯美股 qt.gtimg.cn 响应行"""
    if '="' not in line:
        return None
    _, data = line.split('="', 1)
    fields = data.rstrip('";\n').split('~')
    if len(fields) < 35:
        return None
    code_full = fields[2]
    code = code_full.split('.')[0] if '.' in str(code_full) else code_full
    category = _US_CATEGORY.get(code, '其他')
    return {
        '代码': code,
        '名称': fields[1],
        '分类': category,
        '最新价': _safe_float(fields[3]),
        '昨收': _safe_float(fields[4]),
        '今开': _safe_float(fields[5]),
        '成交量': _safe_float(fields[6]),
        '涨跌额': _safe_float(fields[31]) if len(fields) > 31 else 0,
        '涨跌幅': _safe_float(fields[32]) if len(fields) > 32 else 0,
        '最高': _safe_float(fields[33]) if len(fields) > 33 else 0,
        '最低': _safe_float(fields[34]) if len(fields) > 34 else 0,
        '成交额': _safe_float(fields[37]) if len(fields) > 37 else 0,
    }


def _from_tencent(codes):
    """腾讯串行拉取（~150 只/3 批，< 3s）
    V2.2.7: 连续失败/空数据时自动降级 + 指数退避
    """
    global _us_disabled, _us_fail_count
    if _us_disabled:
        return []
    batches = [codes[i:i + 50] for i in range(0, len(codes), 50)]
    result = []
    has_error = False
    for batch in batches:
        try:
            url = 'https://qt.gtimg.cn/q=' + ','.join('us' + str(c) for c in batch)
            resp = httpx.get(url, timeout=15)
            for line in resp.text.split('\n'):
                r = _parse_tencent_us(line)
                if r:
                    result.append(r)
        except Exception as e:
            print(f'[us] batch error: {e}', flush=True)
            has_error = True
    # V2.2.7: 连续 3 次失败/空数据 → 自动降级
    if has_error or not result:
        _us_fail_count += 1
        if _us_fail_count >= 3:
            _us_disabled = True
            _save_us_disabled(True)
            print(f'[us] AUTO-DISABLED: 连续 {_us_fail_count} 次失败/空数据，已降级为占位符（避免无效请求）', flush=True)
    else:
        if _us_fail_count > 0:
            print(f'[us] 恢复成功，重置 fail_count={_us_fail_count}', flush=True)
        _us_fail_count = 0
    return result


def is_disabled():
    """V2.2.7: 供 main.py /api/health 读取判断 us 状态"""
    return _us_disabled


def get_backoff_seconds():
    """V2.2.7: 指数退避（30s→60s→120s→300s→600s 上限）"""
    if _us_fail_count == 0:
        return 0
    base = 30 * (2 ** (_us_fail_count - 1))
    return min(base, 600)


def fetch_shard(shard_idx, total_shards):
    """美股分片：腾讯直接查白名单 150 只（V2.1.0 串行拉取，3 分片/5s）"""
    codes = _load_us_codes()
    chunk = max(1, len(codes) // total_shards)
    s = shard_idx * chunk
    e = s + chunk if shard_idx < total_shards - 1 else len(codes)
    return _from_tencent(codes[s:e])


def get_json():
    """美股实时行情 — 腾讯 qt.gtimg.cn（白名单 ~150 只，秒级返回）"""
    try:
        rows = _from_tencent(list(_US_WHITELIST))
        return json.dumps(rows, ensure_ascii=False) if rows else '[]'
    except Exception as e:
        print(f'[us] get_json error: {e}', flush=True)
        return '[]'
