"""
SwitchBuilder — Profile → Chrome 命令行参数

v0.2 重构：按 FingerprintMode / SourceMode / WebRTCMode / TriState 分模式处理。
"""
from __future__ import annotations

from typing import List

from .fonts import FontGenerator, FontMode
from .modes import FingerprintMode, SourceMode, WebRTCMode, TriState
from .profile import Profile


def build_switches(profile: Profile) -> List[str]:
    """
    把 Profile 转成 Chrome 启动命令（list[str]）。

    返回列表第 0 项是 chrome_binary 路径，适合直接喂给 subprocess.Popen。
    """
    args: List[str] = [profile.chrome_binary]

    # ===== 基础启动参数 =====
    args += [
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile.auto_user_data_dir()}",
    ]

    # ===== 指纹主控 seed =====
    # 只在 UNIQUE 模式才传 --fingerprint，因为它会激活 Canvas/Audio noise
    # → 独特 hash → 可能被 Masking
    if profile.fingerprint_mode == FingerprintMode.UNIQUE:
        args.append(f"--fingerprint={profile.seed}")
    # REALISTIC / CACHED: 不传 --fingerprint，保留真实硬件 hash

    # ===== UA Brand（3）=====
    if profile.brand:
        args.append(f"--fingerprint-brand={profile.brand}")
    if profile.brand_version:
        args.append(f"--fingerprint-brand-version={profile.brand_version}")
    if profile.user_agent:
        args.append(f"--user-agent={profile.user_agent}")

    # ===== OS =====
    if profile.platform:
        args.append(f"--fingerprint-platform={profile.platform}")
    if profile.platform_version:
        args.append(f"--fingerprint-platform-version={profile.platform_version}")

    # ===== 8. 语言 =====
    if profile.language:
        args.append(f"--lang={profile.language}")
    if profile.accept_lang:
        args.append(f"--accept-lang={profile.accept_lang}")

    # ===== 7a. 时区 =====
    args += _build_timezone(profile)

    # ===== 7b. 地理位置 =====
    args += _build_geolocation(profile)

    # ===== 12b/12c. CPU / RAM =====
    args += _build_hardware(profile)

    # ===== 9. 分辨率 =====
    if profile.screen_width is not None:
        args.append(f"--fingerprint-screen-width={profile.screen_width}")
    if profile.screen_height is not None:
        args.append(f"--fingerprint-screen-height={profile.screen_height}")
    if profile.screen_color_depth is not None:
        args.append(f"--fingerprint-screen-color-depth={profile.screen_color_depth}")
    if profile.max_touch_points is not None:
        args.append(f"--fingerprint-max-touch-points={profile.max_touch_points}")

    # ===== 11. WebGL 元数据 =====
    args += _build_gpu(profile)

    # ===== 12a. WebGPU =====
    args += _build_webgpu(profile)

    # ===== 10. 硬件噪声 =====
    args += _build_noise_switches(profile)

    # ===== 2. 字体 =====
    args += _build_fonts(profile)

    # ===== 6. WebRTC =====
    args += _build_webrtc(profile)

    # ===== 5. 代理 =====
    if profile.proxy:
        args.append(f"--proxy-server={profile.proxy}")

    # ===== 13. Do Not Track =====
    args += _build_dnt(profile)

    # ===== 14. 高级 =====
    args += _build_advanced(profile)

    # ===== 媒体相关（兼容字段）=====
    if profile.battery_level is not None:
        args.append(f"--fingerprint-battery={profile.battery_level}")
    if profile.connection:
        args.append(f"--fingerprint-connection={profile.connection}")

    # ===== 用户附加 =====
    args.extend(profile.extra_args)

    # ===== start URL =====
    if profile.start_url:
        args.append(profile.start_url)

    return args


# ============================================================
# 分类 builders
# ============================================================

def _build_timezone(p: Profile) -> List[str]:
    if p.timezone_mode == SourceMode.REAL:
        return []
    if p.timezone_mode == SourceMode.DISABLED:
        return []  # 不传 = 用系统，目前没法真正禁用
    if p.timezone_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.timezone:
        return [f"--fingerprint-timezone={p.timezone}"]
    return []


def _build_geolocation(p: Profile) -> List[str]:
    if p.geolocation_mode == SourceMode.REAL:
        return []
    if p.geolocation_mode == SourceMode.DISABLED:
        return ["--disable-geolocation"]
    if p.geolocation_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.geolocation:
        g = p.geolocation
        lat, lon = g[0], g[1]
        acc = g[2] if len(g) >= 3 else 100
        return [f"--fingerprint-geolocation={lat},{lon},{acc}"]
    return []


