"""工具函数：安全转换 + DataFrame处理"""
import json

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
