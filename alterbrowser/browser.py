"""
AlterBrowser — 顶层 API 类

封装 Profile + Launcher，提供最简一行用法。

>>> sb = AlterBrowser(seed=12345)
>>> proc = sb.launch("https://example.com")
"""
from __future__ import annotations

import subprocess
from dataclasses import fields
from typing import Any, Dict, List, Optional

from .launcher import launch_profile, kill_all_chrome
from .profile import Profile
from .switches import build_switches


class AlterBrowser:
    """
    顶层 API：一步到位创建 profile 并启动。

    所有 kwargs 都是 :class:`Profile` 的字段。

    Examples
    --------
    >>> sb = AlterBrowser(seed=12345)
    >>> sb.launch("https://example.com")

    >>> sb = AlterBrowser(seed=12345, platform="MacIntel", fonts_mode="mix")
    >>> sb.launch()

    >>> # 从 JSON 加载
    >>> sb = AlterBrowser.load("profile.json")
    """

    def __init__(self, archetype: Optional[str] = None, **kwargs):
        """
        构造 AlterBrowser。

        Args:
            archetype: 可选，支持 archetype id / 短名（"dell" / "macbook"）/
                       "random"（按市场权重随机）。传了就用该 archetype 打底，
                       其他 kwargs 覆盖 archetype 字段。
            **kwargs: 任意 Profile 字段 + shorthand（gpu/cpu/os/resolution/city）。

        Examples:
            >>> AlterBrowser().launch()                             # 100% 默认
            >>> AlterBrowser(city="Shanghai").launch()              # 只改城市
            >>> AlterBrowser(gpu="RTX 5090", cpu="i9-14900K").launch()  # shorthand
            >>> AlterBrowser(archetype="macbook").launch()          # 懒人模式
            >>> AlterBrowser(archetype="random", city="NYC").launch()   # 随机 + 覆盖
        """
        if archetype is not None:
            from .archetype import find_archetype_smart, build_profile_from_archetype, ARCHETYPES
            from .utils import random_seed
            arch_id = find_archetype_smart(archetype)
            if arch_id is None:
                available = sorted(ARCHETYPES.keys())[:5]
                raise ValueError(
                    f"archetype={archetype!r} 匹配不到任何机型。"
                    f"试试 'dell' / 'thinkpad' / 'macbook' / 'surface' / 'random'。"
                    f"完整列表前 5 个: {available}"
                )
            seed = kwargs.pop("seed", None) or random_seed()
            arch_kwargs = build_profile_from_archetype(arch_id, seed=seed)
            arch_kwargs.update(kwargs)  # 用户 kwargs 覆盖 archetype
            kwargs = arch_kwargs

        self.profile = Profile.from_dict(kwargs) if kwargs else Profile()

    # --------------------------------------------
    # 构造方式
    # --------------------------------------------

    @classmethod
    def from_profile(cls, profile: Profile) -> "AlterBrowser":
        obj = cls.__new__(cls)
        obj.profile = profile
        return obj

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlterBrowser":
        return cls.from_profile(Profile.from_dict(data))

    @classmethod
    def load(cls, path: str) -> "AlterBrowser":
        """从 JSON 文件加载"""
        return cls.from_profile(Profile.load(path))

    # --------------------------------------------
    # v0.2 Archetype API
    # --------------------------------------------

    @classmethod
    def from_archetype(
        cls,
        archetype_id: str,
        seed: Optional[int] = None,
        variant_id: Optional[str] = None,
        **user_overrides,
    ) -> "AlterBrowser":
        """
        从 Device Archetype 创建 AlterBrowser (v0.2 推荐用法)。

        Args:
            archetype_id: 从 ``alterbrowser.archetype.ARCHETYPES`` 里选一个
            seed: 派生 variant 选择和细节（None = 随机）
            variant_id: 显式指定 variant（None = 按权重随机选）
            **user_overrides: 覆盖 Profile 任意字段（language / timezone / proxy 等）

        Returns:
            AlterBrowser 实例。fingerprint_mode 默认 REALISTIC（不传 --fingerprint seed）。
        """
        from .archetype import build_profile_from_archetype
        from .utils import random_seed

        if seed is None:
            seed = random_seed()
        data = build_profile_from_archetype(
            archetype_id=archetype_id,
            seed=seed,
            variant_id=variant_id,
            **user_overrides,
        )
        return cls.from_dict(data)

    @classmethod
    def random_archetype(
        cls,
        region: Optional[str] = None,
        form_factor: Optional[str] = None,
        os_family: Optional[str] = None,
        seed: Optional[int] = None,
        variant_id: Optional[str] = None,
        **user_overrides,
    ) -> "AlterBrowser":
        """按条件随机挑一个 archetype 并创建 AlterBrowser"""
        from .archetype import random_archetype as _rand
        from .utils import random_seed

        if seed is None:
            seed = random_seed()
        arch = _rand(seed=seed, region=region, form_factor=form_factor, os_family=os_family)
        return cls.from_archetype(
            arch.id, seed=seed, variant_id=variant_id, **user_overrides
        )

    @classmethod
    def list_archetypes(cls, region: Optional[str] = None,
                        form_factor: Optional[str] = None,
                        os_family: Optional[str] = None):
        """列出符合条件的 archetype（按市场权重降序）"""
        from .archetype import list_archetypes as _list
        return _list(region=region, form_factor=form_factor, os_family=os_family)

    # --------------------------------------------
    # 便捷属性代理
    # --------------------------------------------

    def __getattr__(self, name):
        """把对 AlterBrowser 未知属性的访问转给 Profile"""
        if name.startswith("_"):
            raise AttributeError(name)
        # 用 __dict__ 避免 self.profile 递归触发 __getattr__
        prof = self.__dict__.get("profile")
        if prof is not None and hasattr(prof, name):
            return getattr(prof, name)
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    # --------------------------------------------
    # IP 自适应（避免时区/地理与 IP 不一致被检测）
    # --------------------------------------------

    def adapt_to_ip(
        self,
        *,
        proxy: Optional[str] = None,
        timeout: float = 8.0,
        adjust_timezone: bool = True,
        adjust_geolocation: bool = True,
        adjust_language: bool = True,
        adjust_fonts: bool = True,
    ):
        """
        查询当前出网 IP 地理信息并自动对齐 Profile 时区 / 地理 / 语言 / 区域字体。

        避免指纹检测站通过多维度交叉校验识别出：
        - 时区 vs IP 时区不一致
        - navigator.geolocation vs IP 地理位置不一致
        - Accept-Language vs IP 国家不一致
        - 字体里缺少地区必备字体（如 HK 缺 MingLiU）

        Args:
            proxy: 可选代理（默认用 ``self.profile.proxy``）
            timeout: 单个查询端点超时秒数
            adjust_timezone: 覆写 timezone
            adjust_geolocation: 覆写 geolocation
            adjust_language: 按国家码更新 language + accept_lang
            adjust_fonts: 将区域字体追加到 fonts_custom（仅 CUSTOM/MIX 模式）

        Returns:
            :class:`IPInfo` 或 ``None``（全部端点失败）
        """
        from .ip_adapt import adapt_profile_to_ip
        return adapt_profile_to_ip(
            self.profile,
            proxy=proxy,
            timeout=timeout,
            adjust_timezone=adjust_timezone,
            adjust_geolocation=adjust_geolocation,
            adjust_language=adjust_language,
            adjust_fonts=adjust_fonts,
        )

    # --------------------------------------------
    # 启动 / 控制
    # --------------------------------------------

    def launch(
        self,
        url: Optional[str] = None,
        wait: bool = False,
        timeout: Optional[float] = None,
    ) -> subprocess.Popen:
        """
        启动浏览器。

        Args:
            url: 覆盖 profile.start_url
            wait: 阻塞到进程退出
            timeout: wait=True 时的超时秒数

        Returns:
            subprocess.Popen 实例
        """
        return launch_profile(self.profile, override_url=url, wait=wait, timeout=timeout)

    def build_command(self, url: Optional[str] = None) -> List[str]:
        """只拼命令行，不启动（用于调试）"""
        cmd = build_switches(self.profile)
        if url:
            # 如果 start_url 已存在于末尾，替换它；否则追加
            if self.profile.start_url and cmd and cmd[-1] == self.profile.start_url:
                cmd[-1] = url
            else:
                cmd.append(url)
        return cmd

    # --------------------------------------------
    # 持久化 & 克隆
    # --------------------------------------------

    def save(self, path: str) -> None:
        self.profile.save(path)

    def to_dict(self) -> Dict[str, Any]:
        return self.profile.to_dict()

    def to_json(self, indent: int = 2) -> str:
        return self.profile.to_json(indent=indent)

    def clone(self, **overrides) -> "AlterBrowser":
        return self.from_profile(self.profile.clone(**overrides))

    def diff(self, other) -> Dict[str, Any]:
        if isinstance(other, AlterBrowser):
            return self.profile.diff(other.profile)
        if isinstance(other, Profile):
            return self.profile.diff(other)
        raise TypeError(f"cannot diff with {type(other)}")

    # --------------------------------------------
    # 批量管理快捷方式
    # --------------------------------------------

    @staticmethod
    def kill_all() -> int:
        """杀掉所有 chrome 进程"""
        return kill_all_chrome()

    def __repr__(self):
        return f"AlterBrowser(seed={self.profile.seed}, name={self.profile.name!r})"
