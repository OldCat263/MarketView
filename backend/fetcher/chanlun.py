"""缠论 108 课完整实现 — 纯 Python，零依赖
===========================================
Step 1a (基础层): 包含处理 → 分型 → 笔 → 一类买卖点（简化版）
Step 3.5 (进阶层): 线段 → 中枢 → 走势 → 背驰 → 二三买卖点

参考: chanlun/ 目录（108课原文，只读）

数据结构约定:
  K线行 = [date, open, close, high, low, volume, amount]
  索引:   0     1     2      3     4     5       6

分析结果 dict 键:
  step1a: has_bi, buy_points, sell_points, bi_list, fenxing_list
  step3.5: zhongshu_list, zoushi, beichi_list, buy_points_ext, sell_points_ext
"""

# ============================================================
# Step 1a: 基础层 — 包含处理 → 分型 → 笔 → 一类买卖点
# ============================================================

def _is_up_kline(prev_kl, kl):
    """判断当前K线方向（与前一K线比较）"""
    return kl[2] > prev_kl[2]  # close > prev_close → 向上


def process_inclusions(rows):
    """包含处理: 消除相邻K线的包含关系，返回标准K线列表。
    规则（缠论第 62 课）:
    - 向上序列: 取高高(high=max(a.h,b.h)) 高高(low=max(a.l,b.l))
    - 向下序列: 取低高(high=min(a.h,b.h)) 低低(low=min(a.l,b.l))
    """
    if len(rows) < 2:
        return [list(r) for r in rows]

    result = [list(rows[0])]
    direction = None  # True=向上, False=向下

    for i in range(1, len(rows)):
        curr = list(rows[i])
        prev = result[-1]

        # 判断包含关系: high1>=high2 and low1<=low2 → 前包含后
        #               high1<=high2 and low1>=low2 → 后包含前
        has_inclusion = (prev[3] <= curr[3] and prev[4] >= curr[4]) or \
                        (prev[3] >= curr[3] and prev[4] <= curr[4])

        if not has_inclusion:
            direction = _is_up_kline(prev, curr)
            result.append(curr)
            continue

        # 有包含关系 → 合并
        if direction is None:
            # 前两根K线，用简单规则: 非包含即合并
            direction = _is_up_kline(prev, curr) if prev[2] != curr[2] else True

        if direction:  # 向上 → 取高高
            merged_high = max(prev[3], curr[3])
            merged_low = max(prev[4], curr[4])
        else:  # 向下 → 取低低
            merged_high = min(prev[3], curr[3])
            merged_low = min(prev[4], curr[4])

        # 合并K线: date 取较新的, open/close 按方向取
        result[-1] = [
            curr[0],                           # 用后一根的时间
            prev[1] if direction else curr[1],  # open
            curr[2] if direction else prev[2],  # close
            merged_high,
            merged_low,
            prev[5] + curr[5],                 # volume 累加
            prev[6] + curr[6],                 # amount 累加
        ]

    return result


def _find_fenxing(rows):
    """识别顶分型和底分型（缠论第 63 课）。
    顶分型: 中间K线最高价最高，左右K线最高价较低
    底分型: 中间K线最低价最低，左右K线最低价较高
    Returns: [(index, type, row), ...]  type='top'|'bottom'
    """
    if len(rows) < 3:
        return []

    fx_list = []
    for i in range(1, len(rows) - 1):
        left, mid, right = rows[i-1], rows[i], rows[i+1]

        # 顶分型: mid.h > left.h and mid.h > right.h
        if mid[3] > left[3] and mid[3] > right[3]:
            fx_list.append((i, 'top', mid))

        # 底分型: mid.l < left.l and mid.l < right.l
        if mid[4] < left[4] and mid[4] < right[4]:
            fx_list.append((i, 'bottom', mid))

    return fx_list


