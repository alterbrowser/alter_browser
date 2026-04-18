"""
alterbrowser — 指纹浏览器启动 & profile 管理库
===============================================

用法速查
-------

>>> from alterbrowser import AlterBrowser
>>> sb = AlterBrowser(seed=12345)
>>> sb.launch("https://example.com")

>>> # 完整配置
>>> sb = AlterBrowser(
...     seed=12345,
...     platform="Win32",
...     hardware_concurrency=8,
...     gpu_vendor="Google Inc. (NVIDIA)",
...     fonts_mode="mix",
... )

>>> # 持久化
>>> sb.save("profile_001.json")
>>> sb2 = AlterBrowser.load("profile_001.json")

公开 API
-------
- ``AlterBrowser``      主类
- ``Profile``           dataclass
- ``FontMode``          字体模式枚举
- ``FontGenerator``     字体生成器
- ``ProfileBatch``      批量管理
"""

from .browser import AlterBrowser
from .profile import Profile, ProfileBatch
from .fonts import FontMode, FontGenerator
from .modes import FingerprintMode, SourceMode, WebRTCMode, TriState
from .errors import (
    AlterBrowserError,
    BinaryNotFoundError,
    ProfileLoadError,
    ProfileValidationError,
    LaunchTimeoutError,
    IPAdaptError,
    InconsistencyWarning,
)

__version__ = "0.3.0"
__all__ = [
    "AlterBrowser",
    "Profile",
    "ProfileBatch",
    "FontMode",
    "FontGenerator",
    # v0.2 新增
    "FingerprintMode",
    "SourceMode",
    "WebRTCMode",
    "TriState",
    # 异常
    "AlterBrowserError",
    "BinaryNotFoundError",
    "ProfileLoadError",
    "ProfileValidationError",
    "LaunchTimeoutError",
    "IPAdaptError",
    "InconsistencyWarning",
]
