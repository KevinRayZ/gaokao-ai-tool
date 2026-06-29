"""兑换码存储与管理 — JSON 文件持久化"""
import json
import os
import random
import string
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 兑换码字符集：排除容易混淆的 0/O/I/1
CODE_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8

# 数据文件路径：相对于项目根目录
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "redemption_codes.json"

# TODO: Railway 部署时，data 目录需要在 Volume 中才能持久化。
#       当前 MVP 使用本地文件，重启后已兑换记录不会丢失（因为文件持久化），
#       但如果 Railway 重建容器则文件会丢失。生产环境应使用数据库。


class CodeStore:
    """兑换码存储管理器（单例模式，模块级实例化）"""

    def __init__(self) -> None:
        self._codes: dict[str, dict] = {}
        self._ensure_data_dir()
        self._load()

    def _ensure_data_dir(self) -> None:
        """确保 data 目录存在"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """从 JSON 文件加载兑换码数据"""
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self._codes = json.load(f)
                logger.info(f"Loaded {len(self._codes)} redemption codes from {DATA_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load redemption codes: {e}")
                self._codes = {}
        else:
            logger.info(f"No existing redemption codes file, starting fresh")
            self._codes = {}

    def _save(self) -> None:
        """同步保存兑换码数据到 JSON 文件"""
        self._ensure_data_dir()
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self._codes, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Failed to save redemption codes: {e}")

    def _generate_single_code(self) -> str:
        """生成单个兑换码（8位，排除混淆字符）"""
        return "".join(random.choices(CODE_CHARSET, k=CODE_LENGTH))

    def generate_codes(self, count: int, credits_per_code: int) -> list[str]:
        """
        批量生成兑换码。

        Args:
            count: 生成数量
            credits_per_code: 每个码提供的分析次数

        Returns:
            生成的兑换码列表
        """
        now = datetime.now().isoformat()
        generated: list[str] = []

        for _ in range(count):
            # 确保生成的码不重复
            code = self._generate_single_code()
            while code in self._codes:
                code = self._generate_single_code()

            self._codes[code] = {
                "code": code,
                "credits": credits_per_code,
                "is_used": False,
                "used_at": None,
                "created_at": now,
            }
            generated.append(code)

        self._save()
        logger.info(f"Generated {count} redemption codes, each with {credits_per_code} credits")
        return generated

    def redeem_code(self, code: str) -> dict:
        """
        兑换一个码。

        Args:
            code: 兑换码字符串

        Returns:
            {"success": bool, "credits": int, "message": str}
        """
        code = code.strip().upper()

        if code not in self._codes:
            return {"success": False, "credits": 0, "message": "兑换码不存在"}

        record = self._codes[code]

        if record["is_used"]:
            return {"success": False, "credits": 0, "message": "兑换码已被使用"}

        # 标记为已使用
        record["is_used"] = True
        record["used_at"] = datetime.now().isoformat()
        credits = record["credits"]

        self._save()
        logger.info(f"Redemption code '{code}' redeemed for {credits} credits")
        return {
            "success": True,
            "credits": credits,
            "message": f"兑换成功！获得{credits}次分析次数",
        }

    def get_all_codes(self) -> list[dict]:
        """获取所有兑换码的状态列表"""
        return list(self._codes.values())

    def get_stats(self) -> dict:
        """获取兑换码统计信息"""
        total = len(self._codes)
        used = sum(1 for r in self._codes.values() if r["is_used"])
        unused = total - used
        total_credits_issued = sum(r["credits"] for r in self._codes.values())
        return {
            "total": total,
            "used": used,
            "unused": unused,
            "total_credits_issued": total_credits_issued,
        }


# 模块级单例实例
code_store = CodeStore()