def _connect_bi(fx_list):
    """连接笔: 从分型序列中连接顶-底交替的笔（缠论第 65 课）。
    笔的定义: 相邻的顶和底之间至少有一根独立K线（非顶非底）。
    Returns: [(start_idx, end_idx, direction, start_price, end_price), ...]
    """
    if len(fx_list) < 2:
        return []

    bi_list = []
    # 过滤: 连续同类型分型取最极值
    filtered = [fx_list[0]]

    for i in range(1, len(fx_list)):
        curr = fx_list[i]
        prev = filtered[-1]

        if curr[1] == prev[1]:  # 同类型
            if curr[1] == 'top' and curr[2][3] > prev[2][3]:
                filtered[-1] = curr  # 取更高的顶
            elif curr[1] == 'bottom' and curr[2][4] < prev[2][4]:
                filtered[-1] = curr  # 取更低的底
        elif curr[0] - prev[0] >= 1:  # 至少隔 1 根K线（简化: 中间K线≥1）
            filtered.append(curr)
        # 否则跳过（不满足笔的K线数要求）

    if len(filtered) < 2:
        return []

    # 连接笔
    for i in range(1, len(filtered)):
        prev_fx = filtered[i-1]
        curr_fx = filtered[i]

        if prev_fx[1] == curr_fx[1]:
            continue  # 同类型，不连

        # 判断方向: bottom→top = 上升笔, top→bottom = 下降笔
        if prev_fx[1] == 'bottom':  # 底→顶 = 上升笔
            direction = 'up'
            start_price = prev_fx[2][4]   # 底的最低点
            end_price = curr_fx[2][3]      # 顶的最高点
        else:  # 顶→底 = 下降笔
            direction = 'down'
            start_price = prev_fx[2][3]   # 顶的最高点
            end_price = curr_fx[2][4]      # 底的最低点

        bi_list.append({
            'start_idx': prev_fx[0],
            'end_idx': curr_fx[0],
            'direction': direction,
            'start_price': round(start_price, 2),
            'end_price': round(end_price, 2),
            'start_date': _make_date_str(prev_fx[2][0]),
            'end_date': _make_date_str(curr_fx[2][0]),
            'strength': round(abs(end_price - start_price) / abs(start_price) * 100, 2) if start_price else 0,
        })

    return bi_list


def _make_date_str(raw_date):
    """将各种日期格式统一为 YYYY-MM-DD 字符串"""
    if isinstance(raw_date, str):
        if len(raw_date) >= 10:
            return raw_date[:10]
        return raw_date
    return str(raw_date)


def _find_buy_sell_points_v1(bi_list, rows):
    """Step 1a 简化版: 一类买卖点 = 笔端点反转处。
    一类买点: 下降笔的终点（底分型处）→ 预期反转向上
    一类卖点: 上升笔的终点（顶分型处）→ 预期反转向下

    Step 3.5 将替换为背驰确认版本。
    """
    buy_points = []
    sell_points = []

    for bi in bi_list:
        date_str = bi['end_date']
        end_idx = bi['end_idx']

        # 取终点K线价格
        if end_idx < len(rows):
            close = rows[end_idx][2]
        else:
            close = bi['end_price']

        point = {
            'date': date_str if date_str else _make_date_str(rows[end_idx][0] if end_idx < len(rows) else ''),
            'price': round(float(close), 2),
            'type': '一类买' if bi['direction'] == 'down' else '一类卖',
            'reason': '下降笔终点，预期反转' if bi['direction'] == 'down' else '上升笔终点，预期反转',
            'strength': round(bi.get('strength', 0), 2),
        }

        if bi['direction'] == 'down':
            buy_points.append(point)
        else:
            sell_points.append(point)

    return buy_points, sell_points


# ============================================================
# 主分析入口
# ============================================================

