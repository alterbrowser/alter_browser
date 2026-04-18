"""
Archetype 子模块 — 设备原型库

封装 ``archetype_library`` 子模块，暴露公开 API：

1. 导入 ARCHETYPES / FONTS_PRESETS / DeviceArchetype / ConfigurationVariant
2. 暴露 list_archetypes / random_archetype / find_archetype / validate_profile
3. 提供 ArchetypeProfileBuilder：Archetype → Profile 转换
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any

try:
    from .archetype_library import (
        ARCHETYPES,
        FONTS_PRESETS,
        DeviceArchetype,
        ConfigurationVariant,
        validate_profile,
        list_archetypes as _list_archetypes_raw,
        random_archetype as _random_archetype_raw,
    )
    ARCHETYPES_AVAILABLE = True
except ImportError as e:  # pragma: no cover
    ARCHETYPES_AVAILABLE = False
    ARCHETYPES = {}
    FONTS_PRESETS = {}
    _IMPORT_ERROR = e


# ============================================================
# 公开 API（包装 archetype_library 的原生函数）
# ============================================================

def get_archetype(archetype_id: str) -> DeviceArchetype:
    """按 id 获取 Archetype，不存在时抛 KeyError 并给出提示"""
    if not ARCHETYPES_AVAILABLE:
        raise RuntimeError(f"archetype_library 无法导入: {_IMPORT_ERROR}")
    if archetype_id not in ARCHETYPES:
        close = [k for k in ARCHETYPES.keys() if archetype_id.lower() in k.lower()]
        hint = f" (可能是: {', '.join(close[:5])})" if close else ""
        raise KeyError(f"unknown archetype: {archetype_id!r}{hint}")
    return ARCHETYPES[archetype_id]


def list_archetypes(
    region: Optional[str] = None,
    form_factor: Optional[str] = None,
    os_family: Optional[str] = None,
) -> List[DeviceArchetype]:
    """按条件列出 archetype；空条件返回全部"""
    if not ARCHETYPES_AVAILABLE:
        return []
    # archetype_library 原生 list_archetypes 可能参数不同，这里手动过滤
    result = []
    for arch in ARCHETYPES.values():
        if region and region not in (arch.prevalence_regions or []):
            continue
        if form_factor and not arch.form_factor.startswith(form_factor):
            continue
        if os_family and arch.os_family != os_family:
            continue
        result.append(arch)
    # 按市场权重降序
    result.sort(key=lambda a: -a.market_share_weight)
    return result


def random_archetype(
    seed: int,
    region: Optional[str] = None,
    form_factor: Optional[str] = None,
    os_family: Optional[str] = None,
) -> DeviceArchetype:
    """按权重随机选一个 archetype"""
    import random
    candidates = list_archetypes(region=region, form_factor=form_factor, os_family=os_family)
    if not candidates:
        raise ValueError(
            f"no archetype matches region={region} form_factor={form_factor} os={os_family}")
    rng = random.Random(seed)
    weights = [max(1, a.market_share_weight) for a in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def find_archetype_by_hint(gpu_hint: str = "", os_hint: str = "",
                           form_factor_hint: str = "") -> Optional[DeviceArchetype]:
    """按模糊文本匹配找 archetype（从已有 profile 迁移用）"""
    if not ARCHETYPES_AVAILABLE:
        return None
    best: Optional[DeviceArchetype] = None
    best_score = 0
    for arch in ARCHETYPES.values():
        score = 0
        if gpu_hint and gpu_hint.lower() in arch.gpu_renderer_template.lower():
            score += 3
        if os_hint and os_hint.lower() in arch.os_display_version.lower():
            score += 2
        if form_factor_hint and form_factor_hint in arch.form_factor:
            score += 1
        if score > best_score:
            best_score = score
            best = arch
    return best


# ============================================================
# ArchetypeProfileBuilder —— Archetype -> Profile 转换
# ============================================================

def build_profile_from_archetype(
    archetype_id: str,
    seed: int,
    variant_id: Optional[str] = None,
    **user_overrides
) -> Dict[str, Any]:
    """
    把 Archetype + selections 转成 Profile 字段 dict。

    Args:
        archetype_id: ARCHETYPES 里的 key
        seed: 派生 variant 选择和细节
        variant_id: 显式指定 variant（None = 按权重随机）
        **user_overrides: 覆盖任意 Profile 字段（language / timezone / proxy 等）

    Returns:
        dict 可以直接传给 ``Profile.from_dict(...)`` 或 ``AlterBrowser(**dict)``
    """
    arch = get_archetype(archetype_id)
    sel = arch.derive_selections(seed=seed, variant_id=variant_id)

    # 从 archetype 派生基础字段
    renderer = arch.gpu_renderer_template.format(
        device_id=sel["device_id"], driver_ver=sel["driver_ver"])

    data: Dict[str, Any] = {
        "seed": seed,
        "archetype_id": archetype_id,
        "archetype_selections": sel,

        # Hardware — archetype 值生效需要 CUSTOM 模式
        "cpu_mode": "custom",
        "hardware_concurrency": sel["hc"],
        "ram_mode": "custom",
        "device_memory": sel["ram_gb"],

        # GPU — 同理
        "gpu_mode": "custom",
        "gpu_vendor": arch.gpu_vendor,
        "gpu_renderer": renderer,

        # Screen
        "screen_width": sel["resolution"][0],
        "screen_height": sel["resolution"][1],
        "screen_color_depth": arch.color_depth,

        # OS
        "platform": _os_family_to_platform(arch.os_family),
        "platform_version": arch.os_ua_data_platform_version,

        # Fonts (默认 CUSTOM 用 archetype 的 preset)
        "fonts_mode": "custom",
        "fonts_custom": FONTS_PRESETS.get(arch.fonts_preset_id, []),

        # Media / Voices
        "voices_mode": "custom",
        "voices_preset": arch.voices_preset,
        "media_devices_mode": "custom",
        "media_devices": f"{sel['audio_inputs']}:{sel['video_inputs']}:{sel['audio_outputs']}",

        # Connection (保留兼容字段)
        "connection": f"{sel['connection_type']}:{sel['rtt_ms']}:{sel['downlink_mbps']:.0f}",

        # Battery
        "battery_level": sel.get("battery_level"),

        # Touch
        "max_touch_points": arch.max_touch_points,
    }

    # 用户覆盖（优先级最高）
    # 如果用户传 timezone/geolocation 等，自动把对应 mode 设为 CUSTOM
    if "timezone" in user_overrides and "timezone_mode" not in user_overrides:
        user_overrides["timezone_mode"] = "custom"
    if "geolocation" in user_overrides and "geolocation_mode" not in user_overrides:
        user_overrides["geolocation_mode"] = "custom"

    data.update(user_overrides)
    return data


def _os_family_to_platform(os_family: str) -> str:
    """"windows"/"macos"/"linux" → navigator.platform 值"""
    mapping = {
        "windows": "Win32",
        "macos": "MacIntel",
        "linux": "Linux x86_64",
    }
    return mapping.get(os_family, "Win32")


__all__ = [
    "ARCHETYPES",
    "FONTS_PRESETS",
    "DeviceArchetype",
    "ConfigurationVariant",
    "validate_profile",
    "get_archetype",
    "list_archetypes",
    "random_archetype",
    "find_archetype_by_hint",
    "build_profile_from_archetype",
]
