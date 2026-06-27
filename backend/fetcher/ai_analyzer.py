"""AI 综合分析 — Pollinations（免费无Key）+ 智谱 fallback + proxy线程安全
===========================================
O5: _found_proxy 线程安全（crypto 模块 proxy 检测仅限主线程）
Pollinations API: POST https://text.pollinations.ai/ → 返回纯文本
智谱 fallback: 需 ZHIPU_API_KEY 环境变量
"""
import json, time, httpx, os, threading, hashlib

# ── O5: 线程安全的代理缓存 ──
_proxy_cache = None
_proxy_lock = threading.Lock()


def _get_proxy():
    """线程安全获取代理（从 crypto 模块或环境变量）"""
    global _proxy_cache
    with _proxy_lock:
        if _proxy_cache is not None:
            return _proxy_cache
        # 环境变量优先
        env_proxy = os.environ.get('CRYPTO_PROXY', '')
        if env_proxy:
            _proxy_cache = env_proxy
            return _proxy_cache
        # 尝试从 crypto 模块获取
        try:
            from .crypto import _found_proxy
            if _found_proxy:
                _proxy_cache = _found_proxy
                return _proxy_cache
        except Exception:
            pass
        _proxy_cache = ''
        return ''


def _build_prompt(data):
    """构建 AI prompt（含历史对比+10因子+9指标+多周期确认+基本面+新闻）"""
    parts = []

    c = data.get('chanlun', {})
    s = data.get('score', {})
    qf = data.get('quant_factors', {})
    bt = data.get('backtest', {})
    f = data.get('fundamental', {})
    mp = data.get('multi_period', {})
    ss = data.get('similar_setups', [])
    ns = data.get('news_sentiment', {})

    code = data.get('code', '')
    name = data.get('name', code)

    parts.append(f'分析标的: {code} {name}')
    parts.append('')

    # 缠论
    zs_list = c.get('zhongshu_list', [])
    zoushi = c.get('zoushi', {})
    buy_pts = c.get('buy_points', []) + c.get('buy_points_ext', [])
    sell_pts = c.get('sell_points', []) + c.get('sell_points_ext', [])
    beichi = c.get('beichi_list', [])

    parts.append('## 缠论分析')
    parts.append(f'走势类型: {zoushi.get("type", "未知")}')
    if zs_list:
        last_zs = zs_list[-1]
        parts.append(f'最新中枢: ZG={last_zs["zg"]}, ZD={last_zs["zd"]}, 级别={last_zs["level"]}, 位置={last_zs["position"]}')
    if beichi:
        parts.append(f'背驰信号: {beichi[0]["type"]} (强度{beichi[0]["strength"]})')
    parts.append(f'买点: {len(buy_pts)}个 ({", ".join(p["type"] for p in buy_pts[:3]) or "无"})')
    parts.append(f'卖点: {len(sell_pts)}个 ({", ".join(p["type"] for p in sell_pts[:3]) or "无"})')
    parts.append('')

    # 历史相似场景
    if ss:
        parts.append('## 历史相似中枢结构')
        for i, hist in enumerate(ss):
            parts.append(f'{i+1}. {hist["date"]} ZG={hist["zg"]} ZD={hist["zd"]} 30日后={hist["result_30d"]} 信号={hist["signal"]}')
        parts.append('')

    # 量化因子
    parts.append('## 10因子量化')
    parts.append(f'动量(Q1): {qf.get("q1_momentum",50):.0f} | 反转(Q2): {qf.get("q2_reversal",50):.0f} | 波动率收缩(Q3): {qf.get("q3_vol_contraction",50):.0f}')
    parts.append(f'放量(Q4): {qf.get("q4_volume_ratio",50):.0f} | 均线排列(Q5): {qf.get("q5_ma_alignment",50):.0f} | RSI(Q6): {qf.get("q6_rsi",50):.0f}')
    parts.append(f'ATR(Q7): {qf.get("q7_atr",50):.0f} | VPT(Q8): {qf.get("q8_vpt",50):.0f} | 50日位置(Q9): {qf.get("q9_position_50d",50):.0f}')
    parts.append(f'北向关联(Q10): {qf.get("q10_north_corr",50):.0f} | 量化综合: {qf.get("quant_score",50):.0f}/100')
    parts.append('')

    # 回测
    stats = bt.get('stats', {}).get('all', {})
    if stats and stats.get('sample_count', 0) > 0:
        parts.append('## 回测统计')
        parts.append(f'样本量: {stats["sample_count"]} | 胜率: {stats["win_rate"]}% | 平均收益: {stats["avg_return"]}%')
        parts.append(f'盈亏比: {stats["pl_ratio"]} | 夏普: {stats["sharpe"]} | 最大回撤: {stats["max_drawdown"]}%')
        parts.append(f'连亏: {stats["max_consec_loss"]}次 | 盈利因子: {stats["profit_factor"]} | 持有: 均值{stats["hold_avg"]}d 中位{stats["hold_med"]}d')
        parts.append('')

    # 多周期确认
    if mp:
        parts.append(f'## 多周期确认: {mp.get("signal","")} (系数{mp.get("factor",1.0)})')
        parts.append('')

    # 基本面
    if f and f.get('available'):
        parts.append(f'## 基本面: PE={f.get("pe",0):.1f} PB={f.get("pb",0):.2f} ROE={f.get("roe",0):.1f}%')
        parts.append(f'营收增速: {f.get("rev_growth",0):.1f}% | 利润增速: {f.get("profit_growth",0):.1f}%')
        parts.append('')

    # 评分
    parts.append(f'## 综合评分: {s.get("total_score",50):.0f}/100')
    parts.append(f'缠论:{s.get("chanlun",50):.0f} | 回测:{s.get("backtest",50):.0f} | 量化:{s.get("quant_factors",50):.0f} | 技术:{s.get("tech_indicators",50):.0f}')
    parts.append('')

    # 用户指令
    parts.append('''请基于以上数据进行分析并输出:
1. 当前市场状态（技术面一句话）
2. 缠论视角（趋势/中枢/背驰/买卖点）
3. 多周期确认（共振还是背离）
4. 历史相似场景评估
5. 量化因子分析（10因子逐项解读）
6. 基本面评估
7. 风险提示
8. 交易建议 (buy/sell/hold + 置信度 0-100)
9. 关键价位（支撑/阻力）

注意: 历史数据不代表未来收益，仅供参考。''')

    return '\n'.join(parts)