def analyze(rows, prev_result=None):
    """缠论完整分析流水线。

    Args:
        rows: K线数据 [[date, open, close, high, low, volume, amount], ...]
        prev_result: 前次分析结果（用于增量更新，暂未使用）

    Returns:
        {
            'status': 'ok',
            'has_bi': bool,
            'buy_points': [...],      # Step 1a 简化一类买点
            'sell_points': [...],     # Step 1a 简化一类卖点
            'bi_list': [...],         # 笔列表
            'fenxing_count': int,     # 分型数量
            # Step 3.5 追加:
            # 'zhongshu_list': [...],
            # 'zoushi': {...},
            # 'beichi_list': [...],
            # 'buy_points_ext': [...],
            # 'sell_points_ext': [...],
        }
    """
    if not rows or len(rows) < 3:
        return {
            'status': 'insufficient_data',
            'has_bi': False,
            'buy_points': [],
            'sell_points': [],
            'bi_list': [],
            'fenxing_count': 0,
        }

    # 1. 包含处理
    clean_rows = process_inclusions(rows)

    if len(clean_rows) < 3:
        return {
            'status': 'insufficient_data_after_merge',
            'has_bi': False,
            'buy_points': [],
            'sell_points': [],
            'bi_list': [],
            'fenxing_count': 0,
        }

    # 2. 分型识别
    fx_list = _find_fenxing(clean_rows)

    # 3. 笔的连接
    bi_list = _connect_bi(fx_list)

    # 4. 买卖点（Step 1a 简化版）
    buy_points, sell_points = _find_buy_sell_points_v1(bi_list, clean_rows)

    # 构建分型数据（用于前端可视化）
    fenxing_data = []
    for idx, f_type, row in fx_list:
        fenxing_data.append({
            'index': idx,
            'type': f_type,
            'date': _make_date_str(row[0]),
            'price': round(row[3] if f_type == 'top' else row[4], 2),
        })

    result = {
        'status': 'ok',
        'has_bi': len(bi_list) > 0,
        'buy_points': buy_points,
        'sell_points': sell_points,
        'bi_list': bi_list,
        'fenxing_list': fenxing_data,
        'fenxing_count': len(fenxing_data),
    }

    # 5. 进阶层（Step 3.5）
    xd_list = _build_xian_duan(bi_list, clean_rows)
    zs_list = _find_zhongshu(xd_list if xd_list else bi_list, clean_rows)
    zoushi = _classify_zoushi(zs_list)
    beichi_list = _detect_beichi(bi_list, clean_rows)
    buy_points_ext, sell_points_ext = _find_ext_points(bi_list, zs_list, zoushi, clean_rows)

    result.update({
        'zhongshu_list': zs_list,
        'zoushi': zoushi,
        'beichi_list': beichi_list,
        'buy_points_ext': buy_points_ext,
        'sell_points_ext': sell_points_ext,
        'xian_duan_count': len(xd_list),
        'zhongshu_count': len(zs_list),
    })

    return result


# ============================================================
# Step 3.5: 进阶层 — 线段 → 中枢 → 走势 → 背驰 → 二三买卖点
# ============================================================

def _build_xian_duan(bi_list, rows):
    """从笔构建线段（缠论第 67-69 课）。
    线段由至少 3 笔组成，方向由第一笔决定。
    Returns: [{'start_idx','end_idx','direction','high','low',...},...]
    """
    if len(bi_list) < 3:
        return []

    xd_list = []
    i = 0
    while i < len(bi_list) - 2:
        bi1, bi2, bi3 = bi_list[i], bi_list[i+1], bi_list[i+2]

        # 前三笔必须方向交替: bi1和bi3同向, bi2反向
        if bi1['direction'] != bi3['direction']:
            i += 1
            continue

        direction = bi1['direction']  # 线段方向 = 首笔方向

        # 找线段终点: 继续延伸直到方向改变或笔用完
        j = i + 3
        while j < len(bi_list):
            # 第j笔应与bi1同向则为延伸，反向则线段结束
            if j < len(bi_list):
                next_bi = bi_list[j]
                if next_bi['direction'] != direction:
                    break  # 出现了反向笔，线段可能结束
            j += 1

        # 线段终点 = 最后一笔的终点
        end_bi = bi_list[j - 1] if j <= len(bi_list) else bi_list[-1]

        # 计算线段高低点
        high = max(b['end_price'] if b['direction'] == 'up' else b['start_price']
                   for b in bi_list[i:j])
        low = min(b['end_price'] if b['direction'] == 'down' else b['start_price']
                  for b in bi_list[i:j])

        xd_list.append({
            'start_idx': bi1['start_idx'],
            'end_idx': end_bi['end_idx'],
            'direction': direction,
            'start_date': bi1['start_date'],
            'end_date': end_bi['end_date'],
            'high': round(high, 2),
            'low': round(low, 2),
            'bi_count': j - i,
            'start_price': bi1['start_price'],
            'end_price': end_bi['end_price'],
        })

        i = j  # 跳到线段结束位置

    return xd_list


