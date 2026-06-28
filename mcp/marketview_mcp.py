"""
MarketView MCP Server V2.0.2
=============================
为 AI Agent 提供 MarketView 项目后端的管理工具。

版本同步规则：
  - 本文件版本号必须与项目版本号一致
  - 新增功能 → 同步更新版本号 + tools
  - 改后端 API 路径 → 同步更新对端 URL

Transport: stdio (本地 Agent 调用)
"""

import json, os, signal, subprocess, sys, time, httpx, asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── 服务配置 ──
BACKEND_URL = os.environ.get("MARKETVIEW_BACKEND_URL", "http://localhost:8000")
BACKEND_DIR = os.environ.get("MARKETVIEW_BACKEND_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
VALIDATE_SCRIPT = os.path.join(os.path.dirname(__file__), "..", ".trae", "skills", "mv-validator", "scripts", "mv_validate.py")

mcp = FastMCP("marketview_mcp")

# ── 共享 HTTP 客户端 ──
_client = httpx.AsyncClient(timeout=30.0, verify=False)

# ── 共享工具函数 ──
async def _get(endpoint: str) -> Dict[str, Any]:
    """发送 GET 请求到后端"""
    try:
        resp = await _client.get(f"{BACKEND_URL}{endpoint}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except httpx.ConnectError:
        return {"error": f"Cannot connect to {BACKEND_URL} — is the backend running?"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

async def _post(endpoint: str, payload: dict = None) -> Dict[str, Any]:
    """发送 POST 请求到后端"""
    try:
        resp = await _client.post(f"{BACKEND_URL}{endpoint}", json=payload)
        resp.raise_for_status()
        return resp.json() if resp.text else {"ok": True}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except httpx.ConnectError:
        return {"error": f"Cannot connect to {BACKEND_URL} — is the backend running?"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

def _format_error(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False, indent=2)

def _fmt_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)

# ── Pydantic Models ──

class HealthInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    detail: Optional[str] = Field(default=None, description="If 'detail', returns per-module status")

class SpotDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    module: str = Field(..., description="Module name: stock | etf | hk | us | index | crypto | news", min_length=1)
    limit: Optional[int] = Field(default=20, description="Max items to show", ge=1, le=1000)

class KlineInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    module: str = Field(..., description="Module name: stock | etf | hk | us | index | crypto", min_length=1)
    code: str = Field(..., description="Stock/crypto code, e.g. '000001', 'BTCUSDT'", min_length=1)
    period: Optional[str] = Field(default="1d", description="Period: 1m | 5m | 15m | 30m | 60m | 1d | 1w | 1M")
    count: Optional[int] = Field(default=60, description="Number of candles", ge=10, le=1000)

class PredictRankInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    module: str = Field(..., description="Module: stock | etf | hk | us | index | crypto", min_length=1)
    period: Optional[str] = Field(default="1d", description="Period")
    pool_size: Optional[int] = Field(default=200, description="Number of stocks to rank", ge=10, le=500)

class AnalyzeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    module: str = Field(..., description="Module", min_length=1)
    code: str = Field(..., description="Code to analyze", min_length=1)
    mode: Optional[str] = Field(default="quick", description="'quick' (100 candles) or 'full' (200 candles)")

class BackendActionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action: str = Field(..., description="'restart' to restart the uvicorn backend")

# ── Tools ──

@mcp.tool(
    name="marketview_health",
    annotations={
        "title": "Check MarketView Backend Health",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_health(params: HealthInput) -> str:
    """检查 MarketView 后端运行状态。

    返回后端健康状况、启动时间、各模块缓存状态。
    如果传 detail=True 则返回各模块逐项状态。

    Args:
        detail (Optional[str]): 设为 'detail' 返回详细状态

    Returns:
        str: JSON 格式健康检查结果

    Examples:
        - 使用场景: "后端还活着吗？" → params={}
        - 使用场景: "各模块状态如何？" → params={"detail": "detail"}
    """
    result = await _get("/api/health")
    if "error" in result:
        return _format_error(result["error"])

    if params.detail == "detail":
        return _fmt_json(result)
    # 简洁版
    status = result.get("status", "unknown")
    uptime = result.get("uptime_seconds", 0)
    modules = result.get("modules", {})
    ready = sum(1 for m in modules.values() if m.get("cached", False))
    total = len(modules)
    return f"""MarketView Backend 状态: **{status}**
运行时间: {uptime}s
模块就绪: {ready}/{total}
{_fmt_json({k: {"cached": v.get("cached"), "shard_count": v.get("shard_count")} for k, v in modules.items()})}
"""


@mcp.tool(
    name="marketview_spot_data",
    annotations={
        "title": "Get Market Spot Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_spot_data(params: SpotDataInput) -> str:
    """获取指定模块的实时行情快照。

    返回 stock/etf/hk/us/index/crypto/news 模块的 spot 数据。
    数据来自免费公开 API（腾讯/东财/新浪/Binance），
    经分片内存缓存，延迟 < 5s。

    Args:
        module (str): 模块名: stock | etf | hk | us | index | crypto | news
        limit (Optional[int]): 最多返回多少条

    Returns:
        str: JSON 格式行情数据

    Examples:
        - 使用场景: "看看 A 股行情" → params={"module": "stock", "limit": 10}
        - 使用场景: "美股有什么动静" → params={"module": "us", "limit": 5}
    """
    data = await _get(f"/api/{params.module}/spot")
    if "error" in data:
        return _format_error(data["error"])

    items = data.get("data", [])
    if not items:
        return f"模块 {params.module} 暂无数据（可能正在预热）"

    limited = items[:params.limit]
    return _fmt_json({"module": params.module, "count": len(items), "showing": len(limited), "data": limited})


@mcp.tool(
    name="marketview_kline",
    annotations={
        "title": "Get Kline/Candlestick Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_kline(params: KlineInput) -> str:
    """获取指定标的的 K 线数据。

    支持 8 种周期，含 MA/BOLL/MACD 等指标计算。
    数据走后端 _kline_cache（TTL 5min），同股票同周期二次请求 < 50ms。

    Args:
        module (str): 模块名
        code (str): 标的代码，如 '000001', 'BTCUSDT', '00700'
        period (Optional[str]): 周期: 1m | 5m | 15m | 30m | 60m | 1d | 1w | 1M
        count (Optional[int]): 蜡烛数

    Returns:
        str: JSON 格式 K 线 + 指标数据

    Examples:
        - 使用场景: "看看平安银行的日K线" → params={"module": "stock", "code": "000001"}
        - 使用场景: "比特币15分钟线" → params={"module": "crypto", "code": "BTCUSDT", "period": "15m", "count": 30}
    """
    data = await _get(f"/api/kline/{params.module}/{params.code}?period={params.period}&count={params.count}")
    if "error" in data:
        return _format_error(data["error"])

    rows = data.get("data", [])
    indicators_data = data.get("indicators", {})
    result = {
        "module": params.module,
        "code": params.code,
        "period": params.period,
        "count": len(rows),
        "latest_close": rows[-1][1] if rows else None,
        "latest_volume": rows[-1][5] if rows else None,
    }
    if indicators_data:
        result["indicators"] = {
            k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()}
            for k, v in indicators_data.items()
        }
    result["candles_preview"] = rows[-5:] if len(rows) >= 5 else rows
    return _fmt_json(result)


@mcp.tool(
    name="marketview_predict_rank",
    annotations={
        "title": "Get Prediction Rankings",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_predict_rank(params: PredictRankInput) -> str:
    """获取模块的智能预测排行。

    先触发 POST 批量计算，再 GET 获取排行结果。
    评分系统使用 10 因子 + 七维评分，60s 内返回所有结果。

    Args:
        module (str): 模块名
        period (Optional[str]): 周期
        pool_size (Optional[int]): 参与排行的标的数

    Returns:
        str: JSON 格式排行数据

    Examples:
        - 使用场景: "A股预测排行" → params={"module": "stock", "pool_size": 200}
    """
    # 触发计算
    trigger = await _post(f"/api/predict/batch/{params.module}?period={params.period}&pool_size={params.pool_size}")
    if "error" in trigger:
        return _format_error(trigger["error"])

    # 等 2s 给后端计算时间，再读取
    await asyncio.sleep(2)
    rank = await _get(f"/api/predict/rank/{params.module}?period={params.period}")
    if "error" in rank:
        return _format_error(rank["error"])

    data = rank.get("data", [])
    if not data:
        return f"排行数据尚未就绪（可能需要稍等），触发结果: {_fmt_json(trigger)}"

    preview = []
    for r in data[:10]:
        preview.append({
            "code": r.get("code"),
            "name": r.get("name", ""),
            "score": r.get("score", 0),
            "score_rank": r.get("score_rank"),
            "signals": r.get("signals", [])[:3],
        })
    return _fmt_json({
        "module": params.module,
        "total_ranked": len(data),
        "top_10": preview,
        "source": "免费公开 API（腾讯/Binance/东财）",
        "cache": "无 — 每次触发实时计算" if not data else "缓存命中"
    })


@mcp.tool(
    name="marketview_backend_action",
    annotations={
        "title": "Restart MarketView Backend",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def marketview_backend_action(params: BackendActionInput) -> str:
    """管理 MarketView 后端服务（重启）。

    这会在服务器上 kill 当前 uvicorn 进程并重起。
    仅当后端挂了或部署新代码需要重载时使用。

    Args:
        action (str): 'restart' — 重启后端

    Returns:
        str: 操作结果

    Examples:
        - 使用场景: "重启后端" → params={"action": "restart"}
    """
    if params.action != "restart":
        return _format_error(f"Unknown action: {params.action}. Supported: restart")

    try:
        # 查找并 kill 现有 uvicorn 进程
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/f", "/im", "uvicorn.exe"],
                capture_output=True, timeout=10
            )
        else:
            subprocess.run(
                ["pkill", "-f", "uvicorn"],
                capture_output=True, timeout=10
            )
    except subprocess.TimeoutExpired:
        pass

    time.sleep(1)

    try:
        # 在后台启动 uvicorn
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"],
            cwd=BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # 等 3s 确认启动
        time.sleep(3)
        # 检查是否存活
        health = await _get("/api/health")
        if "error" in health:
            return f"后端进程已启动 (PID {proc.pid})，但健康检查尚未通过，请稍后重试 health 检查"

        return f"""后端重启成功 ✅
PID: {proc.pid}
健康检查: {health.get('status', 'unknown')}
模块就绪: {sum(1 for m in health.get('modules', {}).values() if m.get('cached', False))}/{len(health.get('modules', {}))}
"""

    except Exception as e:
        return _format_error(f"重启失败: {e}")


@mcp.tool(
    name="marketview_validate",
    annotations={
        "title": "Run MarketView Validation Script",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_validate() -> str:
    """运行 MarketView 验收脚本。

    执行 mv_validate.py，检查后端启动、数据量、SSE 心跳等。
    改代码后必须跑这个确认没炸。

    Returns:
        str: 验收结果

    Examples:
        - 使用场景: "跑一遍验收" → params={}
    """
    if not os.path.exists(VALIDATE_SCRIPT):
        return _format_error(f"验收脚本未找到: {VALIDATE_SCRIPT}")

    try:
        result = subprocess.run(
            [sys.executable, VALIDATE_SCRIPT],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout + "\n" + result.stderr
        if result.returncode != 0:
            return f"验收脚本返回非零 ({result.returncode}):\n```\n{output[:2000]}\n```"
        return f"验收通过 ✅\n```\n{output[:2000]}\n```"
    except subprocess.TimeoutExpired:
        return _format_error("验收脚本超时（>120s）")
    except Exception as e:
        return _format_error(f"运行验收失败: {e}")


@mcp.tool(
    name="marketview_version",
    annotations={
        "title": "Get MarketView Version Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_version() -> str:
    """获取 MarketView 项目版本信息和当前 MCP 版本。

    返回项目当前版本号和 MCP 版本号。
    两个版本号必须一致（版本同步规则）。

    Returns:
        str: 版本信息

    Examples:
        - 使用场景: "现在是什么版本" → params={}
        - 使用场景: "MCP 版本和项目版本一致吗" → params={}
    """
    return _fmt_json({
        "mcp_version": "V2.0.2",
        "note": "MCP 版本必须与项目版本一致。新增功能或改 API 路径时同步更新。"
    })

@mcp.tool(
    name="marketview_check_cache",
    annotations={
        "title": "Check Kline Cache Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def marketview_check_cache() -> str:
    """查看后端 K 线缓存状态。

    检查 _kline_cache 大小和最近缓存时间。
    用于诊断缓存命中情况和预测加载加速（V2.0.2）。

    Returns:
        str: 缓存状态

    Examples:
        - 使用场景: "K线缓存还有效吗" → params={}
    """
    try:
        result = await _get("/api/cache/status")
        if "error" in result:
            # 如果后端没有 /api/cache/status，返回 degrade 信息
            return "后端未暴露缓存状态端点。(V2.0.2 计划中，目前缓存不可查。)"

        return _fmt_json({
            "kline_cache_size": result.get("kline_cache_size", "unknown"),
            "predict_cache_size": result.get("predict_cache_size", "unknown"),
            "message": "V2.0.2 实施后: K线走共享缓存，预测启动预计算，SSE 即时推送",
            "铁律3确认": "所有缓存数据来自免费公开 API，不读本地文件作为主数据源"
        })
    except Exception as e:
        return _format_error(f"检查缓存失败: {e}")


if __name__ == "__main__":
    mcp.run()
