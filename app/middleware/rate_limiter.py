"""用量限制中间件 — 控制请求频率和每日配额"""
import time
import logging
from datetime import datetime, date
from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)

# 内存存储（适合单实例部署，重启后重置）
_daily_counts: dict[str, int] = {}  # {date_str: count}
_minute_windows: dict[str, list[float]] = {}  # {ip: [timestamps]}


def _get_client_ip(request: Request) -> str:
    """获取客户端IP（兼容代理）"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_daily_limit(request: Request) -> None:
    """检查每日请求配额，超出则拒绝"""
    today = date.today().isoformat()
    count = _daily_counts.get(today, 0)

    if count >= settings.daily_request_limit:
        logger.warning(f"Daily limit reached: {count}/{settings.daily_request_limit}")
        raise HTTPException(
            status_code=429,
            detail=f"今日请求已达上限（{settings.daily_request_limit}次），请明天再试。",
        )


def increment_daily_count() -> None:
    """增加每日计数"""
    today = date.today().isoformat()
    _daily_counts[today] = _daily_counts.get(today, 0) + 1


def get_usage_info() -> dict:
    """获取当前用量信息（用于前端展示）"""
    today = date.today().isoformat()
    used = _daily_counts.get(today, 0)
    return {
        "date": today,
        "used": used,
        "limit": settings.daily_request_limit,
        "remaining": settings.daily_request_limit - used,
    }


def check_rate_limit(request: Request) -> None:
    """检查每分钟速率限制"""
    ip = _get_client_ip(request)
    now = time.time()
    cutoff = now - 60  # 60秒窗口

    if ip not in _minute_windows:
        _minute_windows[ip] = []

    # 清理过期记录
    _minute_windows[ip] = [t for t in _minute_windows[ip] if t > cutoff]

    if len(_minute_windows[ip]) >= settings.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for IP {ip}")
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试。",
        )

    _minute_windows[ip].append(now)