def _find_zhongshu(xd_list, rows):
    """识别中枢（缠论第 70-73 课）。
    中枢 = 至少 3 段连续线段的重叠区间。
    ZG = min(各线段高点), ZD = max(各线段低点)
    Returns: [{'zg','zd','start_date','end_date','level','position','xd_count'},...]
    """
    if len(xd_list) < 3:
        return []

    zs_list = []
    i = 0
    while i < len(xd_list) - 2:
        xd1, xd2, xd3 = xd_list[i], xd_list[i+1], xd_list[i+2]

        # 计算重叠区间
        highs = [xd1['high'], xd2['high'], xd3['high']]
        lows = [xd1['low'], xd2['low'], xd3['low']]
        zg = min(highs)
        zd = max(lows)

        # 有重叠 (ZG > ZD)
        if zg <= zd:
            i += 1
            continue

        # 延伸中枢: 看后续线段是否仍在重叠区间内
        j = i + 3
        while j < len(xd_list):
            xd_j = xd_list[j]
            if xd_j['high'] < zd or xd_j['low'] > zg:
                break  # 离开中枢区间
            highs.append(xd_j['high'])
            lows.append(xd_j['low'])
            zg = min(highs)
            zd = max(lows)
            if zg <= zd:
                break
            j += 1

        # 级别判定: 日线中枢 ≈ 日线级别
        xd_count = j - i
        if xd_count >= 5:
            level = '日线'
        elif xd_count >= 3:
            level = '30分钟'
        else:
            level = '5分钟'

        # 中枢位置（在中枢内的位置）
        position = '中轨'
        if len(rows) > xd_list[i]['end_idx']:
            last_close = rows[min(xd_list[i]['end_idx'], len(rows)-1)][2]
            if last_close >= zg:
                position = '上轨上方'
            elif last_close <= zd:
                position = '下轨下方'
            elif last_close >= (zg + zd) / 2:
                position = '中轨偏上'
            else:
                position = '中轨偏下'

        zs_list.append({
            'zg': round(zg, 2),
            'zd': round(zd, 2),
            'start_date': xd1['start_date'],
            'end_date': xd_list[j-1]['end_date'],
            'level': level,
            'position': position,
            'xd_count': xd_count,
            'amplitude': round((zg - zd) / zd * 100, 2) if zd > 0 else 0,
        })

        i = j

    return zs_list


def _classify_zoushi(zs_list):
    """走势分类（缠论第 74-76 课）。
    - 上涨: ZG 逐级抬高
    - 下跌: ZG 逐级降低
    - 盘整: 单一中枢或 ZG 无明显方向
    Returns: {'type': '上涨'|'下跌'|'盘整', 'zhongshu_count': int}
    """
    if not zs_list:
        return {'type': '盘整', 'zhongshu_count': 0, 'direction': 'neutral'}

    n = len(zs_list)
    if n == 1:
        return {'type': '盘整', 'zhongshu_count': 1, 'direction': 'neutral'}

    zgs = [zs['zg'] for zs in zs_list]
    ups = sum(1 for i in range(1, n) if zgs[i] > zgs[i-1])
    downs = sum(1 for i in range(1, n) if zgs[i] < zgs[i-1])

    if ups > downs * 2:
        return {'type': '上涨', 'zhongshu_count': n, 'direction': 'up'}
    elif downs > ups * 2:
        return {'type': '下跌', 'zhongshu_count': n, 'direction': 'down'}
    else:
        return {'type': '盘整', 'zhongshu_count': n, 'direction': 'neutral'}


