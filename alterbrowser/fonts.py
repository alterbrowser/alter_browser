"""
字体生成器 — 混合风格 / 系统真实 / 预制 preset 三模式

FontMode 枚举：
    DEFAULT       不传 --fingerprint-fonts，由 C++ seed-hiding 决定
    CUSTOM        用户手动指定白名单
    MIXED         混合风格 (Windows + macOS + Linux + Google 混合, ~85 字体)
    SYSTEM_REAL   系统实际安装字体作为白名单
"""
from __future__ import annotations

import subprocess
from enum import Enum
from typing import List, Optional

from .utils import derive_rng


class FontMode(str, Enum):
    """字体处理模式"""

    DEFAULT = "default"           # 不传白名单
    CUSTOM = "custom"             # 用户自定义
    MIXED = "mix"                 # 混合风格 (Windows + macOS + Linux + Google)
    SYSTEM_REAL = "system"        # 系统实际安装字体

    @classmethod
    def parse(cls, value) -> "FontMode":
        """接受字符串或 FontMode，返回 FontMode"""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            v = value.lower().strip()
            for m in cls:
                if m.value == v:
                    return m
            raise ValueError(f"invalid FontMode: {value!r}; allowed: {[m.value for m in cls]}")
        raise TypeError(f"FontMode must be str or FontMode, got {type(value)}")


# ============================================================
# 字体池定义
# ============================================================

# 核心 Windows 字体（必留，40 个）
CORE_WINDOWS = [
    "Arial", "Calibri", "Cambria", "Cambria Math", "Candara",
    "Comic Sans MS", "Consolas", "Constantia", "Corbel", "Courier New",
    "Ebrima", "Franklin Gothic", "Gabriola", "Gadugi", "Georgia",
    "Impact", "Javanese Text", "Leelawadee UI", "Lucida Console",
    "Lucida Sans Unicode",
    "Malgun Gothic", "Marlett", "Microsoft Himalaya",
    "Microsoft JhengHei", "Microsoft JhengHei UI", "Microsoft New Tai Lue",
    "Microsoft PhagsPa", "Microsoft Sans Serif", "Microsoft Tai Le",
    "Microsoft YaHei", "Microsoft Yi Baiti", "MingLiU-ExtB",
    "MingLiU_HKSCS-ExtB", "Mongolian Baiti", "MS Gothic", "MS PGothic",
    "MS UI Gothic", "MV Boli", "Myanmar Text", "Nirmala UI",
    "PMingLiU-ExtB", "Palatino Linotype",
    "Segoe MDL2 Assets", "Segoe Print", "Segoe Script",
    "Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol",
    "SimSun", "SimSun-ExtB", "Sitka Small",
    "Sylfaen", "Symbol", "Tahoma", "Times New Roman",
    "Trebuchet MS", "Verdana", "Webdings", "Wingdings",
    "Yu Gothic",
]

# Windows 装饰字体
WINDOWS_DECO = [
    "Arial Black", "Arial Narrow", "Arial Rounded MT Bold",
    "Bahnschrift", "Bahnschrift Condensed", "Bahnschrift Light",
    "Bell MT", "Book Antiqua", "Bookman Old Style", "Bookshelf Symbol 7",
    "Bradley Hand ITC", "Britannic Bold", "Brush Script MT",
    "Calibri Light", "Californian FB", "Calisto MT",
    "Cascadia Code", "Cascadia Mono", "Castellar", "Centaur",
    "Century", "Century Gothic", "Century Schoolbook", "Chiller",
    "Colonna MT", "Cooper Black", "Copperplate Gothic Bold",
    "Copperplate Gothic Light", "Corbel Light", "Curlz MT",
    "Edwardian Script ITC", "Elephant", "Engravers MT",
    "Eras Bold ITC", "Eras Demi ITC", "Eras Light ITC", "Eras Medium ITC",
    "Felix Titling", "Footlight MT Light", "Forte",
    "Franklin Gothic Book", "Franklin Gothic Demi",
    "Freestyle Script", "French Script MT",
    "Garamond", "Gigi", "Gill Sans MT",
    "Gloucester MT Extra Condensed", "Goudy Old Style", "Goudy Stout",
    "Haettenschweiler", "Harlow Solid Italic", "Harrington",
    "High Tower Text", "HoloLens MDL2 Assets",
    "Imprint MT Shadow", "Informal Roman", "Ink Free",
    "Jokerman", "Juice ITC", "Kristen ITC", "Kunstler Script",
    "Lucida Bright", "Lucida Calligraphy", "Lucida Fax",
    "Lucida Handwriting", "Lucida Sans", "Lucida Sans Typewriter",
    "Magneto", "Maiandra GD", "Matura MT Script Capitals",
    "Mistral", "Modern No. 20", "Monotype Corsiva",
    "Niagara Engraved", "Niagara Solid",
    "OCR A Extended", "Old English Text MT", "Onyx",
    "Palace Script MT", "Papyrus", "Parchment",
    "Perpetua", "Perpetua Titling MT", "Playbill",
    "Poor Richard", "Pristina",
    "Rage Italic", "Ravie", "Rockwell", "Rockwell Condensed",
    "Rockwell Extra Bold",
    "Script MT Bold", "Segoe Fluent Icons", "Segoe UI Black",
    "Segoe UI Historic", "Segoe UI Light", "Segoe UI Semibold",
    "Segoe UI Semilight",
    "Showcard Gothic", "Sitka Banner", "Sitka Display",
    "Sitka Heading", "Sitka Subheading", "Sitka Text",
    "Snap ITC", "Stencil",
    "Tempus Sans ITC", "Tw Cen MT", "Tw Cen MT Condensed",
    "Viner Hand ITC", "Vivaldi", "Vladimir Script",
    "Wide Latin", "Wingdings 2", "Wingdings 3",
    "Yu Gothic UI",
]