def _call_pollinations(prompt):
    """调用 Pollinations AI（免费，无Key）"""
    try:
        resp = httpx.post(
            'https://text.pollinations.ai/',
            json={'messages': [
                {'role': 'system', 'content': '你是缠中说禅技术分析专家。基于结构化数据给出专业、客观的分析。所有建议仅供参考，不构成投资建议。'},
                {'role': 'user', 'content': prompt[:3000]},  # 截断过长的prompt
            ]},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception as e:
        print(f'[ai] Pollinations failed: {e}')
    return None


def _call_zhipu(prompt):
    """智谱 AI fallback（需 ZHIPU_API_KEY 环境变量）"""
    api_key = os.environ.get('ZHIPU_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = httpx.post(
            'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            json={
                'model': 'glm-4-flash',
                'messages': [
                    {'role': 'system', 'content': '你是缠中说禅技术分析专家。'},
                    {'role': 'user', 'content': prompt[:3000]},
                ],
            },
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', '')
    except Exception as e:
        print(f'[ai] Zhipu failed: {e}')
    return None


def _parse_ai_response(text):
    """从 AI 响应中提取结构化字段"""
    if not text:
        return {'analysis_text': '', 'signal': 'hold', 'confidence': 50,
                'key_levels': {'support': 0, 'resistance': 0}, 'risk_level': '中'}

    signal = 'hold'
    low = text.lower()
    if 'buy' in low or '买入' in text or '做多' in text:
        signal = 'buy'
    elif 'sell' in low or '卖出' in text or '做空' in text:
        signal = 'sell'

    # 提取置信度（搜索 "置信度" 或 "confidence" 后的数字）
    confidence = 50
    for line in text.split('\n'):
        if '置信度' in line or 'confidence' in low:
            import re
            nums = re.findall(r'(\d+)', line)
            if nums:
                confidence = min(100, max(0, int(nums[0])))

    risk_level = '中'
    if '高风险' in text or 'high risk' in low:
        risk_level = '高'
    elif '低风险' in text or 'low risk' in low:
        risk_level = '低'

    return {
        'analysis_text': text[:2000],
        'signal': signal,
        'confidence': confidence,
        'key_levels': {'support': 0, 'resistance': 0},
        'risk_level': risk_level,
    }


def analyze(data):
    """AI 综合分析主入口。

    Args:
        data: score_single() 返回的完整 dict

    Returns:
        {analysis_text, signal, confidence, ai_interpretation, key_levels, risk_level, source, ts}
    """
    t0 = time.time()

    prompt = _build_prompt(data)

    # 主源: Pollinations (免费)
    text = _call_pollinations(prompt)

    source = 'pollinations'
    if not text:
        # fallback: 智谱
        text = _call_zhipu(prompt)
        source = 'zhipu' if text else 'none'

    if not text:
        # 所有AI源不可用 → 基于规则生成简短分析
        s = data.get('score', {})
        total = s.get('total_score', 50)
        buy_count = len(data.get('chanlun', {}).get('buy_points', []))
        text = f'[本地规则分析] 综合评分: {total}/100, 买点: {buy_count}个。'
        text += 'AI 服务暂时不可用，以上为纯数据摘要。'
        source = 'local'

    parsed = _parse_ai_response(text)

    return {
        'ai_interpretation': parsed['analysis_text'],
        'signal': parsed['signal'],
        'confidence': parsed['confidence'],
        'key_levels': parsed['key_levels'],
        'risk_level': parsed['risk_level'],
        'source': source,
        'analysis_text': text[:2000],
        'ts': time.time(),
        'elapsed_ms': round((time.time() - t0) * 1000),
    }
