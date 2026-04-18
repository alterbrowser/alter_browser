"""Shorthand / presets 单元测试"""
import pytest

from alterbrowser import AlterBrowser, Profile, SourceMode
from alterbrowser.presets import (
    resolve_gpu,
    resolve_cpu,
    resolve_os,
    resolve_resolution,
    resolve_city,
)


# ============================================================
# GPU
# ============================================================

def test_resolve_gpu_nvidia_exact():
    r = resolve_gpu("RTX 5090")
    assert r["gpu_mode"] == "custom"
    assert r["gpu_vendor"] == "Google Inc. (NVIDIA)"
    assert "RTX 5090" in r["gpu_renderer"]
    assert "NVIDIA" in r["gpu_renderer"]


def test_resolve_gpu_amd_exact():
    r = resolve_gpu("RX 7900 XTX")
    assert r["gpu_vendor"] == "Google Inc. (AMD)"
    assert "RX 7900 XTX" in r["gpu_renderer"]


def test_resolve_gpu_intel_igpu():
    r = resolve_gpu("UHD 630")
    assert r["gpu_vendor"] == "Google Inc. (Intel)"
    assert "UHD Graphics 630" in r["gpu_renderer"]


def test_resolve_gpu_apple_silicon():
    r = resolve_gpu("M2 Pro")
    assert r["gpu_vendor"] == "Google Inc. (Apple)"
    assert "Apple M2 Pro" in r["gpu_renderer"]


def test_resolve_gpu_free_text_brand_detection():
    """未登记的显卡名也应识别到品牌"""
    r = resolve_gpu("GeForce weird new card 9999")
    assert r["gpu_vendor"] == "Google Inc. (NVIDIA)"


def test_resolve_gpu_empty():
    assert resolve_gpu("") == {}
    assert resolve_gpu(None) == {}


# ============================================================
# CPU
# ============================================================

def test_resolve_cpu_intel_14gen():
    r = resolve_cpu("i9-14900K")
    assert r["cpu_mode"] == "custom"
    assert r["ram_mode"] == "custom"
    assert r["hardware_concurrency"] == 32


def test_resolve_cpu_amd_ryzen():
    r = resolve_cpu("Ryzen 9 7950X")
    assert r["hardware_concurrency"] == 32


def test_resolve_cpu_apple():
    r = resolve_cpu("M2 Pro")
    assert r["hardware_concurrency"] == 12
    assert r["device_memory"] == 16


def test_resolve_cpu_unknown_returns_empty():
    assert resolve_cpu("some unknown chip 9999") == {}


# ============================================================
# OS
# ============================================================

def test_resolve_os_win11():
    r = resolve_os("win11")
    assert r["platform"] == "Win32"
    assert r["platform_version"] == "15.0.0"


def test_resolve_os_windows_11_alias():
    r = resolve_os("Windows 11")
    assert r["platform"] == "Win32"


def test_resolve_os_macos_codename():
    r = resolve_os("Sonoma")
    assert r["platform"] == "MacIntel"
    assert r["platform_version"] == "14.0.0"


def test_resolve_os_linux():
    r = resolve_os("Ubuntu")
    assert r["platform"] == "Linux x86_64"


# ============================================================
# Resolution
# ============================================================

def test_resolve_resolution_wxh():
    r = resolve_resolution("1920x1080")
    assert r == {"screen_width": 1920, "screen_height": 1080}


def test_resolve_resolution_alias_4k():
    r = resolve_resolution("4K")
    assert r == {"screen_width": 3840, "screen_height": 2160}


def test_resolve_resolution_alias_qhd():
    r = resolve_resolution("qhd")
    assert r == {"screen_width": 2560, "screen_height": 1440}


def test_resolve_resolution_bad():
    assert resolve_resolution("not a resolution") == {}


# ============================================================
# City
# ============================================================

def test_resolve_city_shanghai():
    r = resolve_city("Shanghai")
    assert r["timezone"] == "Asia/Shanghai"
    assert r["language"] == "zh-CN"
    assert r["geolocation"][0] == 31.2304


def test_resolve_city_new_york_abbreviation():
    r = resolve_city("NYC")
    assert r["timezone"] == "America/New_York"
    assert r["language"] == "en-US"


def test_resolve_city_hong_kong_traditional_chinese():
    r = resolve_city("Hong Kong")
    assert r["language"] == "zh-HK"


def test_resolve_city_unknown():
    assert resolve_city("Atlantis") == {}


# ============================================================
# Profile integration
# ============================================================

def test_profile_expands_shorthand():
    p = Profile(seed=1, gpu="RTX 5090", cpu="i9-14900K",
                os="win11", resolution="4K", city="Shanghai")
    assert p.platform == "Win32"
    assert p.platform_version == "15.0.0"
    assert p.gpu_mode == SourceMode.CUSTOM
    assert "RTX 5090" in p.gpu_renderer
    assert p.hardware_concurrency == 32
    assert p.screen_width == 3840 and p.screen_height == 2160
    assert p.timezone == "Asia/Shanghai"
    assert p.language == "zh-CN"


def test_user_explicit_fields_override_shorthand():
    """用户显式指定 platform 时，os shorthand 不覆盖"""
    p = Profile(seed=1, os="win11", platform="MacIntel")
    assert p.platform == "MacIntel"


def test_alterbrowser_kwargs_shorthand():
    sb = AlterBrowser(seed=1, gpu="RTX 4090", city="Tokyo")
    assert sb.profile.gpu_renderer and "RTX 4090" in sb.profile.gpu_renderer
    assert sb.profile.timezone == "Asia/Tokyo"
    assert sb.profile.language == "ja-JP"


def test_shorthand_serialization_roundtrip():
    """shorthand 字段应能正常序列化和反序列化"""
    p = Profile(seed=1, gpu="RTX 5090", city="Shanghai")
    d = p.to_dict()
    assert d["gpu"] == "RTX 5090"
    p2 = Profile.from_dict(d)
    assert p2.gpu == "RTX 5090"
    assert p2.gpu_renderer == p.gpu_renderer
