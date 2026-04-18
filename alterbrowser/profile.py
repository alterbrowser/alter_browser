"""
Profile — dataclass 形式描述一个 stealth-chromium 启动配置。

>>> from alterbrowser.profile import Profile
>>> p = Profile(seed=12345, platform="Win32")
>>> p.save("profile.json")
>>> p2 = Profile.load("profile.json")
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_log = logging.getLogger(__name__)

from .errors import ProfileLoadError, ProfileValidationError
from .fonts import FontMode
from .modes import FingerprintMode, SourceMode, WebRTCMode, TriState
from .utils import safe_filename


def _script_directory() -> str:
    """推测用户入口脚本所在目录。交互式 / -c 场景兜底到 CWD。"""
    try:
        argv0 = sys.argv[0] if sys.argv else ""
        if argv0 and os.path.isfile(argv0):
            return os.path.dirname(os.path.abspath(argv0))
    except Exception:
        pass
    return os.getcwd()


def _detect_chrome_binary() -> str:
    """
    探测 **patch 过的** stealth Chromium 路径。

    重要：alterbrowser 需要 patch 过的 Chromium（带 ``--fingerprint`` 等开关），
    不能用普通 Google Chrome / Edge；它们不认这些开关，所有指纹伪装会静默失效。

    约定的探测顺序（从高到低优先级）：
        1. 环境变量 ALTERBROWSER_CHROME_BINARY
        2. **用户脚本同目录** ./chrome.exe（最推荐 —— 脚本和 chrome 放一起即可）
        3. **用户脚本同目录** ./chrome/chrome.exe （子目录版）
        4. 当前工作目录 ./chrome.exe / ./chrome/chrome.exe
        5. 开发者本地 build 输出 <pkg_parent>/build/src/out/Default/chrome.exe
        6. ~/.alterbrowser/chrome/chrome.exe （约定分发位置）

    找不到时返回占位路径，launch 时会报带引导的错。
    """
    # 1. 显式环境变量
    env = os.environ.get("ALTERBROWSER_CHROME_BINARY")
    if env:
        return env

    exe_name = "chrome.exe" if os.name == "nt" else "chrome"

    # 2-3. 脚本同目录
    script_dir = _script_directory()
    for candidate in (
        os.path.join(script_dir, exe_name),
        os.path.join(script_dir, "chrome", exe_name),
    ):
        if os.path.isfile(candidate):
            return candidate

    # 4. 当前工作目录（可能与脚本目录不同）
    cwd = os.getcwd()
    if cwd != script_dir:
        for candidate in (
            os.path.join(cwd, exe_name),
            os.path.join(cwd, "chrome", exe_name),
        ):
            if os.path.isfile(candidate):
                return candidate

    # 5. 开发者本地 build 输出
    pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_build = os.path.join(pkg_parent, "build", "src", "out", "Default", exe_name)
    if os.path.isfile(local_build):
        return local_build

    # 6. ~/.alterbrowser/chrome/
    home_dist = os.path.expanduser(os.path.join("~", ".alterbrowser", "chrome", exe_name))
    if os.path.isfile(home_dist):
        return home_dist

    # 找不到 — 返回脚本目录下的 chrome.exe 占位，launch 时报友好错误
    return os.path.join(script_dir, exe_name)


# 注：DEFAULT_CHROME_BINARY 作为"建议默认值"仅在 import 时算一次；
# 真正运行时由 Profile.__post_init__ 调用 _detect_chrome_binary() 重新解析，
# 这样 sys.argv[0] 能反映用户入口脚本的真实路径。
DEFAULT_CHROME_BINARY = _detect_chrome_binary()

DEFAULT_PROFILES_BASE = os.environ.get(
    "ALTERBROWSER_PROFILES_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles"),
)


@dataclass
class Profile:
    """
    描述一个 alterbrowser 启动配置。

    v0.2 重构：加入 archetype_id / FingerprintMode / SourceMode 等字段，
    覆盖 14 大项指纹能力维度。
    """

    # ===== 核心 =====
    seed: Optional[int] = None   # 留空自动生成（基于时间戳 + 熵）
    name: str = ""
    user_data_dir: Optional[str] = None

    # ===== Archetype（v0.2 推荐用法）=====
    archetype_id: Optional[str] = None
    archetype_selections: Optional[Dict[str, Any]] = None
    fingerprint_mode: FingerprintMode = FingerprintMode.REALISTIC

    # ===== 浏览器版本（3. User-Agent）=====
    brand: str = "Chrome"
    brand_version: str = "142"
    user_agent: Optional[str] = None   # None = Chrome 默认

    # ===== OS（8. 语言）=====
    platform: str = "Win32"
    platform_version: str = "10.0.0"
    language: str = "zh-CN"
    accept_lang: Optional[str] = None  # None = 自动 "<language>,<lang-short>;q=0.9"

    # ===== 时区 / 地理位置（7a/7b）=====
    timezone_mode: SourceMode = SourceMode.REAL
    timezone: Optional[str] = None
    geolocation_mode: SourceMode = SourceMode.REAL
    geolocation: Optional[Tuple[float, float, float]] = None   # (lat, lon, accuracy)

    # ===== 硬件 CPU / RAM（12b/12c）=====
    cpu_mode: SourceMode = SourceMode.REAL
    hardware_concurrency: Optional[int] = None
    ram_mode: SourceMode = SourceMode.REAL
    device_memory: Optional[int] = None

    # ===== 分辨率（9）=====
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    screen_color_depth: Optional[int] = None
    max_touch_points: Optional[int] = None

    # ===== WebGL 元数据 / WebGPU（11 / 12a）=====
    gpu_mode: SourceMode = SourceMode.REAL
    gpu_vendor: Optional[str] = None
    gpu_renderer: Optional[str] = None
    webgpu_mode: SourceMode = SourceMode.REAL

    # ===== 硬件噪声（10a-f）=====
    noise_canvas: bool = True
    noise_webgl_image: bool = True
    noise_audio: bool = True
    noise_clientrects: bool = True
    media_devices_mode: SourceMode = SourceMode.REAL
    media_devices: Optional[str] = None  # "audio_in:video_in:audio_out"
    voices_mode: SourceMode = SourceMode.REAL
    voices_preset: Optional[str] = None  # "windows" | "macos" | "linux"

    # ===== 字体（2）=====
    fonts_mode: FontMode = FontMode.DEFAULT
    fonts_custom: List[str] = field(default_factory=list)

    # ===== WebRTC（6）=====
    webrtc_mode: WebRTCMode = WebRTCMode.REAL
    webrtc_public_ip: Optional[str] = None

    # ===== 代理 / Cookie（5 / 4）=====
    proxy: Optional[str] = None
    cookies_file: Optional[str] = None
    cookies_json: Optional[List[Dict[str, Any]]] = None

    # ===== 媒体 / 其它（保留兼容字段）=====
    battery_level: Optional[float] = None
    connection: Optional[str] = None

    # ===== 隐私 / 高级（13 / 14）=====
    do_not_track: TriState = TriState.DEFAULT
    port_scan_protection: bool = True
    port_scan_allow_list: List[int] = field(default_factory=list)
    hardware_accel: TriState = TriState.DEFAULT
    disable_tls_features: bool = False

    # ===== Chrome =====
    chrome_binary: str = DEFAULT_CHROME_BINARY
    extra_args: List[str] = field(default_factory=list)
    start_url: Optional[str] = None

    # ===== 元信息（不传给 Chrome）=====
    note: str = ""
    tags: List[str] = field(default_factory=list)

    # ===== Shorthand 快捷字段（post_init 里展开到真实字段）=====
    # 这些字段本身不传给 Chrome，只是便于用户一行表达意图。
    # 例：Profile(gpu="RTX 5090", cpu="i9-14900K", os="win11", resolution="4K", city="Shanghai")
    gpu: Optional[str] = None           # "RTX 5090" / "M2 Pro" / 任意字符串
    cpu: Optional[str] = None           # "i9-14900K" / "Ryzen 9 7950X" / "M2"
    os: Optional[str] = None            # "win11" / "macos 14" / "linux"
    resolution: Optional[str] = None    # "1920x1080" / "4K" / "qhd"
    city: Optional[str] = None          # "Shanghai" / "New York" / "Tokyo"
    mobile: Any = None                  # True=android / "android" / "ios"

    # ============================================
    # 校验 & 序列化
    # ============================================

    def __post_init__(self):
        # seed 可选：缺省时用时间戳 + 熵自动生成
        if self.seed is None:
            from .utils import random_seed
            self.seed = random_seed()
        # chrome_binary 运行时再解析一次（用户没显式传才重算），
        # 这样 sys.argv[0] 能反映真实脚本路径
        if self.chrome_binary == DEFAULT_CHROME_BINARY:
            self.chrome_binary = _detect_chrome_binary()
        # 先展开 shorthand 简写字段（gpu / cpu / os / resolution / city）
        self._expand_shorthand()
        # 规范化所有枚举字段（接受字符串输入）
        self.fonts_mode = FontMode.parse(self.fonts_mode)
        self.fingerprint_mode = FingerprintMode.parse(self.fingerprint_mode)
        self.timezone_mode = SourceMode.parse(self.timezone_mode)
        self.geolocation_mode = SourceMode.parse(self.geolocation_mode)
        self.cpu_mode = SourceMode.parse(self.cpu_mode)
        self.ram_mode = SourceMode.parse(self.ram_mode)
        self.gpu_mode = SourceMode.parse(self.gpu_mode)
        self.webgpu_mode = SourceMode.parse(self.webgpu_mode)
        self.media_devices_mode = SourceMode.parse(self.media_devices_mode)
        self.voices_mode = SourceMode.parse(self.voices_mode)
        self.webrtc_mode = WebRTCMode.parse(self.webrtc_mode)
        self.do_not_track = TriState.parse(self.do_not_track)
        self.hardware_accel = TriState.parse(self.hardware_accel)
        # accept_lang 自动派生
        if self.accept_lang is None:
            short = self.language.split("-")[0]
            self.accept_lang = f"{self.language},{short};q=0.9" if short != self.language else self.language
        self.validate()

    def validate(self) -> None:
        """字段值校验。非法抛 ProfileValidationError。"""
        if not isinstance(self.seed, int):
            raise ProfileValidationError("seed must be int")
        if self.seed < 0:
            raise ProfileValidationError("seed must be >= 0")

        if self.hardware_concurrency is not None and not (1 <= self.hardware_concurrency <= 128):
            raise ProfileValidationError("hardware_concurrency must be 1..128")
        _VALID_DEVICE_MEMORY = (0.25, 0.5, 1, 2, 4, 8, 16, 32, 64)
        if self.device_memory is not None and self.device_memory not in _VALID_DEVICE_MEMORY:
            raise ProfileValidationError(
                f"device_memory must be one of {_VALID_DEVICE_MEMORY}, got {self.device_memory}"
            )

        # 下限放宽支持移动端 (iPhone SE 宽度 320)
        if self.screen_width is not None and not (320 <= self.screen_width <= 7680):
            raise ProfileValidationError(
                f"screen_width must be 320..7680, got {self.screen_width}")
        if self.screen_height is not None and not (400 <= self.screen_height <= 4320):
            raise ProfileValidationError(
                f"screen_height must be 400..4320, got {self.screen_height}")

        if self.battery_level is not None and not (0.0 <= self.battery_level <= 1.0):
            raise ProfileValidationError("battery_level must be 0.0..1.0")

        if self.geolocation is not None:
            if len(self.geolocation) < 2 or len(self.geolocation) > 3:
                raise ProfileValidationError("geolocation must be (lat, lon) or (lat, lon, acc)")
            lat, lon = self.geolocation[0], self.geolocation[1]
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ProfileValidationError("geolocation out of WGS84 range")

    # ------- shorthand 展开 -------

    def _expand_shorthand(self) -> None:
        """
        把 shorthand 字段（gpu/cpu/os/resolution/city）展开成底层真实字段。
        规则：字段当前值等于 dataclass 默认值时，就视作"未显式设置"，可以被 shorthand 覆盖。
        """
        from .presets import expand_shorthand
        expanded = expand_shorthand(
            gpu=self.gpu,
            cpu=self.cpu,
            os=self.os,
            resolution=self.resolution,
            city=self.city,
            mobile=self.mobile,
        )
        if not expanded:
            return

        defaults = {f.name: f.default for f in fields(self)}
        for k, v in expanded.items():
            current = getattr(self, k, None)
            default = defaults.get(k)
            # 当前值等于默认值 → 视作未设置；否则尊重用户显式配置
            if current == default or current is None or current == "":
                setattr(self, k, v)

    # ------- 序列化 -------

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 把所有枚举转为字符串值（便于 JSON 序列化）
        enum_fields = [
            "fonts_mode", "fingerprint_mode",
            "timezone_mode", "geolocation_mode",
            "cpu_mode", "ram_mode", "gpu_mode", "webgpu_mode",
            "media_devices_mode", "voices_mode",
            "webrtc_mode",
            "do_not_track", "hardware_accel",
        ]
        for f in enum_fields:
            val = getattr(self, f, None)
            if hasattr(val, "value"):
                d[f] = val.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str) -> None:
        """保存到 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """从 dict 构造 Profile；忽略未知字段（含警告），缺失字段用默认值"""
        allowed = {f.name for f in fields(cls)}
        unknown = [k for k in data if k not in allowed and not k.startswith("_")]
        if unknown:
            _log.warning("Profile.from_dict: ignoring unknown fields: %s", unknown)
        clean = {k: v for k, v in data.items() if k in allowed}
        # geolocation 如果是 list 则转 tuple
        if "geolocation" in clean and isinstance(clean["geolocation"], list):
            clean["geolocation"] = tuple(clean["geolocation"])
        return cls(**clean)

    @classmethod
    def load(cls, path: str) -> "Profile":
        """从 JSON 文件加载"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise ProfileLoadError(f"profile not found: {path}") from e
        except json.JSONDecodeError as e:
            raise ProfileLoadError(f"invalid JSON in {path}: {e}") from e
        return cls.from_dict(data)

    # ------- 克隆 / 对比 -------

    def clone(self, **overrides) -> "Profile":
        """克隆并覆盖指定字段"""
        d = self.to_dict()
        d.update(overrides)
        # 重新构造时走 __post_init__ 校验
        return self.__class__.from_dict(d)

    def diff(self, other: "Profile") -> Dict[str, Tuple[Any, Any]]:
        """返回和另一个 Profile 的字段差异"""
        a = self.to_dict()
        b = other.to_dict()
        return {k: (a[k], b[k]) for k in a.keys() | b.keys() if a.get(k) != b.get(k)}

    # ------- 自动派生 -------

    def auto_user_data_dir(self, base: str = None) -> str:
        """若未设置 user_data_dir，自动生成一个路径"""
        import os as _os
        if self.user_data_dir:
            return self.user_data_dir
        if base is None:
            base = DEFAULT_PROFILES_BASE
        nm = safe_filename(self.name) if self.name else f"seed_{self.seed}"
        return _os.path.join(base, nm)


# ============================================================
# ProfileBatch
# ============================================================

class ProfileBatch:
    """
    管理一组 Profile。

    >>> batch = ProfileBatch.from_seeds([100, 200, 300])
    >>> len(batch)
    3
    """

    def __init__(self, profiles: List[Profile]):
        self.profiles = list(profiles)

    def __iter__(self):
        return iter(self.profiles)

    def __len__(self):
        return len(self.profiles)

    def __getitem__(self, i):
        return self.profiles[i]

    @classmethod
    def from_seeds(cls, seeds: List[int], base_config: Optional[Dict[str, Any]] = None) -> "ProfileBatch":
        """从 seed 列表批量生成 Profile"""
        base_config = base_config or {}
        profiles = []
        for s in seeds:
            cfg = {**base_config, "seed": s, "name": f"seed_{s}"}
            profiles.append(Profile.from_dict(cfg))
        return cls(profiles)

    @classmethod
    def from_directory(cls, path: str, pattern: str = "*.json") -> "ProfileBatch":
        """从目录加载所有 .json profile"""
        root = Path(path)
        if not root.is_dir():
            raise ProfileLoadError(f"not a directory: {path}")
        profiles = []
        for p in sorted(root.glob(pattern)):
            try:
                profiles.append(Profile.load(str(p)))
            except ProfileLoadError:
                continue   # 静默忽略坏文件
        return cls(profiles)

    def save_all(self, directory: str) -> None:
        """把所有 Profile 保存到目录"""
        os.makedirs(directory, exist_ok=True)
        for p in self.profiles:
            nm = safe_filename(p.name) if p.name else f"seed_{p.seed}"
            p.save(os.path.join(directory, f"{nm}.json"))

    def launch_all(
        self,
        url: Optional[str] = None,
        stagger_seconds: float = 0.5,
    ) -> List[Any]:
        """
        并发启动所有 profile。

        Args:
            url: 覆盖每个 profile 的 start_url
            stagger_seconds: 每次启动之间的间隔秒数（避免同时写同一个磁盘位置）

        Returns:
            subprocess.Popen 列表（和 profiles 顺序对应）
        """
        import time
        from .launcher import launch_profile
        procs = []
        for i, p in enumerate(self.profiles):
            if i > 0 and stagger_seconds > 0:
                time.sleep(stagger_seconds)
            procs.append(launch_profile(p, override_url=url))
        return procs

    def summary(self) -> str:
        """返回批量信息的简要字符串表示（调试用）"""
        lines = [f"ProfileBatch ({len(self.profiles)} profiles)"]
        for p in self.profiles:
            tag = p.name or f"seed_{p.seed}"
            arch = f" [archetype={p.archetype_id}]" if p.archetype_id else ""
            lines.append(f"  - {tag}: platform={p.platform} seed={p.seed}{arch}")
        return "\n".join(lines)
