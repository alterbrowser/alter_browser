"""SwitchBuilder 单元测试"""
import pytest

from alterbrowser.fonts import FontMode
from alterbrowser.modes import FingerprintMode, SourceMode, WebRTCMode, TriState
from alterbrowser.profile import Profile
from alterbrowser.switches import build_switches


def test_minimal_profile():
    p = Profile(seed=12345)
    cmd = build_switches(p)
    assert cmd[0].endswith("chrome.exe") or cmd[0].endswith("chrome")
    # 基础
    assert "--no-first-run" in cmd
    # v0.2 默认 REALISTIC → 不传 --fingerprint seed
    assert "--fingerprint=12345" not in cmd
    # 默认字段仍然传
    assert "--fingerprint-platform=Win32" in cmd


def test_unique_mode_passes_seed():
    """UNIQUE 模式才传 --fingerprint seed"""
    p = Profile(seed=12345, fingerprint_mode=FingerprintMode.UNIQUE)
    cmd = build_switches(p)
    assert "--fingerprint=12345" in cmd


def test_realistic_mode_no_seed():
    """REALISTIC 模式不传 --fingerprint seed (默认)"""
    p = Profile(seed=12345, fingerprint_mode="realistic")
    cmd = build_switches(p)
    assert not any(c.startswith("--fingerprint=") for c in cmd)


def test_webrtc_modes():
    """WebRTC 五模式"""
    # REAL: 什么都不加
    p = Profile(seed=1, webrtc_mode=WebRTCMode.REAL)
    cmd = build_switches(p)
    assert not any("webrtc" in c.lower() for c in cmd)

    # REPLACE: 加 public IP
    p = Profile(seed=1, webrtc_mode=WebRTCMode.REPLACE, webrtc_public_ip="1.2.3.4")
    cmd = build_switches(p)
    assert "--fingerprint-webrtc-public-ip=1.2.3.4" in cmd

    # DISABLED_UDP
    p = Profile(seed=1, webrtc_mode=WebRTCMode.DISABLED_UDP)
    cmd = build_switches(p)
    assert any("disable_non_proxied_udp" in c for c in cmd)


def test_source_mode_timezone():
    # REAL: 不传
    p = Profile(seed=1, timezone_mode=SourceMode.REAL, timezone="America/New_York")
    cmd = build_switches(p)
    assert not any("fingerprint-timezone" in c for c in cmd)

    # CUSTOM: 传
    p = Profile(seed=1, timezone_mode=SourceMode.CUSTOM, timezone="America/New_York")
    cmd = build_switches(p)
    assert "--fingerprint-timezone=America/New_York" in cmd


def test_cpu_ram_mode():
    # REAL: 不传
    p = Profile(seed=1, cpu_mode=SourceMode.REAL, hardware_concurrency=8)
    cmd = build_switches(p)
    assert not any("hardware-concurrency" in c for c in cmd)

    # CUSTOM: 传
    p = Profile(seed=1, cpu_mode=SourceMode.CUSTOM, hardware_concurrency=16,
                ram_mode=SourceMode.CUSTOM, device_memory=32)
    cmd = build_switches(p)
    assert "--fingerprint-hardware-concurrency=16" in cmd
    assert "--fingerprint-device-memory=32" in cmd


def test_dnt_tri_state():
    p = Profile(seed=1, do_not_track=TriState.DEFAULT)
    cmd = build_switches(p)
    assert "--enable-do-not-track" not in cmd

    p = Profile(seed=1, do_not_track=TriState.ON)
    cmd = build_switches(p)
    assert "--enable-do-not-track" in cmd


def test_noise_switches():
    # 默认全开
    p = Profile(seed=1)
    cmd = build_switches(p)
    assert "--fingerprinting-canvas-imagedata-noise" in cmd
    assert "--fingerprinting-client-rects-noise" in cmd

    # 关闭
    p = Profile(seed=1, noise_canvas=False, noise_clientrects=False, noise_webgl_image=False)
    cmd = build_switches(p)
    assert "--fingerprinting-canvas-imagedata-noise" not in cmd
    assert "--fingerprinting-client-rects-noise" not in cmd