# 中文花体/装饰
CHINESE_FONTS = [
    "DengXian", "DengXian Light", "FangSong", "KaiTi", "LiSu", "SimHei",
    "STCaiyun", "STFangsong", "STHupo", "STKaiti", "STLiti",
    "STSong", "STXihei", "STXingkai", "STXinwei", "STZhongsong",
    "YouYuan", "Microsoft YaHei Light", "Microsoft YaHei UI",
    "PMingLiU", "MingLiU", "NSimSun", "FZShuTi", "FZYaoTi", "Dubai",
]

# macOS 字体池（Adobe CC / Creative Cloud 附带）
MACOS_FONTS = [
    "Heiti TC", "Heiti SC", "Kaiti SC", "Kaiti TC",
    "Songti SC", "Songti TC", "STIXGeneral", "STHeiti",
    "PingFang SC", "PingFang TC", "PingFang HK",
    "Avenir Next Condensed Medium", "Avenir Next", "Avenir",
    "Apple Braille", "Apple Braille Pinpoint 8 Dot", "Apple Color Emoji",
    "Bodoni 72", "Bodoni 72 Oldstyle", "Bodoni 72 Smallcaps",
    "Chalkboard SE", "Chalkduster",
    "Cochin", "Copperplate", "Didot",
    "Futura", "Geneva", "Helvetica", "Helvetica Neue",
    "Hoefler Text", "Iowan Old Style", "Menlo",
    "Monaco", "Optima", "Skia",
    "Snell Roundhand", "Trattatello", "Zapfino",
    "Devanagari Sangam MN", "Bangla Sangam MN", "Myanmar Sangam MN",
    "Diwan Kufi", "Diwan Thuluth", "Farisi",
    "Hiragino Kaku Gothic Pro", "Hiragino Mincho ProN",
]

# Linux/Noto 字体（开发工具附带）
LINUX_NOTO_FONTS = [
    "Noto Sans", "Noto Serif", "Noto Sans SC", "Noto Sans TC",
    "Noto Sans Armenian", "Noto Sans Hebrew", "Noto Sans Arabic",
    "Noto Sans Mongolian", "Noto Sans New Tai Lue", "Noto Sans Thai",
    "Noto Sans Myanmar", "Noto Sans Ethiopic", "Noto Sans Khmer",
    "Noto Sans Devanagari", "Noto Sans Bengali",
    "DejaVu Sans", "DejaVu Sans Mono", "DejaVu Serif",
    "Liberation Sans", "Liberation Serif", "Liberation Mono",
    "Ubuntu", "Ubuntu Mono",
    "AR PL UMing CN", "AR PL UMing TW", "AR PL UMing TW MBE",
    "AR PL UKai CN", "AR PL UKai TW",
    "Lohit Kannada", "Lohit Tamil", "Lohit Hindi",
    "Navilu", "Gurajada", "Chilanka", "Padauk", "Small Fonts",
]

# Google Web 字体
GOOGLE_WEB_FONTS = [
    "Roboto", "Open Sans", "Lato", "Montserrat", "Oswald", "Raleway",
    "PT Sans", "Merriweather", "Playfair Display",
    "Rubik", "Inter", "Work Sans", "Fira Sans", "Barlow",
    "Mulish", "Quicksand", "Josefin Sans", "Karla", "Cabin",
    "Dosis", "Archivo", "Exo 2", "Prompt", "Titillium Web",
    "Heebo", "Manrope", "DM Sans", "Source Sans Pro", "Yrsa SemiBold",
]


