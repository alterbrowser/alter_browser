"""
模式枚举 — 所有字段的"模式切换"定义。

设计原则:
- 每个枚举值都是字符串（继承 str），方便 JSON 序列化
- 每个类都有 ``parse()`` 类方法，既接受字符串也接受枚举实例
"""
from __future__ import annotations

from enum import Enum


class FingerprintMode(str, Enum):
    """指纹策略（决定是否传 --fingerprint seed）"""

    REALISTIC = "realistic"      # 默认: 不传 seed，Canvas/Audio 真实硬件 hash
    UNIQUE = "unique"            # 传 seed: 每 profile 独特 hash (可能 Masking)
    CACHED = "cached"            # v0.4 规划: 首启采集真实 hash 持久化

    @classmethod
    def parse(cls, value) -> "FingerprintMode":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            v = value.lower().strip()
            for m in cls:
                if m.value == v:
                    return m
            raise ValueError(f"invalid FingerprintMode: {value!r}")
        raise TypeError(f"FingerprintMode must be str or FingerprintMode, got {type(value)}")


class SourceMode(str, Enum):
    """通用"模式切换" —— 时区/地理位置/WebGL元数据/WebGPU/CPU/RAM 等字段共用"""

    REAL = "real"                # 用真实本机值
    CUSTOM = "custom"            # 用户自定义
    BY_IP = "by_ip"              # 根据代理 IP 推导
    DISABLED = "disabled"        # 禁用 / 不报告

    @classmethod
    def parse(cls, value) -> "SourceMode":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            v = value.lower().strip().replace("-", "_")
            for m in cls:
                if m.value == v:
                    return m
            # 别名
            if v in ("ip", "byip"):
                return cls.BY_IP
            if v in ("off", "none"):
                return cls.DISABLED
            raise ValueError(f"invalid SourceMode: {value!r}")
        raise TypeError(f"SourceMode must be str or SourceMode, got {type(value)}")


class WebRTCMode(str, Enum):
    """WebRTC IP 处理策略"""

    REAL = "real"                   # 真实 IP（默认不改）
    FORWARD = "forward"             # 正常转发（走代理）
    REPLACE = "replace"             # 替换为假 IP（需 webrtc_public_ip）
    DISABLED = "disabled"           # 完全禁用 WebRTC
    DISABLED_UDP = "disabled_udp"   # 只禁用非代理 UDP

    @classmethod
    def parse(cls, value) -> "WebRTCMode":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            v = value.lower().strip().replace("-", "_")
            for m in cls:
                if m.value == v:
                    return m
            raise ValueError(f"invalid WebRTCMode: {value!r}")
        raise TypeError(f"WebRTCMode must be str or WebRTCMode, got {type(value)}")


class TriState(str, Enum):
    """三态开关 — 默认/开启/关闭。用于 Do Not Track / 硬件加速 等。"""

    DEFAULT = "default"
    ON = "on"
    OFF = "off"

    @classmethod
    def parse(cls, value) -> "TriState":
        if isinstance(value, cls):
            return value
        if isinstance(value, bool):
            return cls.ON if value else cls.OFF
        if value is None:
            return cls.DEFAULT
        if isinstance(value, str):
            v = value.lower().strip()
            mapping = {
                "default": cls.DEFAULT, "auto": cls.DEFAULT, "none": cls.DEFAULT,
                "on": cls.ON, "true": cls.ON, "1": cls.ON, "enable": cls.ON,
                "off": cls.OFF, "false": cls.OFF, "0": cls.OFF, "disable": cls.OFF,
            }
            if v in mapping:
                return mapping[v]
            raise ValueError(f"invalid TriState: {value!r}")
        raise TypeError(f"TriState must be bool/str/None/TriState, got {type(value)}")