def test_fonts_default_no_switch():
    p = Profile(seed=1, fonts_mode=FontMode.DEFAULT)
    cmd = build_switches(p)
    assert not any(c.startswith("--fingerprint-fonts=") for c in cmd)


def test_fonts_custom():
    p = Profile(seed=1, fonts_mode=FontMode.CUSTOM,
                fonts_custom=["Arial", "Calibri", "Microsoft YaHei"])
    cmd = build_switches(p)
    fonts_args = [c for c in cmd if c.startswith("--fingerprint-fonts=")]
    assert len(fonts_args) == 1
    assert "Arial" in fonts_args[0]
    assert "Microsoft YaHei" in fonts_args[0]


def test_fonts_mixed():
    p = Profile(seed=42, fonts_mode=FontMode.MIXED)
    cmd = build_switches(p)
    fonts_args = [c for c in cmd if c.startswith("--fingerprint-fonts=")]
    assert len(fonts_args) == 1
    # 混合风格应该包含 Windows 核心和 macOS 混合
    assert "Arial" in fonts_args[0]
    assert "Heiti" in fonts_args[0] or "Avenir" in fonts_args[0] or "Noto" in fonts_args[0]


def test_fonts_deterministic_same_seed():
    """同 seed 生成相同字体列表"""
    p1 = Profile(seed=999, fonts_mode=FontMode.MIXED)
    p2 = Profile(seed=999, fonts_mode=FontMode.MIXED)
    cmd1 = build_switches(p1)
    cmd2 = build_switches(p2)
    f1 = [c for c in cmd1 if c.startswith("--fingerprint-fonts=")][0]
    f2 = [c for c in cmd2 if c.startswith("--fingerprint-fonts=")][0]
    assert f1 == f2


def test_fonts_different_seeds_differ():
    """不同 seed 生成不同字体列表"""
    p1 = Profile(seed=100, fonts_mode=FontMode.MIXED)
    p2 = Profile(seed=200, fonts_mode=FontMode.MIXED)
    f1 = [c for c in build_switches(p1) if c.startswith("--fingerprint-fonts=")][0]
    f2 = [c for c in build_switches(p2) if c.startswith("--fingerprint-fonts=")][0]
    assert f1 != f2


def test_gpu_switches():
    p = Profile(
        seed=1,
        gpu_mode=SourceMode.CUSTOM,     # v0.2: 显式开
        gpu_vendor="Google Inc. (NVIDIA)",
        gpu_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 ...)",
    )
    cmd = build_switches(p)
    assert "--fingerprint-gpu-vendor=Google Inc. (NVIDIA)" in cmd
    assert any(c.startswith("--fingerprint-gpu-renderer=") for c in cmd)


def test_hardware_switches():
    p = Profile(
        seed=1,
        cpu_mode=SourceMode.CUSTOM,
        ram_mode=SourceMode.CUSTOM,
        hardware_concurrency=16,
        device_memory=32,
        screen_width=2560,
        screen_height=1440,
    )
    cmd = build_switches(p)
    assert "--fingerprint-hardware-concurrency=16" in cmd
    assert "--fingerprint-device-memory=32" in cmd
    assert "--fingerprint-screen-width=2560" in cmd
    assert "--fingerprint-screen-height=1440" in cmd


def test_geolocation():
    p = Profile(seed=1, geolocation_mode=SourceMode.CUSTOM, geolocation=(40.7128, -74.0060, 100))
    cmd = build_switches(p)
    geo = [c for c in cmd if c.startswith("--fingerprint-geolocation=")]
    assert len(geo) == 1
    assert "40.7128" in geo[0]
    assert "-74.006" in geo[0]


def test_start_url_at_end():
    p = Profile(seed=1, start_url="https://example.com")
    cmd = build_switches(p)
    assert cmd[-1] == "https://example.com"


def test_extra_args():
    p = Profile(seed=1, extra_args=["--disable-blink-features=AutomationControlled"])
    cmd = build_switches(p)
    assert "--disable-blink-features=AutomationControlled" in cmd


def test_proxy():
    p = Profile(seed=1, proxy="http://proxy.com:8080")
    cmd = build_switches(p)
    assert "--proxy-server=http://proxy.com:8080" in cmd
