"""检查缓存问题"""
import json, os

cache_path = 'D:/服务器ETF/backend/.cache/spot_cache.json'
with open(cache_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# 模拟 _cached_get 的逻辑
for key in ['us', 'index']:
    c = d.get(key)
    if not c:
        print(f'{key}: NOT IN CACHE')
        continue
    
    shards = c.get('shards', {})
    if not shards:
        print(f'{key}: NO SHARDS')
        continue
    
    sorted_keys = sorted(shards.keys(), key=int)
    # Get first shard data
    first = None
    for i in sorted_keys:
        sd = shards[i].get('data')
        if sd is not None and sd != []:
            first = sd
            break
    
    if first is None:
        print(f'{key}: first shard data is None/empty')
        continue
    
    print(f'{key}: first data type={type(first).__name__}')
    
    if isinstance(first, dict):
        # index case: return shard 0's data directly
        print(f'  dict keys: {list(first.keys())}')
        for kk in first:
            print(f'  {kk}: {len(first[kk])} items')
            # Check if items are populated
            if first[kk]:
                print(f'    first item: {first[kk][0]}')
    elif isinstance(first, list):
        print(f'  list len: {len(first)}')
        if first:
            print(f'  first item keys: {list(first[0].keys())[:5]}')
            # Check if values look valid
            sample = {k: v for k, v in list(first[0].items())[:5]}
            print(f'  first item sample: {sample}')
            # Check for NaN
            nan_keys = [k for k, v in first[0].items() if v is None or (isinstance(v, float) and (v != v))]
            if nan_keys:
                print(f'  NaN/None keys: {nan_keys}')
