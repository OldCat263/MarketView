"""模块八：新闻 — 新浪财经 + 财新头条（V1.8.0+）
数据源：新浪财经 feed.mix.sina.com.cn（主）→ 财新头条 stock_news_main_cx（备）
字段：datetime（发布时间）、content（标题+摘要）、source（来源媒体）
刷新：60s 低频防限流，异常返回空数组不崩主流程

主源格式：
  URL: https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=50&page=1
  返回: JSON {result: {data: [{ctime: unix_ts, title: str, intro: str, media_name: str, url: str}, ...]}}
  转换: ctime → datetime(YYYY-MM-DD HH:MM:SS), title+intro → content, media_name → source, url → url
备源格式：
  函数: AKShare stock_news_main_cx() → DataFrame(tag, summary, url)
  转换: tag+summary → content, '财新头条' → source, datetime 为空
  仅主源失败时使用

原设计数据源 AKShare js_news → 金十数据，当前版本无此函数，
改用新浪财经直接 HTTP（免费公开 API，无需 Key）+ 财新头条 fallback（V1.8.0 设计师审批）
"""
import json
from datetime import datetime
import httpx


def _from_sina():
    """新浪财经新闻 — 直接 HTTP，50 条财经要闻"""
    url = ('https://feed.mix.sina.com.cn/api/roll/get'
           '?pageid=153&lid=2516&k=&num=50&page=1')
    try:
        r = httpx.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        data = r.json()
        items = data.get('result', {}).get('data', [])
        if not items:
            return []
        result = []
        for item in items:
            try:
                ts = int(item.get('ctime', 0))
                if ts <= 0:
                    continue
                dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                title = (item.get('title') or '').strip()
                intro = (item.get('intro') or '').strip()
                # content = 标题（如有摘要则追加）
                content = title
                if intro and intro != title:
                    content = title + '：' + intro
                media = (item.get('media_name') or '新浪财经').strip()
                news_url = (item.get('url') or '').strip()
                if title:
                    result.append({
                        'datetime': dt,
                        'content': content,
                        'source': media,
                        'url': news_url,
                    })
            except Exception:
                continue
        return result
    except Exception as e:
        print(f'[news] sina error: {e}')
        return []


def _from_caixin():
    """财新头条 — AKShare stock_news_main_cx，100 条"""
    try:
        import akshare as ak
        df = ak.stock_news_main_cx()
        if df is None or df.empty:
            return []
        result = []
        for _, row in df.iterrows():
            tag = str(row.get('tag', '')).strip()
            summary = str(row.get('summary', '')).strip()
            if not summary:
                continue
            content = f'【{tag}】{summary}' if tag else summary
            result.append({
                'datetime': '',  # 财新无时间字段
                'content': content,
                'source': '财新头条',
                'url': str(row.get('url', '')).strip(),
            })
        return result
    except Exception as e:
        print(f'[news] caixin error: {e}')
        return []


def get_news_json():
    """拉全量新闻 → JSON 字符串
    主源：新浪财经（50 条，有精确时间）
    备源：财新头条（100 条，无时间字段，仅主源为空时使用）
    """
    result = _from_sina()
    if not result:
        print('[news] sina empty, trying caixin fallback')
        result = _from_caixin()
    if not result:
        print('[news] all sources empty')
        return '[]'
    # 按时间倒序（有时间的排前面，无时间的排后面）
    result.sort(key=lambda x: x['datetime'] or '0', reverse=True)
    print(f'[news] fetched {len(result)} items (sina+caixin)')
    return json.dumps(result, ensure_ascii=False)


def fetch_news_shard(shard_id, total_shards):
    """分片拉取（新闻只有 1 个分片，直接返回全量）"""
    raw = get_news_json()
    return json.loads(raw) if isinstance(raw, str) else raw
