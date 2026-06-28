#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarketView 验收脚本
跑模块数据量 + SSE 心跳 + K线接口 + 铁律自检 + 核心文件 diff + 预测端点
0 token 消耗：调脚本即可，无需 AI 介入
V1.6.0.15: Windows GBK 终端兼容（sys.stdout.reconfigure utf-8）

用法：
  python mv_validate.py all      # 全部检查
  python mv_validate.py modules  # 8 模块数据量
  python mv_validate.py sse      # 8 模块 SSE 心跳
  python mv_validate.py kline    # V1.7.0+ K线接口
  python mv_validate.py news     # V1.8.0+ 新闻接口
  python mv_validate.py predict  # V2.0.0+ 智能预测端点
  python mv_validate.py rules    # 铁律自检
  python mv_validate.py diff     # 核心文件 diff
"""
import sys
import os
import json
import re
import subprocess
from urllib.request import urlopen
from urllib.error import URLError
import socket

# V1.6.0.15: Windows 终端默认 GBK 不支持 emoji，
# reconfigure 为 utf-8 让 ✅/⚠️/❌ 正常输出（Python 3.7+）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = os.environ.get('MV_BASE_URL', 'http://localhost:8000')
# __file__ = d:\服务器ETF\.trae\skills\mv-validator\scripts\mv_validate.py
# 5 次 dirname 才能到 d:\服务器ETF
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    )
)

MODULES = ['stock', 'etf', 'hk', 'us', 'index', 'crypto', 'news']
CORE_FILES = [
    'backend/main.py',
    'frontend/js/core.js',
    'frontend/index.html',
    'frontend/css/main.css',
]
KLINE_SAMPLES = {
    'stock': 'sh600519',
    'etf': 'sh510300',
    'hk': 'hk00700',
    'us': 'usAAPL',
    'index': 'sh000001',
    'crypto': 'BTCUSDT',
}


def hr(title):
    print('\n' + '=' * 60)
    print(f'【{title}】')
    print('=' * 60)


def fetch_json(url, timeout=5):
    try:
        with urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (URLError, socket.timeout, ConnectionRefusedError, OSError) as e:
        return {'_error': str(e)}


def read_sse_lines(url, timeout=6, max_lines=15):
    try:
        with urlopen(url, timeout=timeout) as resp:
            lines = []
            for i, line in enumerate(resp):
                lines.append(line.decode('utf-8', errors='ignore').strip())
                if i >= max_lines:
                    break
            return lines
    except Exception as e:
        return [f'_error: {e}']


def check_modules():
    hr('1. 6 模块数据量检查')
    total_ok = 0
    for m in MODULES:
        data = fetch_json(f'{BASE_URL}/api/{m}/spot')
        if '_error' in data:
            print(f'  ❌ {m:8s} 连接失败: {data["_error"]}')
            continue
        d = data.get('data')
        if isinstance(d, dict):
            cnt = sum(len(v) if isinstance(v, list) else 0 for v in d.values())
            structure = 'dict{china,global}'
        elif isinstance(d, list):
            cnt = len(d)
            structure = 'list'
        else:
            cnt = 0
            structure = 'unknown'
        if m == 'crypto' and cnt == 0:
            print(f'  ⚠️  {m:8s} {cnt:>6} 条  ({structure}) - 无代理属预期')
        elif cnt > 0:
            print(f'  ✅ {m:8s} {cnt:>6} 条  ({structure})')
            total_ok += 1
        else:
            print(f'  ❌ {m:8s} {cnt:>6} 条  ({structure})')
    print(f'\n  汇总: {total_ok}/{len(MODULES)-1} 模块有数据（crypto 单独计）')
    return total_ok


def check_sse():
    hr('2. SSE 心跳检查（每模块 6s 窗口，应收 1~2 个 shard:-1）')
    total_ok = 0
    for m in MODULES:
        lines = read_sse_lines(f'{BASE_URL}/api/stream/{m}', timeout=6, max_lines=20)
        if lines and lines[0].startswith('_error'):
            print(f'  ❌ {m:8s} {lines[0]}')
            continue
        # SSE 格式 "data: {...}"，找含 shard:-1 的 data 行
        data_lines = [l for l in lines if l.startswith('data:')]
        heartbeats = sum(1 for l in data_lines if 'shard":-1' in l or 'shard": -1' in l)
        data_msgs = sum(1 for l in data_lines if '"shard":' in l and 'shard":-1' not in l and 'shard": -1' not in l)
        if heartbeats >= 1:
            print(f'  ✅ {m:8s} 心跳 {heartbeats} 次 / 数据 {data_msgs} 条')
            total_ok += 1
        elif data_msgs >= 1:
            print(f'  ⚠️  {m:8s} 数据 {data_msgs} 条但无 shard:-1 心跳（V1.6.0.6 前的实现）')
        else:
            print(f'  ❌ {m:8s} 无任何 data 消息')
    print(f'\n  汇总: {total_ok}/{len(MODULES)} 模块心跳正常')


def check_kline():
    hr('3. K线接口检查（V1.7.0+）')
    total_ok = 0
    for m, code in KLINE_SAMPLES.items():
        data = fetch_json(f'{BASE_URL}/api/kline/{m}/{code}?period=1d&count=10')
        if '_error' in data:
            print(f'  ❌ {m:8s} {code:10s} 连接失败: {data["_error"]}')
            continue
        if 'detail' in data and '_error' not in data:
            print(f'  ❌ {m:8s} {code:10s} API 错误: {data.get("detail", "")}')
            continue
        rows = data.get('data', [])
        ma = data.get('ma', {})
        boll = data.get('boll', {})
        macd = data.get('macd', {})
        ma_ok = bool(ma.get('MA5'))
        boll_ok = bool(boll.get('MID'))
        macd_ok = bool(macd.get('DIF'))
        indicator_ok = ma_ok and boll_ok and macd_ok
        if m == 'crypto' and len(rows) == 0:
            print(f'  ⚠️  {m:8s} {code:10s} {len(rows):>3} rows - 无代理属预期')
        elif len(rows) >= 5 and indicator_ok:
            print(f'  ✅ {m:8s} {code:10s} {len(rows):>3} rows  MA+BOLL+MACD ✓')
            total_ok += 1
        else:
            print(f'  ⚠️  {m:8s} {code:10s} {len(rows):>3} rows  MA={ma_ok} BOLL={boll_ok} MACD={macd_ok}')
    print(f'\n  汇总: {total_ok}/{len(KLINE_SAMPLES)-1} 模块 K线完整（crypto 单独计）')


def check_news():
    hr('3.5. 新闻接口检查（V1.8.0+）')
    data = fetch_json(f'{BASE_URL}/api/news/spot')
    if '_error' in data:
        print(f'  ❌ 新闻 REST 连接失败: {data["_error"]}')
        return
    rows = data.get('data', [])
    cnt = len(rows) if isinstance(rows, list) else 0
    fields_ok = False
    if cnt > 0:
        first = rows[0]
        fields_ok = all(k in first for k in ('datetime', 'content', 'source'))
    if cnt > 0 and fields_ok:
        print(f'  ✅ 新闻 REST  {cnt:>4} 条  datetime+content+source ✓')
    elif cnt > 0:
        print(f'  ⚠️  新闻 REST  {cnt:>4} 条  字段不完整: {list(first.keys()) if rows else "N/A"}')
    else:
        print(f'  ⚠️  新闻 REST  {cnt:>4} 条  - 可能无新闻或数据源异常')
    # SSE
    lines = read_sse_lines(f'{BASE_URL}/api/stream/news', timeout=8, max_lines=10)
    if lines and lines[0].startswith('_error'):
        print(f'  ❌ 新闻 SSE  {lines[0]}')
        return
    data_lines = [l for l in lines if l.startswith('data:')]
    if data_lines:
        print(f'  ✅ 新闻 SSE  {len(data_lines)} 条消息')
    else:
        print(f'  ⚠️  新闻 SSE  无 data 消息（60s 间隔可能还没到）')


def check_predict():
    hr('3.7. 智能预测端点检查（V2.0.0+）')
    # 1. analyze
    data = fetch_json(f'{BASE_URL}/api/predict/analyze/stock/sh600519?period=1d&count=200', timeout=30)
    if '_error' in data:
        print(f'  ❌ predict/analyze 连接失败: {data["_error"]}')
        return
    cl = data.get('chanlun', {})
    has_bi = cl.get('has_bi', False)
    buy_pts = cl.get('buy_points', [])
    sell_pts = cl.get('sell_points', [])
    zs_list = cl.get('zhongshu_list', [])
    score = data.get('score', {})
    qf = data.get('quant_factors', {})
    total_score = score.get('total_score', 0)
    quant_score = qf.get('quant_score', 0)
    # 缠论
    if has_bi:
        print(f'  ✅ chanlun.has_bi=true  buy={len(buy_pts)} sell={len(sell_pts)} 中枢={len(zs_list)}')
    else:
        print(f'  ⚠️  chanlun.has_bi=false  (K线数据不足或无笔)')
    # 10因子
    q_keys = [f'q{i}' for i in range(1, 11)]
    q_ok = all(qf.get(k) is not None for k in q_keys)
    if q_ok and quant_score > 0:
        print(f'  ✅ 10因子完整  quant_score={quant_score}')
    else:
        print(f'  ⚠️  10因子不完整  keys present: {sum(1 for k in q_keys if k in qf)}/10')
    # 评分
    if total_score > 0:
        print(f'  ✅ 综合评分={total_score:.0f}/100')
    else:
        print(f'  ⚠️  综合评分=0')
    # 回测
    bt = data.get('backtest', {})
    all_stats = bt.get('stats', {}).get('all', {})
    if all_stats:
        n = all_stats.get('sample_count', 0)
        wr = all_stats.get('win_rate', 0)
        print(f'  ✅ 回测 {n}笔 胜率{wr}%')
    else:
        print(f'  ⚠️  回测 stats 为空')
    # 2. fundamental
    fund = fetch_json(f'{BASE_URL}/api/fundamental/stock/sh600519', timeout=10)
    if '_error' not in fund:
        avail = fund.get('available', False)
        if avail:
            print(f'  ✅ 基本面 available=true  PE={fund.get("pe",0):.1f}')
        else:
            print(f'  ⚠️  基本面 available=false')
    else:
        print(f'  ⚠️  fundamental 端点失败')
    # 3. 非A股基本面
    fund_hk = fetch_json(f'{BASE_URL}/api/fundamental/hk/hk00700', timeout=5)
    if '_error' not in fund_hk and fund_hk.get('available') == False:
        print(f'  ✅ 非A股基本面 available=false（预期）')
    elif '_error' not in fund_hk:
        print(f'  ⚠️  非A股基本面 available={fund_hk.get("available")}（应为false）')


def check_rules():
    hr('4. 铁律自检')

    # 铁律 3: 零本地存储
    print('\n  [铁律 3] 零本地存储 - 检查 backend/ 有无业务写盘')
    open_writes = []
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, 'backend')):
        if '__pycache__' in root or '.pyc' in root or '/.' in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for i, line in enumerate(fp, 1):
                        if re.search(r"\bopen\([^)]*['\"]w['\"]", line):
                            if 'logging.' not in line and 'self.write' not in line and '#' not in line.split('open')[0]:
                                open_writes.append(f'{path}:{i}: {line.strip()[:80]}')
                        elif re.search(r'\.write\(', line) and 'self.write' not in line and 'resp.write' not in line:
                            if '#' not in line.split('.write')[0]:
                                open_writes.append(f'{path}:{i}: {line.strip()[:80]}')
            except Exception:
                pass
    if open_writes:
        print(f'    ⚠️  疑似 {len(open_writes)} 处业务写盘:')
        for w in open_writes[:5]:
            print(f'      - {w}')
    else:
        print('    ✅ 无业务写盘')

    # 铁律 4: 免费 API
    print('\n  [铁律 4] 免费 API - 检查有无 api_key/token/secret 硬编码')
    paid = []
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, 'backend')):
        if '__pycache__' in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for i, line in enumerate(fp, 1):
                        if re.search(r'(api_key|token|secret)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                            if line.strip().startswith('#'):
                                continue
                            paid.append(f'{path}:{i}: {line.strip()[:80]}')
            except Exception:
                pass
    if paid:
        print(f'    ⚠️  疑似 {len(paid)} 处收费配置:')
        for p in paid[:5]:
            print(f'      - {p}')
    else:
        print('    ✅ 无收费 API 配置')

    # 铁律 1: 核心文件最近改动
    print('\n  [铁律 1] 核心文件最近 commit:')
    for cf in CORE_FILES:
        full = os.path.join(PROJECT_ROOT, cf)
        if not os.path.exists(full):
            print(f'    ⚠️  {cf} 不存在')
            continue
        try:
            r = subprocess.run(
                ['git', 'log', '--oneline', '-3', '--', cf],
                cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=5
            )
            log = r.stdout.strip() or '无 commit'
            lines = log.split('\n')
            print(f'    {cf}')
            for l in lines[:3]:
                print(f'      {l}')
        except Exception as e:
            print(f'    ⚠️  {cf} git 检查失败: {e}')


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else 'all'
    actions = {
        'modules': [check_modules],
        'sse': [check_sse],
        'kline': [check_kline],
        'news': [check_news],
        'predict': [check_predict],
        'rules': [check_rules],
        'diff': [check_rules],
        'all': [check_modules, check_sse, check_kline, check_news, check_predict, check_rules],
    }
    if arg not in actions:
        print(f'用法: {sys.argv[0]} [all|modules|sse|kline|news|predict|rules|diff]')
        sys.exit(1)
    for fn in actions[arg]:
        try:
            fn()
        except Exception as e:
            print(f'\n❌ {fn.__name__} 异常: {e}')

    print('\n' + '=' * 60)
    print('验收完成')
    print('=' * 60)


if __name__ == '__main__':
    main()
