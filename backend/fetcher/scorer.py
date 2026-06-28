"""七维评分系统 — 10 因子 + 历史相似场景 + 多周期确认 + 百分位排名
===========================================
纯 Python，零依赖。快速档（4维纯本地）< 100ms，完整档（7维+外部）< 5s。

评分维度: 缠论(25%) + 回测(20%) + 量化因子(15%) + 基本面(15%) + 技术指标(10%) + 资金面(10%) + 新闻(5%)
"""
import json, time, math, random, os, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .indicators import calc_ma, calc_boll, calc_macd, calc_rsi, calc_atr, calc_vpt


# V2.0.2: 共享 K 线缓存读取（走 utils.py 的 set/get，与 main.py 共用 + 磁盘持久化）
def _fetch_kline_cached(module, code, period='1d', count=100):
    """走共享 K 线缓存（含磁盘持久化），避免重复拉取。
    TTL 5min，cache_key 不含 count（不同 count 请求共享，取 max count）。
    """
    from .utils import get_kline_cache, set_kline_cache
    cache_key = f'{module}_{code}_{period}'
    cached = get_kline_cache(cache_key)
    if cached and time.time() - cached['ts'] < 300:
        rows = cached['data'].get('data', [])
        if rows:
            return rows[-count:] if len(rows) > count else rows
        return []
    # 未命中 → 拉取（用较大 count 以覆盖后续请求）
    fn = _KL_FN.get(module)
    if not fn:
        return []
    rows = fn(code, period, max(count, 200))  # 至少拉 200 根
    if rows:
        set_kline_cache(cache_key, {'data': {'data': rows}, 'ts': time.time()})
        return rows[-count:] if len(rows) > count else rows
    return rows
from .chanlun import analyze as chanlun_analyze
from .backtest import backtest as run_backtest
from .fundamentals import get_fundamentals
from .kline import fetch_kline_stock, fetch_kline_etf, fetch_kline_hk, \
    fetch_kline_us, fetch_kline_index, fetch_kline_crypto

# 6 模块 K线 fetch 映射
_KL_FN = {
    'stock': fetch_kline_stock, 'etf': fetch_kline_etf,
    'hk': fetch_kline_hk, 'us': fetch_kline_us,
    'index': fetch_kline_index, 'crypto': fetch_kline_crypto,
}

# ── 因子计算 ──

def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, round(v, 2)))