def _build_hardware(p: Profile) -> List[str]:
    args: List[str] = []
    if p.cpu_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.hardware_concurrency is not None:
        args.append(f"--fingerprint-hardware-concurrency={p.hardware_concurrency}")
    if p.ram_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.device_memory is not None:
        args.append(f"--fingerprint-device-memory={p.device_memory}")
    return args


def _build_gpu(p: Profile) -> List[str]:
    if p.gpu_mode != SourceMode.CUSTOM:
        return []
    args: List[str] = []
    if p.gpu_vendor:
        args.append(f"--fingerprint-gpu-vendor={p.gpu_vendor}")
    if p.gpu_renderer:
        args.append(f"--fingerprint-gpu-renderer={p.gpu_renderer}")
    return args


def _build_webgpu(p: Profile) -> List[str]:
    # 当前 Patch --fingerprint-webgpu 只接受 "blank" 值
    if p.webgpu_mode == SourceMode.DISABLED:
        return ["--fingerprint-webgpu=blank"]
    return []


def _build_noise_switches(p: Profile) -> List[str]:
    args: List[str] = []
    # 这些开关是"启用"式：加了就开 noise，不加则默认（上游原生开关）
    if p.noise_canvas:
        args.append("--fingerprinting-canvas-imagedata-noise")
    if p.noise_clientrects:
        args.append("--fingerprinting-client-rects-noise")
    # measuretext noise 也加上（与 canvas 强相关）
    if p.noise_canvas or p.noise_webgl_image:
        args.append("--fingerprinting-canvas-measuretext-noise")

    # 媒体设备
    if p.media_devices_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.media_devices:
        args.append(f"--fingerprint-media-devices={p.media_devices}")

    # 语音
    if p.voices_mode in (SourceMode.CUSTOM, SourceMode.BY_IP) and p.voices_preset:
        args.append(f"--fingerprint-voices={p.voices_preset}")

    return args


def _build_fonts(p: Profile) -> List[str]:
    mode = p.fonts_mode
    if mode == FontMode.DEFAULT:
        return []
    if mode == FontMode.CUSTOM and p.fonts_custom:
        return [f"--fingerprint-fonts={','.join(p.fonts_custom)}"]
    # 生成式字体列表需要 FontGenerator
    fg = FontGenerator(p.seed)
    fonts = fg.generate(mode, custom=p.fonts_custom or None)
    if fonts:
        # MIX/SYSTEM 模式：合并 ip_adapt 等模块追加到 fonts_custom 的区域字体
        if p.fonts_custom:
            existing = set(fonts)
            extras = [f for f in p.fonts_custom if f not in existing]
            if extras:
                fonts.extend(extras)
        return [f"--fingerprint-fonts={','.join(fonts)}"]
    return []


def _build_webrtc(p: Profile) -> List[str]:
    if p.webrtc_mode == WebRTCMode.REAL:
        return []
    if p.webrtc_mode == WebRTCMode.FORWARD:
        return ["--force-webrtc-ip-handling-policy=default_public_interface_only"]
    if p.webrtc_mode == WebRTCMode.REPLACE and p.webrtc_public_ip:
        return [f"--fingerprint-webrtc-public-ip={p.webrtc_public_ip}"]
    if p.webrtc_mode == WebRTCMode.DISABLED:
        return ["--disable-webrtc", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    if p.webrtc_mode == WebRTCMode.DISABLED_UDP:
        return ["--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    return []


def _build_dnt(p: Profile) -> List[str]:
    # DNT 通过 Chrome prefs 设置，命令行能做的是 --enable-do-not-track
    # 当前 patches 未实现；预留开关
    if p.do_not_track == TriState.ON:
        return ["--enable-do-not-track"]
    return []


def _build_advanced(p: Profile) -> List[str]:
    args: List[str] = []
    # 硬件加速三态
    if p.hardware_accel == TriState.OFF:
        args.append("--disable-gpu")
    # 禁用 TLS 特性（占位，具体开关待研究）
    if p.disable_tls_features:
        args.append("--disable-features=TLS13EarlyData")
    # 端口扫描保护（占位）
    if not p.port_scan_protection:
        args.append("--disable-features=RestrictPrivateNetworkAccess")
    return args
