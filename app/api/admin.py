"""管理员路由 — 兑换码管理接口"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException

from app.config import settings
from app.services.code_store import code_store

admin_router = APIRouter(prefix="/admin", tags=["管理员"])


def _verify_admin_key(admin_key: Optional[str]) -> None:
    """验证管理员密钥"""
    if not admin_key or admin_key != settings.admin_key:
        raise HTTPException(
            status_code=403,
            detail="管理员密钥无效",
        )


@admin_router.post("/codes/generate")
async def generate_codes(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    count: int = 10,
    credits_per_code: int = 1,
):
    """
    批量生成兑换码。

    Header: X-Admin-Key
    Query params: count（数量）, credits_per_code（每个码的次数）
    """
    _verify_admin_key(x_admin_key)

    if count < 1 or count > 1000:
        raise HTTPException(status_code=400, detail="生成数量需在 1-1000 之间")
    if credits_per_code < 1 or credits_per_code > 100:
        raise HTTPException(status_code=400, detail="每个码的次数需在 1-100 之间")

    codes = code_store.generate_codes(count, credits_per_code)
    return {
        "count": len(codes),
        "credits_per_code": credits_per_code,
        "codes": codes,
    }


@admin_router.get("/codes/list")
async def list_codes(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    查看所有兑换码和统计信息。

    Header: X-Admin-Key
    """
    _verify_admin_key(x_admin_key)

    codes = code_store.get_all_codes()
    stats = code_store.get_stats()
    return {
        "stats": stats,
        "codes": codes,
    }