def _calc_quant_factors(rows):
    """计算 10 个量化因子（Q1-Q10，方案 B）。
    Returns: {q1_momentum: 0-100, ..., quant_score: 0-100}
    """
    if len(rows) < 60:
        return _empty_quant_score()

    closes = [r[2] for r in rows]
    highs = [r[3] for r in rows]
    lows = [r[4] for r in rows]
    volumes = [r[5] for r in rows]
    n = len(closes)

    # Extract indicators
    ma = calc_ma(closes)
    boll = calc_boll(closes)
    rsi_d = calc_rsi(closes)
    atr_d = calc_atr(highs, lows, closes)
    vpt_d = calc_vpt(closes, volumes)

    # Q1: 动量（20日收益率）
    if n >= 21:
        momentum_pct = (closes[-1] - closes[-21]) / closes[-21] * 100
    else:
        momentum_pct = 0
    q1 = _clamp(momentum_pct / 10 * 100)  # +10% → 100分

    # Q2: 反转（5日收益率取负）
    if n >= 6:
        rev_pct = -(closes[-1] - closes[-6]) / closes[-6] * 100
    else:
        rev_pct = 0
    q2 = _clamp(rev_pct / 5 * 100)  # +5% → 100分

    # Q3: 波动率收缩（BOLL 带宽 / 20日均带宽）
    boll_upper = [v for v in boll['UPPER'] if v is not None]
    boll_lower = [v for v in boll['LOWER'] if v is not None]
    if len(boll_upper) >= 41 and len(boll_lower) >= 41:
        cur_band = boll_upper[-1] - boll_lower[-1]
        past_bands = [boll_upper[i] - boll_lower[i] for i in range(-21, 0) if boll_upper[i] and boll_lower[i]]
        avg_band = sum(past_bands) / len(past_bands) if past_bands else cur_band
        contraction = (1 - cur_band / avg_band) * 100 if avg_band > 0 else 0
    else:
        contraction = 0
    q3 = _clamp(contraction / 30 * 100)

    # Q4: 放量（今日量 / 20日均量）
    if n >= 21:
        vol_ratio = volumes[-1] / (sum(volumes[-21:]) / 21) if sum(volumes[-21:]) > 0 else 1
    else:
        vol_ratio = 1
    q4 = _clamp((vol_ratio - 1) / 1.0 * 100)  # 2.0倍 → 100分

    # Q5: 均线排列
    ma5 = ma.get('MA5', [])
    ma10 = ma.get('MA10', [])
    ma20 = ma.get('MA20', [])
    ma60 = ma.get('MA60', [])
    q5 = 0
    if ma5 and ma10 and ma20 and ma60:
        last5 = ma5[-1] if ma5[-1] is not None else 0
        last10 = ma10[-1] if ma10[-1] is not None else 0
        last20 = ma20[-1] if ma20[-1] is not None else 0
        last60 = ma60[-1] if ma60[-1] is not None else 0
        if last5 > last10: q5 += 25
        if last10 > last20: q5 += 25
        if last20 > last60: q5 += 25
        if last5 > last20: q5 += 25

    # Q6: RSI(14)
    rsi_vals = [v for v in rsi_d.get('RSI', []) if v is not None]
    if rsi_vals:
        rsi = rsi_vals[-1]
        if rsi < 30:
            q6 = _clamp((30 - rsi) / 30 * 100)
        elif rsi > 70:
            q6 = _clamp((rsi - 70) / 30 * 100)
        else:
            q6 = 0
    else:
        q6 = 50

    # Q7: ATR(14) — 在历史范围中的位置
    atr_vals = [v for v in atr_d.get('ATR', []) if v is not None]
    if len(atr_vals) >= 21:
        atr_now = atr_vals[-1]
        atr_20d_min = min(atr_vals[-21:])
        atr_20d_max = max(atr_vals[-21:])
        denom = atr_20d_max - atr_20d_min
        q7 = _clamp((atr_now - atr_20d_min) / denom * 100) if denom > 0 else 50
    else:
        q7 = 50

    # Q8: VPT — 量价趋势位置
    vpt_vals = [v for v in vpt_d.get('VPT', []) if v is not None]
    if len(vpt_vals) >= 21:
        vpt_now = vpt_vals[-1]
        vpt_20d_min = min(vpt_vals[-21:])
        vpt_20d_max = max(vpt_vals[-21:])
        denom = vpt_20d_max - vpt_20d_min
        q8 = _clamp((vpt_now - vpt_20d_min) / denom * 100) if denom > 0 else 50
    else:
        q8 = 50

    # Q9: 50日位置
    if n >= 50:
        h50 = max(highs[-50:])
        l50 = min(lows[-50:])
        pos = (closes[-1] - l50) / (h50 - l50) if (h50 - l50) > 0 else 0.5
        q9 = _clamp(pos * 100)
    else:
        q9 = 50

    # Q10: 北向关联（默认 50 分，scorer 会覆盖）
    q10 = 50

    # 等权综合
    factors = {'q1_momentum': q1, 'q2_reversal': q2, 'q3_vol_contraction': q3,
               'q4_volume_ratio': q4, 'q5_ma_alignment': q5,
               'q6_rsi': q6, 'q7_atr': q7, 'q8_vpt': q8,
               'q9_position_50d': q9, 'q10_north_corr': q10}
    quant_score = round(sum(factors.values()) / 10, 2)
    factors['quant_score'] = quant_score

    return factors


def _empty_quant_score():
    return {f'q{i}': 50 for i in range(1, 11)} | {'quant_score': 50.0}


# ── 历史相似场景匹配 ──

