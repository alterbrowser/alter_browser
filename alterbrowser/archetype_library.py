"""
Device Archetype Library (v3.1)
================================

物理一致性的"真实设备画像"预制库。
每个 Archetype 是一个真实世界存在的硬件配置，所有字段交叉验证通过。
用户不能自由组合 CPU/GPU/RAM，只能从 archetype 提供的合理选项里挑。

核心原则：
- 不是"我能控多少维度"，是"我的维度多合理"。
- 预制 > 自由组合
- 10 个 archetype 覆盖 80% 业务场景
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import random

# ============================================================================
# Font Preset Library
# ============================================================================

FONTS_PRESETS: dict[str, list[str]] = {
    # Windows 10 中文商务（55+ 字体，含中文 UI fallback）
    "windows_10_zh_CN_business": [
        # ASCII 字体
        "Arial", "Arial Black", "Bahnschrift", "Calibri", "Calibri Light",
        "Cambria", "Cambria Math", "Candara", "Comic Sans MS", "Consolas",
        "Constantia", "Corbel", "Courier New", "Ebrima", "Franklin Gothic",
        "Gabriola", "Georgia", "Impact", "Ink Free",
        "Lucida Console", "Lucida Sans Unicode",
        "Marlett", "Microsoft Sans Serif",
        "MV Boli", "Palatino Linotype",
        "Segoe Print", "Segoe Script", "Segoe UI", "Segoe UI Black",
        "Segoe UI Emoji", "Segoe UI Historic", "Segoe UI Light",
        "Segoe UI Semibold", "Segoe UI Semilight", "Segoe UI Symbol",
        "Sitka Banner", "Sitka Small", "Sitka Subheading",
        "Sylfaen", "Symbol", "Tahoma", "Times New Roman", "Trebuchet MS",
        "Verdana", "Webdings", "Wingdings",
        # 中文字体（关键：pixelscan 会扫这些）
        "Microsoft YaHei", "Microsoft YaHei UI", "Microsoft YaHei Light",
        "Microsoft JhengHei", "Microsoft JhengHei UI", "Microsoft JhengHei Light",
        "DengXian", "DengXian Light",
        "SimSun", "SimSun-ExtB", "NSimSun", "SimHei", "KaiTi", "FangSong",
        "PMingLiU-ExtB", "MingLiU-ExtB", "MingLiU_HKSCS-ExtB",
        # 日韩字体
        "Yu Gothic", "Yu Gothic UI", "Meiryo", "Meiryo UI",
        "MS Gothic", "MS PGothic", "MS UI Gothic",
        "Malgun Gothic",
        # 少数民族 & 其他
        "Microsoft Himalaya", "Microsoft New Tai Lue", "Microsoft PhagsPa",
        "Microsoft Tai Le", "Microsoft Yi Baiti", "Mongolian Baiti",
        "Javanese Text", "Myanmar Text", "Gadugi",
    ],

    # Windows 10 英语默认（约 45 字体）
    "windows_10_en_US_basic": [
        "Arial", "Arial Black", "Bahnschrift", "Calibri", "Calibri Light",
        "Cambria", "Cambria Math", "Candara", "Comic Sans MS", "Consolas",
        "Constantia", "Corbel", "Courier New", "Ebrima",
        "Franklin Gothic", "Gabriola", "Georgia", "Impact", "Ink Free",
        "Javanese Text", "Leelawadee UI", "Lucida Console",
        "Lucida Sans Unicode", "Malgun Gothic", "Marlett", "Microsoft Himalaya",
        "Microsoft Sans Serif", "Microsoft Tai Le", "Microsoft Yi Baiti",
        "Mongolian Baiti", "Myanmar Text", "MV Boli", "Nirmala UI",
        "Palatino Linotype", "Segoe Print", "Segoe Script", "Segoe UI",
        "Segoe UI Emoji", "Segoe UI Historic", "Segoe UI Symbol",
        "SimSun", "Sitka Small", "Sylfaen", "Symbol", "Tahoma",
        "Times New Roman", "Trebuchet MS", "Verdana", "Webdings",
        "Wingdings", "Yu Gothic",
    ],

    # Windows 11 默认（加了 Aptos / Cascadia）
    "windows_11_en_US_2024": [
        # 继承 Win 10 + Win 11 新增
        "Aptos", "Aptos Display", "Aptos Narrow", "Aptos SemiBold",
        "Aptos Serif",
        "Cascadia Code", "Cascadia Mono",
        "Arial", "Arial Black", "Bahnschrift", "Calibri", "Calibri Light",
        "Cambria", "Cambria Math", "Candara", "Comic Sans MS", "Consolas",
        "Constantia", "Corbel", "Courier New",
        "Georgia", "Impact", "Ink Free", "Javanese Text",
        "Leelawadee UI", "Lucida Console", "Lucida Sans Unicode",
        "Malgun Gothic", "Marlett", "Microsoft Himalaya",
        "Microsoft Sans Serif", "MV Boli", "Nirmala UI",
        "Palatino Linotype",
        "Segoe Fluent Icons",  # Win11 新增
        "Segoe MDL2 Assets",
        "Segoe Print", "Segoe Script", "Segoe UI",
        "Segoe UI Emoji", "Segoe UI Historic", "Segoe UI Symbol",
        "Segoe UI Variable Display", "Segoe UI Variable Small",
        "Segoe UI Variable Text",  # Win11 新增
        "SimSun", "Sitka Small", "Sylfaen", "Symbol", "Tahoma",
        "Times New Roman", "Trebuchet MS", "Verdana", "Webdings",
        "Wingdings", "Yu Gothic",
    ],

    # macOS 14 默认（约 40 字体）
    "macos_14_default": [
        "Helvetica Neue", "Helvetica", "SF Pro", "SF Pro Display",
        "SF Pro Text", "SF Mono", "San Francisco",
        "Apple Color Emoji", "Apple Symbols", "Apple SD Gothic Neo",
        "Arial", "Arial Black", "Arial Narrow",
        "Avenir", "Avenir Next", "Avenir Next Condensed",
        "Courier", "Courier New",
        "Futura", "Georgia", "Gill Sans", "Helvetica Neue",
        "Hiragino Kaku Gothic Pro", "Hiragino Kaku Gothic ProN",
        "Hiragino Mincho ProN", "Hiragino Sans",
        "Impact",
        "Lucida Grande", "Menlo", "Monaco",
        "Optima", "Palatino",
        "PingFang HK", "PingFang SC", "PingFang TC",
        "STFangsong", "STHeiti", "STKaiti", "STSong",
        "Tahoma", "Times", "Times New Roman", "Trebuchet MS",
        "Verdana", "Wingdings", "Zapfino",
    ],

    # Linux Ubuntu 22 默认
    "linux_ubuntu_22_default": [
        "Ubuntu", "Ubuntu Mono", "Ubuntu Condensed",
        "DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono",
        "Liberation Sans", "Liberation Serif", "Liberation Mono",
        "Nimbus Sans", "Nimbus Roman", "Nimbus Mono",
        "Noto Sans", "Noto Serif", "Noto Mono",
        "Noto Sans CJK SC", "Noto Sans CJK TC", "Noto Sans CJK JP",
        "Noto Color Emoji",
        "FreeSans", "FreeSerif", "FreeMono",
    ],
}


# ============================================================================
# Device Archetype
# ============================================================================

@dataclass
class ConfigurationVariant:
    """Archetype 内部一个"已知真实存在的硬件组合"。整组配合使用，不自由组合。
    每个 variant 代表市场上真实存在的某个具体型号配置（从市场报告/二手机市场采集）。"""
    variant_id: str                     # "i7_8gb_wqhd" / "i5_4gb_hd" / ...
    display_name: str                   # "i7-3520M / 8GB / 2560x1440 外接"
    weight: int                         # 该 variant 的流行权重
    hc: int
    ram_gb: int
    resolution: tuple[int, int]
    pixel_ratio: float = 1.0
    typical_battery_levels: list[float] = field(default_factory=list)
    typical_audio_inputs: list[int] = field(default_factory=lambda: [1])
    typical_video_inputs: list[int] = field(default_factory=lambda: [1])
    typical_audio_outputs: list[int] = field(default_factory=lambda: [1, 2])


@dataclass
class DeviceArchetype:
    """单一真实硬件配置的完整画像"""
    id: str
    display_name: str
    form_factor: str  # laptop_13 | laptop_14 | laptop_15 | laptop_17 | desktop | tablet

    # ===== Hardware =====
    cpu_model: str
    cpu_era_year: int
    gpu_vendor: str
    gpu_renderer_template: str  # 含占位符 {driver_ver} 和 {device_id}
    gpu_driver_versions: list[str]
    gpu_device_ids: list[str]  # 如 "0x00000166"
    webgpu_supported: bool

    # ===== Display defaults =====
    color_depth: int  # 通常 24

    # ===== OS =====
    os_family: str  # "windows" | "macos" | "linux"
    os_version_ua: str  # "Windows NT 10.0" | "Macintosh; Intel Mac OS X 10_15_7"
    os_display_version: str  # "Windows 10"
    os_ua_data_platform_version: str  # "10.0.0"

    # ===== Fonts / Voices =====
    fonts_preset_id: str  # 引用 FONTS_PRESETS
    voices_preset: str  # "windows" | "macos" | "linux"

    # ===== Capabilities =====
    has_battery: bool
    max_touch_points: int

    # ===== Variants（预定好的已知真实组合）=====
    variants: list[ConfigurationVariant]

    # ===== Network =====
    typical_connection_types: list[str]
    typical_rtt_range: tuple[int, int]
    typical_downlink_range: tuple[float, float]

    # ===== Misc =====
    market_share_weight: int = 50
    prevalence_regions: list[str] = field(default_factory=list)

    def derive_selections(self, seed: int,
                           variant_id: Optional[str] = None) -> dict:
        """从 seed 派生：先选 variant（已知存在的配置），再派生 variant 内部细节

        Args:
            seed: 派生细节的随机种子
            variant_id: 显式指定 variant（None 则按权重随机选）
        """
        rng = random.Random(seed)
        # 第一步：选 variant
        if variant_id:
            variant = next((v for v in self.variants
                            if v.variant_id == variant_id), None)
            if variant is None:
                raise ValueError(
                    f"variant_id={variant_id} 不存在于 {self.id}.variants，"
                    f"可选: {[v.variant_id for v in self.variants]}")
        else:
            # 按权重随机选（但默认建议用户指定）
            variant = rng.choices(self.variants,
                                   weights=[v.weight for v in self.variants],
                                   k=1)[0]
        # 第二步：variant 内部细节（driver 版本、battery 等）
        return {
            "variant_id": variant.variant_id,
            "hc": variant.hc,
            "ram_gb": variant.ram_gb,
            "resolution": variant.resolution,
            "pixel_ratio": variant.pixel_ratio,
            "driver_ver": rng.choice(self.gpu_driver_versions),
            "device_id": rng.choice(self.gpu_device_ids),
            "battery_level": rng.choice(variant.typical_battery_levels)
                              if self.has_battery and variant.typical_battery_levels
                              else None,
            "audio_inputs": rng.choice(variant.typical_audio_inputs),
            "video_inputs": rng.choice(variant.typical_video_inputs),
            "audio_outputs": rng.choice(variant.typical_audio_outputs),
            "connection_type": rng.choice(self.typical_connection_types),
            "rtt_ms": rng.randint(*self.typical_rtt_range),
            "downlink_mbps": round(
                rng.uniform(*self.typical_downlink_range), 1),
        }


# ============================================================================
# 内置 Archetype 库
# ============================================================================

ARCHETYPES: dict[str, DeviceArchetype] = {
    # ---------- Windows 笔记本 ----------
    "dell_latitude_e6430_2012": DeviceArchetype(
        id="dell_latitude_e6430_2012",
        display_name="Dell Latitude E6430 (2012 商务本 Ivy Bridge)",
        form_factor="laptop_14",
        cpu_model="Intel Core i7-3520M",
        cpu_era_year=2012,
        gpu_vendor="Google Inc. (Intel)",
        gpu_renderer_template=(
            "ANGLE (Intel, Intel(R) HD Graphics 4000 ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["10.18.10.4252", "10.18.10.4358"],
        gpu_device_ids=["0x00000162", "0x00000166"],
        webgpu_supported=False,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 10",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_10_zh_CN_business",
        voices_preset="windows",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi", "ethernet"],
        typical_rtt_range=(20, 80),
        typical_downlink_range=(10, 100),
        market_share_weight=30,
        prevalence_regions=["CN", "SG", "TW", "HK", "MY"],
        variants=[
            # variant 1: 典型商务用户（外接显示器 2K）— 最常见
            ConfigurationVariant(
                variant_id="business_i7_8gb_2k_extdisp",
                display_name="i7 / 8GB / 外接 2K 显示器",
                weight=50,
                hc=8, ram_gb=8, resolution=(2560, 1440),
                typical_battery_levels=[0.6, 0.8, 0.95],
            ),
            # variant 2: 标配 FHD（本机屏）
            ConfigurationVariant(
                variant_id="business_i7_8gb_fhd",
                display_name="i7 / 8GB / 1920x1080 本机屏",
                weight=30,
                hc=8, ram_gb=8, resolution=(1920, 1080),
                typical_battery_levels=[0.5, 0.7, 0.9],
            ),
            # variant 3: 低配 i5（原版）
            ConfigurationVariant(
                variant_id="budget_i5_4gb_hd",
                display_name="i5 / 4GB / 1366x768",
                weight=20,
                hc=4, ram_gb=4, resolution=(1366, 768),
                typical_battery_levels=[0.3, 0.5, 0.7],
            ),
        ],
    ),

    "lenovo_thinkpad_t480_2018": DeviceArchetype(
        id="lenovo_thinkpad_t480_2018",
        display_name="Lenovo ThinkPad T480 (2018 商务本 Kaby Lake R)",
        form_factor="laptop_14",
        cpu_model="Intel Core i7-8550U",
        cpu_era_year=2018,
        gpu_vendor="Google Inc. (Intel)",
        gpu_renderer_template=(
            "ANGLE (Intel, Intel(R) UHD Graphics 620 ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["27.20.100.9415", "30.0.101.1340", "31.0.101.2111"],
        gpu_device_ids=["0x00005917"],
        webgpu_supported=True,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 10",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_10_en_US_basic",
        voices_preset="windows",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi", "ethernet"],
        typical_rtt_range=(15, 60),
        typical_downlink_range=(20, 200),
        market_share_weight=80,
        prevalence_regions=["US", "EU", "CN", "SG", "JP"],
        variants=[
            ConfigurationVariant(
                variant_id="i7_16gb_fhd", display_name="i7 / 16GB / FHD",
                weight=50, hc=8, ram_gb=16, resolution=(1920, 1080),
                pixel_ratio=1.25,
                typical_battery_levels=[0.5, 0.7, 0.9]),
            ConfigurationVariant(
                variant_id="i7_32gb_wqhd", display_name="i7 / 32GB / WQHD",
                weight=30, hc=8, ram_gb=32, resolution=(2560, 1440),
                pixel_ratio=1.0,
                typical_battery_levels=[0.5, 0.75, 0.95]),
            ConfigurationVariant(
                variant_id="i5_8gb_fhd", display_name="i5 / 8GB / FHD",
                weight=20, hc=4, ram_gb=8, resolution=(1920, 1080),
                typical_battery_levels=[0.4, 0.6, 0.85]),
        ],
    ),

    "asus_rog_strix_g16_2023": DeviceArchetype(
        id="asus_rog_strix_g16_2023",
        display_name="ASUS ROG Strix G16 (2023 游戏本 RTX 4070)",
        form_factor="laptop_17",
        cpu_model="Intel Core i9-13980HX",
        cpu_era_year=2023,
        gpu_vendor="Google Inc. (NVIDIA)",
        gpu_renderer_template=(
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["31.0.15.5161", "32.0.15.6094", "32.0.15.6614"],
        gpu_device_ids=["0x00002882"],
        webgpu_supported=True,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 11",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_11_en_US_2024",
        voices_preset="windows",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi", "ethernet"],
        typical_rtt_range=(10, 50),
        typical_downlink_range=(50, 500),
        market_share_weight=40,
        prevalence_regions=["US", "CN", "KR", "JP"],
        variants=[
            ConfigurationVariant(
                variant_id="i9_32gb_wqxga",
                display_name="i9 / 32GB / 2560x1600 165Hz",
                weight=60, hc=32, ram_gb=32, resolution=(2560, 1600),
                typical_battery_levels=[0.4, 0.6, 0.95]),
            ConfigurationVariant(
                variant_id="i7_16gb_fhd",
                display_name="i7 / 16GB / 1920x1200",
                weight=40, hc=24, ram_gb=16, resolution=(1920, 1200),
                typical_battery_levels=[0.4, 0.65, 0.9]),
        ],
    ),

    "microsoft_surface_pro_9_2022": DeviceArchetype(
        id="microsoft_surface_pro_9_2022",
        display_name="Microsoft Surface Pro 9 (2022 触控平板)",
        form_factor="tablet",
        cpu_model="Intel Core i5-1235U",
        cpu_era_year=2022,
        gpu_vendor="Google Inc. (Intel)",
        gpu_renderer_template=(
            "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["31.0.101.4575", "31.0.101.5186"],
        gpu_device_ids=["0x000046A8"],
        webgpu_supported=True,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 11",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_11_en_US_2024",
        voices_preset="windows",
        has_battery=True,
        max_touch_points=10,
        typical_connection_types=["wifi", "4g"],
        typical_rtt_range=(15, 80),
        typical_downlink_range=(10, 300),
        market_share_weight=20,
        prevalence_regions=["US", "EU", "JP"],
        variants=[
            ConfigurationVariant(
                variant_id="i5_8gb_retina",
                display_name="i5 / 8GB / 2880x1920",
                weight=60, hc=12, ram_gb=8, resolution=(2880, 1920),
                pixel_ratio=2.0,
                typical_battery_levels=[0.4, 0.65, 0.85],
                typical_audio_inputs=[2], typical_video_inputs=[2]),
            ConfigurationVariant(
                variant_id="i7_16gb_retina",
                display_name="i7 / 16GB / 2880x1920",
                weight=40, hc=12, ram_gb=16, resolution=(2880, 1920),
                pixel_ratio=2.0,
                typical_battery_levels=[0.5, 0.75, 0.95],
                typical_audio_inputs=[2], typical_video_inputs=[2]),
        ],
    ),

    # ---------- Windows 台式机 ----------
    "desktop_dell_optiplex_7020_2015": DeviceArchetype(
        id="desktop_dell_optiplex_7020_2015",
        display_name="Dell OptiPlex 7020 (2015 办公台式)",
        form_factor="desktop",
        cpu_model="Intel Core i7-4790",
        cpu_era_year=2014,
        gpu_vendor="Google Inc. (Intel)",
        gpu_renderer_template=(
            "ANGLE (Intel, Intel(R) HD Graphics 4600 ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["10.18.14.4264", "20.19.15.4531", "27.20.100.8336"],
        gpu_device_ids=["0x00000412", "0x00000416"],
        webgpu_supported=False,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 10",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_10_en_US_basic",
        voices_preset="windows",
        has_battery=False,
        max_touch_points=0,
        typical_connection_types=["ethernet", "wifi"],
        typical_rtt_range=(5, 30),
        typical_downlink_range=(50, 1000),
        market_share_weight=70,
        prevalence_regions=["US", "EU", "CN"],
        variants=[
            ConfigurationVariant(
                variant_id="i7_8gb_fhd", display_name="i7 / 8GB / FHD",
                weight=60, hc=8, ram_gb=8, resolution=(1920, 1080),
                typical_audio_inputs=[0, 1], typical_video_inputs=[0]),
            ConfigurationVariant(
                variant_id="i5_8gb_hd_plus", display_name="i5 / 8GB / 1920x1200",
                weight=40, hc=4, ram_gb=8, resolution=(1920, 1200),
                typical_audio_inputs=[0], typical_video_inputs=[0]),
        ],
    ),

    "desktop_custom_rtx_4070_2024": DeviceArchetype(
        id="desktop_custom_rtx_4070_2024",
        display_name="Gaming PC RTX 4070 + Ryzen 9 (2024 高端台式)",
        form_factor="desktop",
        cpu_model="AMD Ryzen 9 7950X",
        cpu_era_year=2023,
        gpu_vendor="Google Inc. (NVIDIA)",
        gpu_renderer_template=(
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 ({device_id}) "
            "Direct3D11 vs_5_0 ps_5_0, D3D11-{driver_ver})"
        ),
        gpu_driver_versions=["31.0.15.5161", "32.0.15.6094", "32.0.15.6614"],
        gpu_device_ids=["0x00002786", "0x00002783"],
        webgpu_supported=True,
        color_depth=24,
        os_family="windows",
        os_version_ua="Windows NT 10.0",
        os_display_version="Windows 11",
        os_ua_data_platform_version="10.0.0",
        fonts_preset_id="windows_11_en_US_2024",
        voices_preset="windows",
        has_battery=False,
        max_touch_points=0,
        typical_connection_types=["ethernet", "wifi"],
        typical_rtt_range=(5, 40),
        typical_downlink_range=(100, 1000),
        market_share_weight=30,
        prevalence_regions=["US", "EU", "CN", "KR"],
        variants=[
            ConfigurationVariant(
                variant_id="r9_32gb_wqhd",
                display_name="Ryzen 9 / 32GB / 2560x1440",
                weight=50, hc=32, ram_gb=32, resolution=(2560, 1440),
                typical_audio_inputs=[1, 2], typical_video_inputs=[0, 1]),
            ConfigurationVariant(
                variant_id="r9_64gb_4k",
                display_name="Ryzen 9 / 64GB / 3840x2160",
                weight=30, hc=32, ram_gb=64, resolution=(3840, 2160),
                pixel_ratio=1.5,
                typical_audio_inputs=[1, 2], typical_video_inputs=[0, 1]),
            ConfigurationVariant(
                variant_id="r9_32gb_uw",
                display_name="Ryzen 9 / 32GB / 3440x1440 超宽",
                weight=20, hc=32, ram_gb=32, resolution=(3440, 1440),
                typical_audio_inputs=[1, 2], typical_video_inputs=[0, 1]),
        ],
    ),

    # ---------- macOS ----------
    "macbook_air_m2_2022": DeviceArchetype(
        id="macbook_air_m2_2022",
        display_name="MacBook Air M2 (2022 13-inch)",
        form_factor="laptop_13",
        cpu_model="Apple M2",
        cpu_era_year=2022,
        gpu_vendor="Google Inc. (Apple)",
        gpu_renderer_template="ANGLE (Apple, Apple M2, OpenGL 4.1)",
        gpu_driver_versions=["OpenGL 4.1"],
        gpu_device_ids=["-"],
        webgpu_supported=True,
        color_depth=30,
        os_family="macos",
        os_version_ua="Macintosh; Intel Mac OS X 10_15_7",
        os_display_version="macOS 14",
        os_ua_data_platform_version="14.6.0",
        fonts_preset_id="macos_14_default",
        voices_preset="macos",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi"],
        typical_rtt_range=(15, 60),
        typical_downlink_range=(50, 500),
        market_share_weight=80,
        prevalence_regions=["US", "EU", "CN", "JP", "HK", "SG"],
        variants=[
            ConfigurationVariant(
                variant_id="m2_8gb_retina",
                display_name="M2 / 8GB / 1512x982 retina",
                weight=60, hc=8, ram_gb=8, resolution=(1512, 982),
                pixel_ratio=2.0,
                typical_battery_levels=[0.5, 0.75, 0.95],
                typical_audio_inputs=[3]),
            ConfigurationVariant(
                variant_id="m2_16gb_retina",
                display_name="M2 / 16GB / 1512x982 retina",
                weight=40, hc=8, ram_gb=16, resolution=(1512, 982),
                pixel_ratio=2.0,
                typical_battery_levels=[0.55, 0.8, 0.95],
                typical_audio_inputs=[3]),
        ],
    ),

    "macbook_pro_m3_pro_2023": DeviceArchetype(
        id="macbook_pro_m3_pro_2023",
        display_name="MacBook Pro M3 Pro (2023 14-inch)",
        form_factor="laptop_14",
        cpu_model="Apple M3 Pro",
        cpu_era_year=2023,
        gpu_vendor="Google Inc. (Apple)",
        gpu_renderer_template="ANGLE (Apple, Apple M3 Pro, OpenGL 4.1)",
        gpu_driver_versions=["OpenGL 4.1"],
        gpu_device_ids=["-"],
        webgpu_supported=True,
        color_depth=30,
        os_family="macos",
        os_version_ua="Macintosh; Intel Mac OS X 10_15_7",
        os_display_version="macOS 14",
        os_ua_data_platform_version="14.6.0",
        fonts_preset_id="macos_14_default",
        voices_preset="macos",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi"],
        typical_rtt_range=(10, 50),
        typical_downlink_range=(100, 800),
        market_share_weight=60,
        prevalence_regions=["US", "EU", "CN", "JP", "HK", "SG"],
        variants=[
            ConfigurationVariant(
                variant_id="m3pro_18gb",
                display_name="M3 Pro 11-core / 18GB",
                weight=60, hc=11, ram_gb=18, resolution=(1512, 982),
                pixel_ratio=2.0,
                typical_battery_levels=[0.55, 0.8, 0.95],
                typical_audio_inputs=[3]),
            ConfigurationVariant(
                variant_id="m3pro_36gb",
                display_name="M3 Pro 12-core / 36GB",
                weight=40, hc=12, ram_gb=36, resolution=(1512, 982),
                pixel_ratio=2.0,
                typical_battery_levels=[0.6, 0.85, 0.95],
                typical_audio_inputs=[3]),
        ],
    ),

    "imac_24_m1_2021": DeviceArchetype(
        id="imac_24_m1_2021",
        display_name="iMac 24-inch M1 (2021 desktop all-in-one)",
        form_factor="desktop",
        cpu_model="Apple M1",
        cpu_era_year=2021,
        gpu_vendor="Google Inc. (Apple)",
        gpu_renderer_template="ANGLE (Apple, Apple M1, OpenGL 4.1)",
        gpu_driver_versions=["OpenGL 4.1"],
        gpu_device_ids=["-"],
        webgpu_supported=True,
        color_depth=30,
        os_family="macos",
        os_version_ua="Macintosh; Intel Mac OS X 10_15_7",
        os_display_version="macOS 14",
        os_ua_data_platform_version="14.6.0",
        fonts_preset_id="macos_14_default",
        voices_preset="macos",
        has_battery=False,
        max_touch_points=0,
        typical_connection_types=["wifi", "ethernet"],
        typical_rtt_range=(5, 30),
        typical_downlink_range=(100, 1000),
        market_share_weight=40,
        prevalence_regions=["US", "EU", "CN", "JP"],
        variants=[
            ConfigurationVariant(
                variant_id="m1_8gb_45k",
                display_name="M1 / 8GB / 4.5K Retina",
                weight=60, hc=8, ram_gb=8, resolution=(2240, 1260),
                pixel_ratio=2.0,
                typical_audio_inputs=[1, 2], typical_audio_outputs=[1, 6]),
            ConfigurationVariant(
                variant_id="m1_16gb_45k",
                display_name="M1 / 16GB / 4.5K Retina",
                weight=40, hc=8, ram_gb=16, resolution=(2240, 1260),
                pixel_ratio=2.0,
                typical_audio_inputs=[1, 2], typical_audio_outputs=[1, 6]),
        ],
    ),

    # ---------- Linux ----------
    "thinkpad_t14_ubuntu_2022": DeviceArchetype(
        id="thinkpad_t14_ubuntu_2022",
        display_name="Lenovo ThinkPad T14 Gen3 Ubuntu 22.04 (2022)",
        form_factor="laptop_14",
        cpu_model="AMD Ryzen 7 PRO 6850U",
        cpu_era_year=2022,
        gpu_vendor="Google Inc. (AMD)",
        gpu_renderer_template=(
            "ANGLE (AMD, AMD Radeon Graphics (RADV REMBRANDT), "
            "23.1.1 (Mesa {driver_ver}))"
        ),
        gpu_driver_versions=["23.0.4", "23.1.5", "23.3.3"],
        gpu_device_ids=["0x00001681"],
        webgpu_supported=True,
        color_depth=24,
        os_family="linux",
        os_version_ua="X11; Linux x86_64",
        os_display_version="Ubuntu 22.04",
        os_ua_data_platform_version="22.04.0",
        fonts_preset_id="linux_ubuntu_22_default",
        voices_preset="linux",
        has_battery=True,
        max_touch_points=0,
        typical_connection_types=["wifi", "ethernet"],
        typical_rtt_range=(10, 60),
        typical_downlink_range=(20, 300),
        market_share_weight=10,
        prevalence_regions=["US", "EU", "IN"],
        variants=[
            ConfigurationVariant(
                variant_id="r7_16gb_fhd", display_name="Ryzen 7 / 16GB / FHD",
                weight=60, hc=16, ram_gb=16, resolution=(1920, 1080),
                typical_battery_levels=[0.5, 0.75, 0.9]),
            ConfigurationVariant(
                variant_id="r7_32gb_2k", display_name="Ryzen 7 / 32GB / 2240x1400",
                weight=40, hc=16, ram_gb=32, resolution=(2240, 1400),
                pixel_ratio=1.25,
                typical_battery_levels=[0.5, 0.8, 0.95]),
        ],
    ),
}


# ============================================================================
# v3.2: 从 GPU 数据库自动扩展 Archetype 库（40+ GPU → 450+ variants）
# ============================================================================

def _load_auto_generated_archetypes():
    """从 gpu_hw_database 载入自动生成的 archetypes"""
    try:
        from gpu_hw_database import generate_archetypes
        auto = generate_archetypes()
        # 合并到 ARCHETYPES（不覆盖手写的）
        for aid, arc in auto.items():
            if aid not in ARCHETYPES:
                ARCHETYPES[aid] = arc
    except ImportError:
        pass  # 没有 gpu_hw_database 时，沿用手写库


_load_auto_generated_archetypes()


# ============================================================================
# 交叉校验规则
# ============================================================================

class ValidationWarning:
    def __init__(self, severity: str, rule: str, msg: str):
        self.severity = severity  # ERROR | WARN | INFO
        self.rule = rule
        self.msg = msg

    def __repr__(self):
        return f"[{self.severity}] {self.rule}: {self.msg}"


def validate_profile(archetype: DeviceArchetype, selections: dict,
                      timezone: str, language: str,
                      battery_level: Optional[float],
                      screen_w: int, screen_h: int) -> list[ValidationWarning]:
    """交叉校验一个 Profile 的字段组合"""
    warnings = []

    # 找到对应的 variant
    vid = selections.get("variant_id")
    variant = next((v for v in archetype.variants if v.variant_id == vid), None)
    if variant is None:
        warnings.append(ValidationWarning(
            "ERROR", "variant_not_found",
            f"variant_id={vid} 不存在于 {archetype.id}.variants"))
        return warnings

    # Rule 1: HC 必须匹配 variant
    if selections.get("hc") != variant.hc:
        warnings.append(ValidationWarning(
            "ERROR", "hc_matches_variant",
            f"HC={selections.get('hc')} 与 variant {vid} 的 HC={variant.hc} 不符"))

    # Rule 2: RAM 必须匹配 variant
    if selections.get("ram_gb") != variant.ram_gb:
        warnings.append(ValidationWarning(
            "ERROR", "ram_matches_variant",
            f"RAM={selections.get('ram_gb')} 与 variant {vid} 的 RAM={variant.ram_gb} 不符"))

    # Rule 3: Resolution 必须匹配 variant
    if (screen_w, screen_h) != variant.resolution:
        warnings.append(ValidationWarning(
            "ERROR", "resolution_matches_variant",
            f"({screen_w}x{screen_h}) 与 variant {vid}={variant.resolution} 不符"))

    # Rule 4: battery 一致性
    if archetype.has_battery and battery_level is None:
        warnings.append(ValidationWarning(
            "WARN", "battery_must_set",
            f"{archetype.id} 是笔记本应有 battery_level"))
    elif not archetype.has_battery and battery_level is not None:
        warnings.append(ValidationWarning(
            "ERROR", "desktop_no_battery",
            f"{archetype.id} 是桌面不应有 battery_level"))

    # Rule 4: touch points 合理性
    if archetype.form_factor == "desktop" and archetype.max_touch_points > 0:
        warnings.append(ValidationWarning(
            "ERROR", "desktop_no_touch",
            f"desktop 不应有 touch_points"))

    # Rule 5: TZ/Language 合理性（soft）
    tz_lang_inconsistencies = {
        ("Asia/Shanghai", "ja-JP"): "TZ=Shanghai 但 lang=ja-JP 罕见",
        ("Asia/Tokyo", "zh-CN"): "TZ=Tokyo 但 lang=zh-CN 罕见",
        ("America/New_York", "zh-CN"): "TZ=NY 但 lang=zh-CN (移民可能)",
    }
    hint = tz_lang_inconsistencies.get((timezone, language))
    if hint:
        warnings.append(ValidationWarning("INFO", "tz_lang_hint", hint))

    return warnings


# ============================================================================
# Helpers
# ============================================================================

def list_archetypes(region: Optional[str] = None,
                     form_factor: Optional[str] = None,
                     os_family: Optional[str] = None) -> list[DeviceArchetype]:
    """按过滤条件列出 archetypes，按权重排序"""
    result = []
    for a in ARCHETYPES.values():
        if region and region not in (a.prevalence_regions or []):
            continue
        if form_factor and a.form_factor != form_factor:
            continue
        if os_family and a.os_family != os_family:
            continue
        result.append(a)
    result.sort(key=lambda x: -x.market_share_weight)
    return result


def random_archetype(seed: int,
                      region: Optional[str] = None,
                      os_family: Optional[str] = None) -> DeviceArchetype:
    """按 market share 权重随机选一个 archetype"""
    candidates = list_archetypes(region=region, os_family=os_family)
    if not candidates:
        raise ValueError(f"无符合条件的 archetype: region={region}, os={os_family}")
    rng = random.Random(seed)
    weights = [a.market_share_weight for a in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


if __name__ == "__main__":
    # 自检
    print(f"Archetype count: {len(ARCHETYPES)}")
    print(f"Fonts presets:   {list(FONTS_PRESETS.keys())}")
    print()
    for aid, a in ARCHETYPES.items():
        fonts_ok = a.fonts_preset_id in FONTS_PRESETS
        hc_set = sorted(set(v.hc for v in a.variants))
        print(f"  {aid:<40s} {'[OK]' if fonts_ok else '[NO fonts!]'} "
              f"| {a.form_factor} | {a.os_family} | HC={hc_set} "
              f"| {len(a.variants)} variants")

    print("\n[Test] derive_selections for dell_latitude_e6430:")
    arch = ARCHETYPES["dell_latitude_e6430_2012"]
    sel = arch.derive_selections(seed=12345)
    for k, v in sel.items():
        print(f"  {k}: {v}")

    print("\n[Test] validate with mismatched HC:")
    bad_sel = dict(sel, hc=20)  # Wrong HC for HD 4000
    ws = validate_profile(
        arch, bad_sel,
        timezone="Asia/Shanghai", language="zh-CN",
        battery_level=0.82, screen_w=1920, screen_h=1080)
    for w in ws:
        print(f"  {w}")

    print("\n[Test] random Chinese Windows laptop:")
    a = random_archetype(seed=42, region="CN", os_family="windows")
    print(f"  Picked: {a.id} ({a.display_name})")
