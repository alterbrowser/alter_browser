"""
通用工具 — seed 派生、确定性随机数。
"""
from __future__ import annotations

import hashlib
import random
from typing import Any, List, Sequence


def derive_int(seed: int, key: str, lo: int, hi: int) -> int:
    """
    从 (seed, key) 派生一个 [lo, hi] 范围的确定性整数。
    同一 (seed, key) 永远得到相同结果。

    >>> derive_int(12345, "cpu", 4, 16)
    8
    """
    h = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()
    n = int.from_bytes(h[:8], "big")
    return lo + (n % (hi - lo + 1))


def derive_choice(seed: int, key: str, options: Sequence[Any]) -> Any:
    """从 options 列表中按 (seed, key) 确定性选一个"""
    if not options:
        raise ValueError("empty options")
    idx = derive_int(seed, key, 0, len(options) - 1)
    return options[idx]


def derive_rng(seed: int, key: str) -> random.Random:
    """
    返回一个确定性 Random 实例。适用于需要 sample/shuffle 等复杂随机操作的场景。
    """
    h = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()
    # 取前 8 字节做 Random 的 seed
    sub_seed = int.from_bytes(h[:8], "big")
    return random.Random(sub_seed)


def derive_float(seed: int, key: str, lo: float, hi: float) -> float:
    """
    从 (seed, key) 派生 [lo, hi) 范围的确定性浮点数。
    """
    h = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()
    n = int.from_bytes(h[:8], "big")
    # 转换到 [0, 1)
    u = n / 2**64
    return lo + u * (hi - lo)


def random_seed() -> int:
    """生成一个随机 32 位 seed"""
    return random.randint(1, 2**31 - 1)


def safe_filename(name: str) -> str:
    """把任意字符串转成合法文件名（不含路径分隔符）"""
    bad = '<>:"/\\|?*'
    return "".join("_" if c in bad else c for c in name).strip()[:120]