def _find_similar_setups(chanlun_result, rows, N=3):
    """在当前 K线历史中找最近的相似中枢结构。
    Returns: [{date, zg, zd, result_30d, signal}, ...]
    """
    zs_list = chanlun_result.get('zhongshu_list', [])
    if not zs_list or len(rows) < 60:
        return []

    current_zs = zs_list[-1]
    cur_zg = current_zs['zg']
    cur_zd = current_zs['zd']

    matches = []
    # 在 rows 后2/3区域滑动窗口搜索相似中枢
    for i in range(len(rows) // 3, len(rows) - 30):
        window = rows[i:i+30]
        highs = [r[3] for r in window]
        lows = [r[4] for r in window]
        zg_hist = sum(sorted(highs)[-5:]) / 5  # 近5日高均值
        zd_hist = sum(sorted(lows)[:5]) / 5      # 近5日低均值

        # 计算匹配度（ZG/ZD偏差率）
        dev = (abs(zg_hist - cur_zg) + abs(zd_hist - cur_zd)) / max(cur_zg, 0.01)
        if dev < 0.15:  # 偏差 < 15%
            # 30日后结果
            result_idx = min(i + 30, len(rows) - 1)
            result_30d = round((rows[result_idx][2] - rows[i][2]) / rows[i][2] * 100, 2)

            # 推断信号类型
            if result_30d > 5:
                signal = '一类买'
            elif result_30d < -5:
                signal = '一类卖'
            else:
                signal = '盘整'

            matches.append({
                'date': str(rows[i][0])[:10],
                'zg': round(zg_hist, 2),
                'zd': round(zd_hist, 2),
                'result_30d': f'{result_30d:+.1f}%',
                'signal': signal,
                'deviation': round(dev * 100, 1),
            })

    # 按偏差排序取前 N 个
    matches.sort(key=lambda m: m['deviation'])
    return matches[:N]


# ── 多周期确认 ──

def _multi_period_confirm(module, code, daily_signal_type):
    """日线信号用周线走势做置信度调节。
    Returns: {'weekly_zoushi': str, 'factor': float, 'signal': str}
    factor > 1 = 共振, factor < 1 = 背离
    """
    fn = _KL_FN.get(module)
    if not fn:
        return {'weekly_zoushi': 'unknown', 'factor': 1.0, 'signal': '无周线数据'}

    try:
        weekly_rows = fn(code, '1w', 200)
        if not weekly_rows or len(weekly_rows) < 30:
            return {'weekly_zoushi': 'insufficient', 'factor': 1.0, 'signal': '周线数据不足'}
        w_cl = chanlun_analyze(weekly_rows)
        weekly_zoushi = w_cl.get('zoushi', {}).get('type', '盘整')
    except Exception:
        return {'weekly_zoushi': 'error', 'factor': 1.0, 'signal': '周线获取失败'}

    # 日线信号 + 周线走势 → 置信度因子
    is_buy = '买' in daily_signal_type
    is_sell = '卖' in daily_signal_type

    if is_buy:
        if weekly_zoushi == '上涨':
            return {'weekly_zoushi': weekly_zoushi, 'factor': 1.3, 'signal': '大小周期共振'}
        elif weekly_zoushi == '盘整':
            return {'weekly_zoushi': weekly_zoushi, 'factor': 1.0, 'signal': '日线信号，周线盘整'}
        else:
            return {'weekly_zoushi': weekly_zoushi, 'factor': 0.7, 'signal': '逆大势（日买周跌）'}
    elif is_sell:
        if weekly_zoushi == '下跌':
            return {'weekly_zoushi': weekly_zoushi, 'factor': 1.3, 'signal': '大小周期共振'}
        elif weekly_zoushi == '盘整':
            return {'weekly_zoushi': weekly_zoushi, 'factor': 1.0, 'signal': '日线信号，周线盘整'}
        else:
            return {'weekly_zoushi': weekly_zoushi, 'factor': 0.7, 'signal': '逆大势（日卖周涨）'}
    else:
        return {'weekly_zoushi': weekly_zoushi, 'factor': 1.0, 'signal': '无明确信号'}


# ── 百分位排名 ──

def _percentile_rank(scores, key):
    """计算某个 key 在分数列表中的百分位排名（越小越好，即前X%）。"""
    # 先判断：如果 scores 是纯数字列表，直接排序取百分位
    if scores and isinstance(scores[0], (int, float)):
        vals = sorted(scores, reverse=True)
        my_val = scores[-1]
    else:
        # scores 是字典列表
        vals = sorted([s.get(key, 0) for s in scores], reverse=True)
        if not vals:
            return 50.0
        my_val = scores[-1].get(key, 0) if isinstance(scores[-1], dict) else 0

    better = sum(1 for v in vals if v > my_val)
    return round(better / len(vals) * 100, 1)


# ── 主评分入口 ──

def score_single(module, code, rows, period='1d', mode='quick'):
    """单票七维评分。

    Args:
        module: 模块名
        code: 代码
        rows: K线数据
        period: 周期
        mode: 'quick'(4维纯本地) | 'full'(7维+外部)

    Returns:
        {code, name, module, period, chanlun, backtest, score, quant_factors,
         similar_setups, multi_period, fundamental, news_sentiment, ai, ts}
    """
    t0 = time.time()

    # 1. 缠论分析
    cl = chanlun_analyze(rows)

    # 2. 回测
    bt = run_backtest(cl, rows)

    # 3. 量化因子
    qf = _calc_quant_factors(rows)

    # 4. 缠论评分 (0-100)
    buy_pts = len(cl['buy_points']) + len(cl['buy_points_ext'])
    sell_pts = len(cl['sell_points']) + len(cl['sell_points_ext'])
    has_beichi = len(cl['beichi_list']) > 0
    zs_count = len(cl['zhongshu_list'])

    chanlun_score = 50
    if buy_pts > 0 and sell_pts == 0: chanlun_score = 75
    if buy_pts > 0 and has_beichi: chanlun_score = 85
    if sell_pts > 0 and buy_pts == 0: chanlun_score = 25
    if zs_count >= 2: chanlun_score += 5
    chanlun_score = _clamp(chanlun_score)

    # 5. 回测评分的weighted组合
    all_stats = bt['stats'].get('all', {})
    win_rate = all_stats.get('win_rate', 50)
    sharpe = all_stats.get('sharpe', 0)
    pl_ratio = all_stats.get('pl_ratio', 0)
    n_trades = all_stats.get('sample_count', 0)

    backtest_score = 50
    if n_trades >= 5:
        backtest_score = _clamp(win_rate * 0.5 + sharpe * 10 + pl_ratio * 10)

    # 6. 技术指标评分（MA排列 + BOLL位置）
    tech_score = qf.get('q5_ma_alignment', 50) * 0.5 + qf.get('q3_vol_contraction', 50) * 0.5
    tech_score = _clamp(tech_score)

    # 7. 综合评分（4维快速档）
    total = (
        chanlun_score * 0.30 +      # 缠论30% (quick加权)
        backtest_score * 0.25 +     # 回测25%
        qf.get('quant_score', 50) * 0.25 +  # 量化因子25%
        tech_score * 0.20           # 技术指标20%
    )
    total = _clamp(total)

    score_detail = {
        'chanlun': chanlun_score,
        'backtest': backtest_score,
        'quant_factors': qf.get('quant_score', 50),
        'tech_indicators': round(tech_score, 2),
        'fundamental': 50,
        'capital_flow': 50,
        'news_sentiment': 50,
        'total_score': round(total, 2),
    }

    result = {
        'code': code, 'name': '', 'module': module, 'period': period,
        'chanlun': cl,
        'backtest': bt,
        'score': score_detail,
        'quant_factors': qf,
        'similar_setups': [],
        'multi_period': {'factor': 1.0, 'signal': 'quick mode'},
        'fundamental': {'available': False},
        'news_sentiment': {'score': 50},
        'ai': None,
        'ts': time.time(),
        'elapsed_ms': round((time.time() - t0) * 1000),
    }

    # 完整档：外援扩展
    if mode == 'full':
        # 基本面
        try:
            result['fundamental'] = get_fundamentals(module, code)
            # Q10: 北向关联（从基本面数据）
            nf = result['fundamental'].get('north_flow', 0)
            if isinstance(nf, (int, float)) and nf > 0:
                qf['q10_north_corr'] = _clamp((nf / 1e8) * 100)
            score_detail['fundamental'] = _clamp(50 + (result['fundamental'].get('roe', 0) - 10))
        except Exception:
            pass

        # 多周期确认
        try:
            primary_signal = cl['buy_points'][0]['type'] if cl['buy_points'] else (
                cl['sell_points'][0]['type'] if cl['sell_points'] else '')
            result['multi_period'] = _multi_period_confirm(module, code, primary_signal)
            # 调整总分
            mp_factor = result['multi_period'].get('factor', 1.0)
            score_detail['total_score'] = _clamp(total * mp_factor)
        except Exception:
            pass

        # 历史相似场景
        result['similar_setups'] = _find_similar_setups(cl, rows)

        result['elapsed_ms'] = round((time.time() - t0) * 1000)

    return result


# ── 批量排行 ──

def rank_batch(module, codes, period='1d', mode='quick', max_workers=5):
    """批量评分排行。

    Args:
        module: 模块名
        codes: 代码列表（最多 300）
        period: K线周期
        mode: 'quick' | 'full'
        max_workers: 并发线程数

    Returns:
        按 total_score 降序排列的结果列表
    """
    fn = _KL_FN.get(module)
    if not fn:
        return []

    codes = codes[:300]  # 候选池上限

    def _score_one(code):
        try:
            count = 100 if mode == 'quick' else 200
            rows = _fetch_kline_cached(module, code, period, count)
            if not rows or len(rows) < 30:
                return None
            return score_single(module, code, rows, period, mode)
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_score_one, c): c for c in codes}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # 按总分降序
    results.sort(key=lambda x: x['score'].get('total_score', 0), reverse=True)

    # 添加百分位排名
    all_scores = [r['score'].get('total_score', 0) for r in results]
    for i, r in enumerate(results):
        r['pct_total'] = round((1 - (i + 1) / max(len(results), 1)) * 100, 1)
        r['pct_chanlun'] = _percentile_rank(
            [x['score'].get('chanlun', 0) for x in results],
            r['score'].get('chanlun', 0))

    return results