# ============================================================
# FontGenerator
# ============================================================

class FontGenerator:
    """
    字体列表生成器。

    >>> fg = FontGenerator(seed=12345)
    >>> fonts = fg.mixed_style()
    >>> len(fonts)
    110
    """

    def __init__(self, seed: int):
        self.seed = seed
        self.rng = derive_rng(seed, "font_gen")

    # --------------------------------------------
    # 混合风格
    # --------------------------------------------
    def mixed_style(self) -> List[str]:
        """混合风格：核心 + Windows 装饰 + CJK + macOS + Linux + Google 混合，70-120 个。"""
        # 每次调用重建 rng 保证幂等（多次调用结果一致）
        rng = derive_rng(self.seed, "font_gen")
        fonts: List[str] = list(CORE_WINDOWS)

        # 装饰字体 15-30
        n = rng.randint(15, 30)
        fonts.extend(rng.sample(WINDOWS_DECO, min(n, len(WINDOWS_DECO))))

        # 中文字体 3-8
        n = rng.randint(3, 8)
        fonts.extend(rng.sample(CHINESE_FONTS, min(n, len(CHINESE_FONTS))))

        # macOS 字体 8-18
        n = rng.randint(8, 18)
        fonts.extend(rng.sample(MACOS_FONTS, min(n, len(MACOS_FONTS))))

        # Linux/Noto 字体 5-12
        n = rng.randint(5, 12)
        fonts.extend(rng.sample(LINUX_NOTO_FONTS, min(n, len(LINUX_NOTO_FONTS))))

        # Google Web 2-6
        n = rng.randint(2, 6)
        fonts.extend(rng.sample(GOOGLE_WEB_FONTS, min(n, len(GOOGLE_WEB_FONTS))))

        # 1-3 重复（模拟真实环境字体重复现象）
        for _ in range(rng.randint(1, 3)):
            fonts.append(rng.choice(fonts))

        return fonts

    # --------------------------------------------
    # 系统实际安装字体
    # --------------------------------------------
    @staticmethod
    def system_real(include_core: bool = True) -> List[str]:
        """
        读取系统实际安装的字体家族名（仅 Windows 支持）。

        Args:
            include_core: 是否自动追加 CORE_WINDOWS 保证关键字体都在。

        Returns:
            去重排序后的字体名列表。
        """
        ps_cmd = (
            "Add-Type -AssemblyName PresentationCore; "
            "[Windows.Media.Fonts]::SystemFontFamilies | "
            "ForEach-Object { $_.Source } | Sort-Object -Unique"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, encoding="utf-8",
                timeout=10,
            )
            installed = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        except Exception:
            installed = []

        # 只保留 ASCII（避免命令行编码问题）
        ascii_fonts = [f for f in installed if all(ord(c) < 128 for c in f)]

        if include_core:
            merged = sorted(set(ascii_fonts) | set(CORE_WINDOWS))
        else:
            merged = sorted(set(ascii_fonts))
        return merged

    # --------------------------------------------
    # 预制 preset
    # --------------------------------------------
    def preset(self, name: str) -> List[str]:
        """获取预制字体集"""
        if name == "win10_minimal":
            return list(CORE_WINDOWS)
        if name == "win10_home":
            fonts = list(CORE_WINDOWS) + WINDOWS_DECO[:50]
            return sorted(set(fonts))
        if name == "win10_office":
            fonts = list(CORE_WINDOWS) + WINDOWS_DECO + CHINESE_FONTS[:10]
            return sorted(set(fonts))
        if name == "win11_creative":
            fonts = (list(CORE_WINDOWS) + WINDOWS_DECO + CHINESE_FONTS[:8]
                     + MACOS_FONTS[:15] + GOOGLE_WEB_FONTS[:10])
            return sorted(set(fonts))
        raise ValueError(f"unknown preset: {name!r}")

    # --------------------------------------------
    # 根据 FontMode 生成
    # --------------------------------------------
    def generate(self, mode: FontMode, custom: Optional[List[str]] = None) -> Optional[List[str]]:
        """
        根据 FontMode 生成字体列表。返回 None 表示 DEFAULT 模式（不传白名单）。
        """
        if mode == FontMode.DEFAULT:
            return None
        if mode == FontMode.CUSTOM:
            if not custom:
                raise ValueError("FontMode.CUSTOM requires non-empty fonts_custom")
            return list(custom)
        if mode == FontMode.MIXED:
            return self.mixed_style()
        if mode == FontMode.SYSTEM_REAL:
            return self.system_real()
        raise ValueError(f"unsupported FontMode: {mode}")