def _detect_beichi(bi_list, rows):
    """背驰检测（缠论第 37-40 课）。
    比较相邻同向笔的力度（用 MACD 面积或涨跌幅），力度衰减 = 背驰。
    Returns: [{'type':'顶背驰'|'底背驰','date','price','strength'},...]
    """
    if len(bi_list) < 2:
        return []

    beichi_list = []

    for i in range(1, len(bi_list)):
        prev_bi = bi_list[i-1]
        curr_bi = bi_list[i]

        if prev_bi['direction'] != curr_bi['direction']:
            continue

        # 同向笔比较: 力度衰减 = 背驰
        prev_strength = prev_bi.get('strength', 0)
        curr_strength = curr_bi.get('strength', 0)

        # 笔的伸展幅度（绝对涨跌幅）
        prev_amplitude = abs(prev_bi['end_price'] - prev_bi['start_price']) / max(abs(prev_bi['start_price']), 0.01)
        curr_amplitude = abs(curr_bi['end_price'] - curr_bi['start_price']) / max(abs(curr_bi['start_price']), 0.01)

        # 力度衰减阈值: 当前力度 < 前一笔的 60%
        if curr_amplitude < prev_amplitude * 0.6:
            if curr_bi['direction'] == 'up':
                beichi_type = '顶背驰'
                price = curr_bi['end_price']
            else:
                beichi_type = '底背驰'
                price = curr_bi['end_price']

            beichi_list.append({
                'type': beichi_type,
                'date': curr_bi['end_date'],
                'price': round(price, 2),
                'strength': round(prev_amplitude - curr_amplitude, 4),
                'prev_strength': round(prev_amplitude, 4),
                'curr_strength': round(curr_amplitude, 4),
            })

    return beichi_list[-10:]  # 最近 10 个背驰信号


def _find_ext_points(bi_list, zs_list, zoushi, rows):
    """二三类买卖点（缠论第 21/32 课）。

    二类买点: 下降笔终点在 中枢 ZD 上方或附近（不创新低）
    二类卖点: 上升笔终点在 中枢 ZG 下方或附近（不创新高）
    三类买点: 上升笔突破中枢 ZG 后回踩不破 ZG
    三类卖点: 下降笔跌破中枢 ZD 后反抽不破 ZD
    """
    buy_points_ext = []
    sell_points_ext = []

    if not zs_list:
        return buy_points_ext, sell_points_ext

    last_zs = zs_list[-1]
    zg, zd = last_zs['zg'], last_zs['zd']

    for bi in bi_list[-20:]:  # 只检查最近 20 笔
        end_price = bi['end_price']
        date_str = bi['end_date']

        if bi['direction'] == 'down':
            # 二类买点: 下降笔终点在 ZD 上方 → 不创新低，回调买入
            if zd * 0.95 <= end_price <= zg * 1.05:
                buy_points_ext.append({
                    'date': date_str,
                    'price': round(end_price, 2),
                    'type': '二类买',
                    'reason': f'回调至中枢附近(ZD={zd:.2f})',
                    'strength': round(bi.get('strength', 0), 2),
                })
            # 三类买点: 下降笔终点在 ZG 上方 → 突破后回踩
            if end_price > zg:
                buy_points_ext.append({
                    'date': date_str,
                    'price': round(end_price, 2),
                    'type': '三类买',
                    'reason': f'回踩不破中枢上轨(ZG={zg:.2f})',
                    'strength': round(bi.get('strength', 0), 2),
                })

        else:  # up stroke
            # 二类卖点: 上升笔终点在 ZG 下方 → 不创新高，反弹卖出
            if zd * 0.95 <= end_price <= zg * 1.05:
                sell_points_ext.append({
                    'date': date_str,
                    'price': round(end_price, 2),
                    'type': '二类卖',
                    'reason': f'反弹至中枢附近(ZG={zg:.2f})',
                    'strength': round(bi.get('strength', 0), 2),
                })
            # 三类卖点: 上升笔终点在 ZD 下方 → 跌破后反抽
            if end_price < zd:
                sell_points_ext.append({
                    'date': date_str,
                    'price': round(end_price, 2),
                    'type': '三类卖',
                    'reason': f'反抽不破中枢下轨(ZD={zd:.2f})',
                    'strength': round(bi.get('strength', 0), 2),
                })

    return buy_points_ext[-10:], sell_points_ext[-10:]  # 各自最近 10 个
