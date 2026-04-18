"""
Shorthand 预设与模糊识别
=======================

将用户友好的简写字符串（如 "RTX 5090" / "win11" / "Shanghai"）展开成
Profile 底层字段。覆盖 GPU / CPU / OS / Resolution / City 5 大维度。

所有识别都是大小写不敏感、空白/标点容错。
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


# ============================================================
# 通用工具
# ============================================================

def _normalize(s: str) -> str:
    """小写 + 合并空白 + 去连字符/下划线"""
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"[\s_\-]+", " ", s)
    return s


# ============================================================
# GPU 识别
# ============================================================

# (vendor_brand, 显卡完整名称 — 会包进 ANGLE 模板)
#
# vendor_brand 用于 `--fingerprint-gpu-vendor=Google Inc. (<vendor_brand>)`
# 显卡名会拼成 ANGLE 模板作为 `--fingerprint-gpu-renderer=`

GPU_PRESETS: Dict[str, Tuple[str, str]] = {
    # NVIDIA RTX 50 系
    "rtx 5090": ("NVIDIA", "NVIDIA GeForce RTX 5090"),
    "rtx 5080": ("NVIDIA", "NVIDIA GeForce RTX 5080"),
    "rtx 5070 ti": ("NVIDIA", "NVIDIA GeForce RTX 5070 Ti"),
    "rtx 5070": ("NVIDIA", "NVIDIA GeForce RTX 5070"),
    # NVIDIA RTX 40 系
    "rtx 4090": ("NVIDIA", "NVIDIA GeForce RTX 4090"),
    "rtx 4080 super": ("NVIDIA", "NVIDIA GeForce RTX 4080 SUPER"),
    "rtx 4080": ("NVIDIA", "NVIDIA GeForce RTX 4080"),
    "rtx 4070 ti super": ("NVIDIA", "NVIDIA GeForce RTX 4070 Ti SUPER"),
    "rtx 4070 ti": ("NVIDIA", "NVIDIA GeForce RTX 4070 Ti"),
    "rtx 4070 super": ("NVIDIA", "NVIDIA GeForce RTX 4070 SUPER"),
    "rtx 4070": ("NVIDIA", "NVIDIA GeForce RTX 4070"),
    "rtx 4060 ti": ("NVIDIA", "NVIDIA GeForce RTX 4060 Ti"),
    "rtx 4060": ("NVIDIA", "NVIDIA GeForce RTX 4060"),
    # NVIDIA RTX 30 系
    "rtx 3090 ti": ("NVIDIA", "NVIDIA GeForce RTX 3090 Ti"),
    "rtx 3090": ("NVIDIA", "NVIDIA GeForce RTX 3090"),
    "rtx 3080 ti": ("NVIDIA", "NVIDIA GeForce RTX 3080 Ti"),
    "rtx 3080": ("NVIDIA", "NVIDIA GeForce RTX 3080"),
    "rtx 3070 ti": ("NVIDIA", "NVIDIA GeForce RTX 3070 Ti"),
    "rtx 3070": ("NVIDIA", "NVIDIA GeForce RTX 3070"),
    "rtx 3060 ti": ("NVIDIA", "NVIDIA GeForce RTX 3060 Ti"),
    "rtx 3060": ("NVIDIA", "NVIDIA GeForce RTX 3060"),
    "rtx 3050": ("NVIDIA", "NVIDIA GeForce RTX 3050"),
    # NVIDIA RTX 20 系
    "rtx 2080 ti": ("NVIDIA", "NVIDIA GeForce RTX 2080 Ti"),
    "rtx 2080": ("NVIDIA", "NVIDIA GeForce RTX 2080"),
    "rtx 2070": ("NVIDIA", "NVIDIA GeForce RTX 2070"),
    "rtx 2060": ("NVIDIA", "NVIDIA GeForce RTX 2060"),
    # NVIDIA GTX 16 / 10 系
    "gtx 1660 super": ("NVIDIA", "NVIDIA GeForce GTX 1660 SUPER"),
    "gtx 1660 ti": ("NVIDIA", "NVIDIA GeForce GTX 1660 Ti"),
    "gtx 1660": ("NVIDIA", "NVIDIA GeForce GTX 1660"),
    "gtx 1650": ("NVIDIA", "NVIDIA GeForce GTX 1650"),
    "gtx 1080 ti": ("NVIDIA", "NVIDIA GeForce GTX 1080 Ti"),
    "gtx 1080": ("NVIDIA", "NVIDIA GeForce GTX 1080"),
    "gtx 1070": ("NVIDIA", "NVIDIA GeForce GTX 1070"),
    "gtx 1060": ("NVIDIA", "NVIDIA GeForce GTX 1060"),

    # AMD Radeon RX 7000 / 6000 系
    "rx 7900 xtx": ("AMD", "AMD Radeon RX 7900 XTX"),
    "rx 7900 xt": ("AMD", "AMD Radeon RX 7900 XT"),
    "rx 7800 xt": ("AMD", "AMD Radeon RX 7800 XT"),
    "rx 7700 xt": ("AMD", "AMD Radeon RX 7700 XT"),
    "rx 7600": ("AMD", "AMD Radeon RX 7600"),
    "rx 6950 xt": ("AMD", "AMD Radeon RX 6950 XT"),
    "rx 6900 xt": ("AMD", "AMD Radeon RX 6900 XT"),
    "rx 6800 xt": ("AMD", "AMD Radeon RX 6800 XT"),
    "rx 6700 xt": ("AMD", "AMD Radeon RX 6700 XT"),
    "rx 6600": ("AMD", "AMD Radeon RX 6600"),

    # Intel Arc
    "arc a770": ("Intel", "Intel(R) Arc(TM) A770 Graphics"),
    "arc a750": ("Intel", "Intel(R) Arc(TM) A750 Graphics"),
    "arc a380": ("Intel", "Intel(R) Arc(TM) A380 Graphics"),
    # Intel 集成显卡
    "iris xe": ("Intel", "Intel(R) Iris(R) Xe Graphics"),
    "uhd 770": ("Intel", "Intel(R) UHD Graphics 770"),
    "uhd 730": ("Intel", "Intel(R) UHD Graphics 730"),
    "uhd 630": ("Intel", "Intel(R) UHD Graphics 630"),
    "hd 4000": ("Intel", "Intel(R) HD Graphics 4000"),

    # Apple Silicon
    "m1": ("Apple", "Apple M1"),
    "m1 pro": ("Apple", "Apple M1 Pro"),
    "m1 max": ("Apple", "Apple M1 Max"),
    "m2": ("Apple", "Apple M2"),
    "m2 pro": ("Apple", "Apple M2 Pro"),
    "m2 max": ("Apple", "Apple M2 Max"),
    "m3": ("Apple", "Apple M3"),
    "m3 pro": ("Apple", "Apple M3 Pro"),
    "m3 max": ("Apple", "Apple M3 Max"),
    "m4": ("Apple", "Apple M4"),
    "m4 pro": ("Apple", "Apple M4 Pro"),
    "m4 max": ("Apple", "Apple M4 Max"),
}


def _detect_gpu_brand(s: str) -> str:
    """根据关键词推测品牌"""
    s_lower = s.lower()
    if any(k in s_lower for k in ("nvidia", "geforce", "rtx", "gtx", "quadro", "titan")):
        return "NVIDIA"
    if any(k in s_lower for k in ("radeon", "amd", "ryzen radeon", "rx ", "rx-", "rx_")):
        return "AMD"
    if any(k in s_lower for k in ("intel", "iris", "uhd", "arc ", "arc-", "arc_", "hd graphics")):
        return "Intel"
    if any(k in s_lower for k in ("apple", "m1", "m2", "m3", "m4")):
        return "Apple"
    return "Unknown"


def resolve_gpu(name: str) -> Dict[str, Any]:
    """
    把 GPU 简写解析成 gpu_mode / gpu_vendor / gpu_renderer 字段。

    >>> resolve_gpu("RTX 5090")
    {'gpu_mode': 'custom', 'gpu_vendor': 'Google Inc. (NVIDIA)',
     'gpu_renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 5090 Direct3D11 vs_5_0 ps_5_0, D3D11)'}
    """
    if not name:
        return {}
    key = _normalize(name)
    # 精确匹配预设
    if key in GPU_PRESETS:
        brand, card = GPU_PRESETS[key]
    else:
        # 模糊：根据关键词推品牌，显卡名直接用用户输入
        brand = _detect_gpu_brand(name)
        card = name.strip()

    vendor = f"Google Inc. ({brand})"
    if brand == "Apple":
        renderer = f"ANGLE (Apple, Apple M-series ({card}), OpenGL 4.1)"
    else:
        renderer = f"ANGLE ({brand}, {card} Direct3D11 vs_5_0 ps_5_0, D3D11)"
    return {
        "gpu_mode": "custom",
        "gpu_vendor": vendor,
        "gpu_renderer": renderer,
    }


# ============================================================
# CPU 识别 → hardware_concurrency + device_memory 推荐
# ============================================================

CPU_PRESETS: Dict[str, Dict[str, Any]] = {
    # Intel Core 14 代
    "i9 14900k": {"hardware_concurrency": 32, "device_memory": 32},
    "i9 14900": {"hardware_concurrency": 32, "device_memory": 32},
    "i7 14700k": {"hardware_concurrency": 28, "device_memory": 32},
    "i7 14700": {"hardware_concurrency": 28, "device_memory": 16},
    "i5 14600k": {"hardware_concurrency": 20, "device_memory": 16},
    "i5 14600": {"hardware_concurrency": 20, "device_memory": 16},
    "i5 14400": {"hardware_concurrency": 16, "device_memory": 16},
    # Intel Core 13 代
    "i9 13900k": {"hardware_concurrency": 32, "device_memory": 32},
    "i9 13900": {"hardware_concurrency": 32, "device_memory": 32},
    "i7 13700k": {"hardware_concurrency": 24, "device_memory": 16},
    "i7 13700": {"hardware_concurrency": 24, "device_memory": 16},
    "i5 13600k": {"hardware_concurrency": 20, "device_memory": 16},
    "i5 13600": {"hardware_concurrency": 20, "device_memory": 16},
    "i5 13400": {"hardware_concurrency": 16, "device_memory": 16},
    # Intel Core 12 代
    "i9 12900k": {"hardware_concurrency": 24, "device_memory": 32},
    "i7 12700k": {"hardware_concurrency": 20, "device_memory": 16},
    "i5 12600k": {"hardware_concurrency": 16, "device_memory": 16},
    "i5 12400": {"hardware_concurrency": 12, "device_memory": 16},
    # Intel Core 11 / 10 代
    "i9 11900k": {"hardware_concurrency": 16, "device_memory": 16},
    "i7 11700k": {"hardware_concurrency": 16, "device_memory": 16},
    "i9 10900k": {"hardware_concurrency": 20, "device_memory": 16},
    "i7 10700k": {"hardware_concurrency": 16, "device_memory": 16},
    "i5 10600k": {"hardware_concurrency": 12, "device_memory": 16},
    "i7 8700k": {"hardware_concurrency": 12, "device_memory": 16},
    "i7 7700k": {"hardware_concurrency": 8, "device_memory": 16},

    # AMD Ryzen 9000
    "ryzen 9 9950x": {"hardware_concurrency": 32, "device_memory": 32},
    "ryzen 9 9900x": {"hardware_concurrency": 24, "device_memory": 32},
    "ryzen 7 9700x": {"hardware_concurrency": 16, "device_memory": 16},
    "ryzen 5 9600x": {"hardware_concurrency": 12, "device_memory": 16},
    # AMD Ryzen 7000
    "ryzen 9 7950x": {"hardware_concurrency": 32, "device_memory": 32},
    "ryzen 9 7900x": {"hardware_concurrency": 24, "device_memory": 32},
    "ryzen 7 7800x3d": {"hardware_concurrency": 16, "device_memory": 16},
    "ryzen 7 7700x": {"hardware_concurrency": 16, "device_memory": 16},
    "ryzen 5 7600x": {"hardware_concurrency": 12, "device_memory": 16},
    # AMD Ryzen 5000
    "ryzen 9 5950x": {"hardware_concurrency": 32, "device_memory": 32},
    "ryzen 9 5900x": {"hardware_concurrency": 24, "device_memory": 32},
    "ryzen 7 5800x": {"hardware_concurrency": 16, "device_memory": 16},
    "ryzen 5 5600x": {"hardware_concurrency": 12, "device_memory": 16},

    # Apple Silicon
    "m1": {"hardware_concurrency": 8, "device_memory": 8},
    "m1 pro": {"hardware_concurrency": 10, "device_memory": 16},
    "m1 max": {"hardware_concurrency": 10, "device_memory": 32},
    "m2": {"hardware_concurrency": 8, "device_memory": 8},
    "m2 pro": {"hardware_concurrency": 12, "device_memory": 16},
    "m2 max": {"hardware_concurrency": 12, "device_memory": 32},
    "m3": {"hardware_concurrency": 8, "device_memory": 8},
    "m3 pro": {"hardware_concurrency": 12, "device_memory": 16},
    "m3 max": {"hardware_concurrency": 16, "device_memory": 32},
    "m4": {"hardware_concurrency": 10, "device_memory": 16},
    "m4 pro": {"hardware_concurrency": 14, "device_memory": 16},
    "m4 max": {"hardware_concurrency": 16, "device_memory": 32},
}


def resolve_cpu(name: str) -> Dict[str, Any]:
    """
    把 CPU 简写解析成 cpu_mode / ram_mode / hardware_concurrency / device_memory 字段。

    >>> resolve_cpu("i9-14900K")
    {'cpu_mode': 'custom', 'ram_mode': 'custom',
     'hardware_concurrency': 32, 'device_memory': 32}
    """
    if not name:
        return {}
    key = _normalize(name)
    if key not in CPU_PRESETS:
        # 简单模糊：去掉 "intel core" / "amd" 等前缀后重试
        stripped = re.sub(r"^(intel\s*core\s*|amd\s*|apple\s*)", "", key).strip()
        if stripped in CPU_PRESETS:
            key = stripped
    if key not in CPU_PRESETS:
        return {}
    p = CPU_PRESETS[key]
    return {
        "cpu_mode": "custom",
        "ram_mode": "custom",
        **p,
    }


# ============================================================
# OS 识别
# ============================================================

OS_PRESETS: Dict[str, Dict[str, Any]] = {
    "win7":         {"platform": "Win32",      "platform_version": "6.1.0"},
    "win8":         {"platform": "Win32",      "platform_version": "6.2.0"},
    "win8.1":       {"platform": "Win32",      "platform_version": "6.3.0"},
    "win10":        {"platform": "Win32",      "platform_version": "10.0.0"},
    "win11":        {"platform": "Win32",      "platform_version": "15.0.0"},
    "macos 12":     {"platform": "MacIntel",   "platform_version": "12.0.0"},
    "macos 13":     {"platform": "MacIntel",   "platform_version": "13.0.0"},
    "macos 14":     {"platform": "MacIntel",   "platform_version": "14.0.0"},
    "macos 15":     {"platform": "MacIntel",   "platform_version": "15.0.0"},
    "macos":        {"platform": "MacIntel",   "platform_version": "14.0.0"},
    "linux":        {"platform": "Linux x86_64", "platform_version": "6.5.0"},
    "ubuntu":       {"platform": "Linux x86_64", "platform_version": "6.5.0"},
}

# 常见别名
_OS_ALIASES = {
    "windows 7": "win7", "windows 8": "win8", "windows 8.1": "win8.1",
    "windows 10": "win10", "windows 11": "win11",
    "win 10": "win10", "win 11": "win11",
    "monterey": "macos 12", "ventura": "macos 13",
    "sonoma": "macos 14", "sequoia": "macos 15",
}


def resolve_os(name: str) -> Dict[str, Any]:
    """
    >>> resolve_os("Windows 11")
    {'platform': 'Win32', 'platform_version': '15.0.0'}
    """
    if not name:
        return {}
    key = _normalize(name)
    key = _OS_ALIASES.get(key, key)
    return dict(OS_PRESETS.get(key, {}))


# ============================================================
# Resolution / Screen
# ============================================================

_RESOLUTION_ALIASES: Dict[str, Tuple[int, int]] = {
    "720p": (1280, 720),
    "hd": (1280, 720),
    "1080p": (1920, 1080),
    "fhd": (1920, 1080),
    "1440p": (2560, 1440),
    "qhd": (2560, 1440),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
    "uhd": (3840, 2160),
    "5k": (5120, 2880),
    "8k": (7680, 4320),
    # 常见笔记本
    "macbook air": (2560, 1664),
    "macbook pro 14": (3024, 1964),
    "macbook pro 16": (3456, 2234),
}


def resolve_resolution(name: str) -> Dict[str, Any]:
    """
    >>> resolve_resolution("1920x1080")
    {'screen_width': 1920, 'screen_height': 1080}

    >>> resolve_resolution("4K")
    {'screen_width': 3840, 'screen_height': 2160}
    """
    if not name:
        return {}
    key = _normalize(name)
    if key in _RESOLUTION_ALIASES:
        w, h = _RESOLUTION_ALIASES[key]
        return {"screen_width": w, "screen_height": h}
    # 解析 "WxH" 格式
    m = re.match(r"^\s*(\d{3,5})\s*[x×*]\s*(\d{3,5})\s*$", name, re.I)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        return {"screen_width": w, "screen_height": h}
    return {}


# ============================================================
# City → timezone / geolocation / language
# ============================================================

CITY_PRESETS: Dict[str, Dict[str, Any]] = {
    # 亚太
    "beijing":      {"timezone": "Asia/Shanghai",   "geolocation": (39.9042, 116.4074, 100), "language": "zh-CN"},
    "shanghai":     {"timezone": "Asia/Shanghai",   "geolocation": (31.2304, 121.4737, 100), "language": "zh-CN"},
    "guangzhou":    {"timezone": "Asia/Shanghai",   "geolocation": (23.1291, 113.2644, 100), "language": "zh-CN"},
    "shenzhen":     {"timezone": "Asia/Shanghai",   "geolocation": (22.5431, 114.0579, 100), "language": "zh-CN"},
    "hong kong":    {"timezone": "Asia/Hong_Kong",  "geolocation": (22.3193, 114.1694, 100), "language": "zh-HK"},
    "taipei":       {"timezone": "Asia/Taipei",     "geolocation": (25.0330, 121.5654, 100), "language": "zh-TW"},
    "tokyo":        {"timezone": "Asia/Tokyo",      "geolocation": (35.6762, 139.6503, 100), "language": "ja-JP"},
    "osaka":        {"timezone": "Asia/Tokyo",      "geolocation": (34.6937, 135.5023, 100), "language": "ja-JP"},
    "seoul":        {"timezone": "Asia/Seoul",      "geolocation": (37.5665, 126.9780, 100), "language": "ko-KR"},
    "singapore":    {"timezone": "Asia/Singapore",  "geolocation": (1.3521, 103.8198, 100),  "language": "en-SG"},
    "bangkok":      {"timezone": "Asia/Bangkok",    "geolocation": (13.7563, 100.5018, 100), "language": "th-TH"},
    "mumbai":       {"timezone": "Asia/Kolkata",    "geolocation": (19.0760, 72.8777, 100),  "language": "en-IN"},
    "delhi":        {"timezone": "Asia/Kolkata",    "geolocation": (28.6139, 77.2090, 100),  "language": "en-IN"},
    "dubai":        {"timezone": "Asia/Dubai",      "geolocation": (25.2048, 55.2708, 100),  "language": "ar-AE"},

    # 欧洲
    "london":       {"timezone": "Europe/London",   "geolocation": (51.5074, -0.1278, 100),  "language": "en-GB"},
    "paris":        {"timezone": "Europe/Paris",    "geolocation": (48.8566, 2.3522, 100),   "language": "fr-FR"},
    "berlin":       {"timezone": "Europe/Berlin",   "geolocation": (52.5200, 13.4050, 100),  "language": "de-DE"},
    "frankfurt":    {"timezone": "Europe/Berlin",   "geolocation": (50.1109, 8.6821, 100),   "language": "de-DE"},
    "amsterdam":    {"timezone": "Europe/Amsterdam","geolocation": (52.3676, 4.9041, 100),   "language": "nl-NL"},
    "madrid":       {"timezone": "Europe/Madrid",   "geolocation": (40.4168, -3.7038, 100),  "language": "es-ES"},
    "rome":         {"timezone": "Europe/Rome",     "geolocation": (41.9028, 12.4964, 100),  "language": "it-IT"},
    "moscow":       {"timezone": "Europe/Moscow",   "geolocation": (55.7558, 37.6173, 100),  "language": "ru-RU"},
    "istanbul":     {"timezone": "Europe/Istanbul", "geolocation": (41.0082, 28.9784, 100),  "language": "tr-TR"},

    # 北美
    "new york":     {"timezone": "America/New_York","geolocation": (40.7128, -74.0060, 100), "language": "en-US"},
    "nyc":          {"timezone": "America/New_York","geolocation": (40.7128, -74.0060, 100), "language": "en-US"},
    "los angeles":  {"timezone": "America/Los_Angeles", "geolocation": (34.0522, -118.2437, 100), "language": "en-US"},
    "la":           {"timezone": "America/Los_Angeles", "geolocation": (34.0522, -118.2437, 100), "language": "en-US"},
    "san francisco":{"timezone": "America/Los_Angeles", "geolocation": (37.7749, -122.4194, 100), "language": "en-US"},
    "chicago":      {"timezone": "America/Chicago", "geolocation": (41.8781, -87.6298, 100), "language": "en-US"},
    "seattle":      {"timezone": "America/Los_Angeles", "geolocation": (47.6062, -122.3321, 100), "language": "en-US"},
    "toronto":      {"timezone": "America/Toronto", "geolocation": (43.6532, -79.3832, 100), "language": "en-CA"},
    "vancouver":    {"timezone": "America/Vancouver","geolocation": (49.2827, -123.1207, 100), "language": "en-CA"},

    # 南半球 / 其它
    "sydney":       {"timezone": "Australia/Sydney","geolocation": (-33.8688, 151.2093, 100),"language": "en-AU"},
    "melbourne":    {"timezone": "Australia/Melbourne","geolocation": (-37.8136, 144.9631, 100), "language": "en-AU"},
    "sao paulo":    {"timezone": "America/Sao_Paulo","geolocation": (-23.5505, -46.6333, 100), "language": "pt-BR"},
    "mexico city":  {"timezone": "America/Mexico_City","geolocation": (19.4326, -99.1332, 100), "language": "es-MX"},
}


def resolve_city(name: str) -> Dict[str, Any]:
    """
    >>> resolve_city("Shanghai")
    {'timezone_mode': 'custom', 'geolocation_mode': 'custom',
     'timezone': 'Asia/Shanghai', 'geolocation': (31.2304, 121.4737, 100), 'language': 'zh-CN'}
    """
    if not name:
        return {}
    key = _normalize(name)
    if key not in CITY_PRESETS:
        return {}
    p = CITY_PRESETS[key]
    return {
        "timezone_mode": "custom",
        "geolocation_mode": "custom",
        **p,
    }


# ============================================================
# 综合展开入口
# ============================================================

def expand_shorthand(
    gpu: Optional[str] = None,
    cpu: Optional[str] = None,
    os: Optional[str] = None,
    resolution: Optional[str] = None,
    city: Optional[str] = None,
) -> Dict[str, Any]:
    """
    把所有简写字段一次性展开成 Profile 字段字典。
    顺序：城市优先（因为可能含 language），其次 OS / CPU / GPU / resolution。
    后填的不会覆盖前面明确的字段。
    """
    out: Dict[str, Any] = {}
    if city:
        out.update(resolve_city(city))
    if os:
        out.update(resolve_os(os))
    if cpu:
        out.update(resolve_cpu(cpu))
    if gpu:
        out.update(resolve_gpu(gpu))
    if resolution:
        out.update(resolve_resolution(resolution))
    return out
