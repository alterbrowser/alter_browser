"""
IP Adaptation Module
====================

查询当前外网 IP 的地理位置，自动对齐 Profile 的 timezone/geolocation 字段，
避免指纹检测站的 "Timezone spoofed" / "Location mismatch" 误判。

典型用法::

    sb = AlterBrowser.from_archetype('dell_latitude_e6430_2012', seed=12345)
    sb.adapt_to_ip()           # 按当前出网 IP 自动设置 timezone/geo
    sb.launch('https://example.com')

若 Profile.proxy 有值，则通过该代理查询（保证查出来的 IP 和浏览器实际出网 IP 一致）。
离线或查询失败时返回 None，调用方应保留 Profile 原值。
"""
from __future__ import annotations

import json
import logging
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .modes import SourceMode

_log = logging.getLogger(__name__)


# ============================================================
# Country → Language / 字体 区域映射
# ============================================================

# country_code → (primary_lang_tag, accept_lang_string)
# 选择策略：用 Chrome 在该地区默认的 Accept-Language 习惯写法
_COUNTRY_LANG: dict = {
    # 华语
    "CN": ("zh-CN", "zh-CN,zh;q=0.9,en;q=0.8"),
    "HK": ("zh-HK", "zh-HK,zh-Hant;q=0.9,zh;q=0.8,en;q=0.7"),
    "TW": ("zh-TW", "zh-TW,zh-Hant;q=0.9,zh;q=0.8,en;q=0.7"),
    "MO": ("zh-HK", "zh-HK,zh-Hant;q=0.9,zh;q=0.8,en;q=0.7"),
    "SG": ("en-SG", "en-SG,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"),
    # 英语圈
    "US": ("en-US", "en-US,en;q=0.9"),
    "CA": ("en-CA", "en-CA,en;q=0.9,fr-CA;q=0.8"),
    "GB": ("en-GB", "en-GB,en;q=0.9"),
    "AU": ("en-AU", "en-AU,en;q=0.9"),
    "NZ": ("en-NZ", "en-NZ,en;q=0.9"),
    "IE": ("en-IE", "en-IE,en;q=0.9"),
    "IN": ("en-IN", "en-IN,en;q=0.9,hi;q=0.8"),
    # 日韩
    "JP": ("ja-JP", "ja,en-US;q=0.9,en;q=0.8"),
    "KR": ("ko-KR", "ko,en-US;q=0.9,en;q=0.8"),
    # 欧洲
    "DE": ("de-DE", "de-DE,de;q=0.9,en;q=0.8"),
    "AT": ("de-AT", "de-AT,de;q=0.9,en;q=0.8"),
    "FR": ("fr-FR", "fr-FR,fr;q=0.9,en;q=0.8"),
    "BE": ("fr-BE", "fr-BE,fr;q=0.9,nl-BE;q=0.8,en;q=0.7"),
    "CH": ("de-CH", "de-CH,de;q=0.9,en;q=0.8,fr;q=0.7"),
    "ES": ("es-ES", "es-ES,es;q=0.9,en;q=0.8"),
    "IT": ("it-IT", "it-IT,it;q=0.9,en;q=0.8"),
    "PT": ("pt-PT", "pt-PT,pt;q=0.9,en;q=0.8"),
    "NL": ("nl-NL", "nl-NL,nl;q=0.9,en;q=0.8"),
    "SE": ("sv-SE", "sv-SE,sv;q=0.9,en;q=0.8"),
    "NO": ("nb-NO", "nb-NO,nb;q=0.9,en;q=0.8"),
    "DK": ("da-DK", "da-DK,da;q=0.9,en;q=0.8"),
    "FI": ("fi-FI", "fi-FI,fi;q=0.9,en;q=0.8"),
    "PL": ("pl-PL", "pl-PL,pl;q=0.9,en;q=0.8"),
    "CZ": ("cs-CZ", "cs-CZ,cs;q=0.9,en;q=0.8"),
    "RU": ("ru-RU", "ru-RU,ru;q=0.9,en;q=0.8"),
    "UA": ("uk-UA", "uk-UA,uk;q=0.9,ru;q=0.8,en;q=0.7"),
    "TR": ("tr-TR", "tr-TR,tr;q=0.9,en;q=0.8"),
    # 中东
    "AE": ("ar-AE", "ar-AE,ar;q=0.9,en;q=0.8"),
    "SA": ("ar-SA", "ar-SA,ar;q=0.9,en;q=0.8"),
    "IL": ("he-IL", "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"),
    # 拉美
    "BR": ("pt-BR", "pt-BR,pt;q=0.9,en;q=0.8"),
    "MX": ("es-MX", "es-MX,es;q=0.9,en;q=0.8"),
    "AR": ("es-AR", "es-AR,es;q=0.9,en;q=0.8"),
    "CL": ("es-CL", "es-CL,es;q=0.9,en;q=0.8"),
    # 东南亚
    "TH": ("th-TH", "th-TH,th;q=0.9,en;q=0.8"),
    "VN": ("vi-VN", "vi-VN,vi;q=0.9,en;q=0.8"),
    "ID": ("id-ID", "id-ID,id;q=0.9,en;q=0.8"),
    "MY": ("ms-MY", "ms-MY,ms;q=0.9,en;q=0.8"),
    "PH": ("en-PH", "en-PH,en;q=0.9,fil;q=0.8"),
}

# 区域额外字体补丁：在 fonts_custom 基础上追加（仅 FontMode.CUSTOM 生效）
# 这里列出的字体必须是 Windows 上常见的（避免找不到）
_REGION_EXTRA_FONTS: dict = {
    "CN":  ["SimSun", "SimHei", "Microsoft YaHei", "Microsoft YaHei UI",
            "NSimSun", "KaiTi", "FangSong", "DengXian"],
    "HK":  ["PMingLiU", "PMingLiU-ExtB", "MingLiU", "MingLiU-ExtB",
            "MingLiU_HKSCS-ExtB", "Microsoft JhengHei", "Microsoft JhengHei UI",
            "DFKai-SB"],
    "TW":  ["PMingLiU", "PMingLiU-ExtB", "MingLiU", "MingLiU-ExtB",
            "Microsoft JhengHei", "Microsoft JhengHei UI", "DFKai-SB"],
    "MO":  ["PMingLiU", "PMingLiU-ExtB", "MingLiU", "MingLiU_HKSCS-ExtB",
            "Microsoft JhengHei"],
    "JP":  ["MS Gothic", "MS PGothic", "MS UI Gothic", "MS Mincho",
            "MS PMincho", "Meiryo", "Meiryo UI", "Yu Gothic", "Yu Gothic UI",
            "Yu Mincho"],
    "KR":  ["Malgun Gothic", "Gulim", "GulimChe", "Dotum", "DotumChe",
            "Batang", "BatangChe", "Gungsuh", "GungsuhChe"],
    "TH":  ["Leelawadee UI", "Leelawadee", "Angsana New", "AngsanaUPC",
            "Cordia New", "CordiaUPC", "Tahoma"],
    "AE":  ["Tahoma", "Arial", "Traditional Arabic", "Simplified Arabic",
            "Arabic Typesetting", "Sakkal Majalla"],
    "SA":  ["Tahoma", "Arial", "Traditional Arabic", "Simplified Arabic",
            "Arabic Typesetting", "Sakkal Majalla"],
    "IL":  ["Arial", "Tahoma", "David", "FrankRuehl", "Narkisim", "Miriam"],
}


def language_for_country(country_code: str) -> Optional[tuple]:
    """根据 ISO 国家码返回 (primary_lang, accept_lang) 或 None（未知国家用 en-US 兜底）。"""
    if not country_code:
        return None
    return _COUNTRY_LANG.get(country_code.upper())


def extra_fonts_for_country(country_code: str) -> list:
    """根据 ISO 国家码返回应追加的区域字体列表（可能为空）。"""
    if not country_code:
        return []
    return list(_REGION_EXTRA_FONTS.get(country_code.upper(), []))


@dataclass
class IPInfo:
    """外网 IP 查询结果。"""
    ip: str
    country_code: str          # ISO 3166-1 alpha-2，如 "US", "HK", "CN"
    country_name: str
    city: str
    region: str
    timezone: str              # IANA 时区名，如 "America/New_York"
    latitude: float
    longitude: float
    raw: dict = None           # 原始 JSON，便于调试


# 多端点兜底：单个查不通就用下一个
# 字段映射不同，parse 函数按 endpoint 分别处理
_ENDPOINTS = [
    ("https://ipapi.co/json/",        "ipapi"),
    ("https://ipwho.is/",              "ipwho"),
    ("http://ip-api.com/json/",        "ip_api"),
]


def _build_opener(proxy: Optional[str]):
    """构造带可选 proxy 的 urllib opener。proxy 格式 'http://host:port' 或 'socks5://...'（socks 需 PySocks）。"""
    if proxy:
        if proxy.lower().startswith("socks"):
            _log.warning(
                "detect_ip: socks proxy (%s) requires PySocks (pip install pysocks). "
                "urllib ProxyHandler may not work. Consider using http proxy instead.",
                proxy,
            )
        proxy_handler = urllib.request.ProxyHandler({
            "http":  proxy,
            "https": proxy,
        })
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def _parse_ipapi(j: dict) -> IPInfo:
    return IPInfo(
        ip=j.get("ip", ""),
        country_code=j.get("country_code", "") or j.get("country", ""),
        country_name=j.get("country_name", ""),
        city=j.get("city", ""),
        region=j.get("region", ""),
        timezone=j.get("timezone", ""),
        latitude=float(j.get("latitude") or 0.0),
        longitude=float(j.get("longitude") or 0.0),
        raw=j,
    )


def _parse_ipwho(j: dict) -> IPInfo:
    if not j.get("success", True):
        raise RuntimeError(j.get("message", "ipwho.is failed"))
    tz = (j.get("timezone") or {}).get("id", "")
    return IPInfo(
        ip=j.get("ip", ""),
        country_code=j.get("country_code", ""),
        country_name=j.get("country", ""),
        city=j.get("city", ""),
        region=j.get("region", ""),
        timezone=tz,
        latitude=float(j.get("latitude") or 0.0),
        longitude=float(j.get("longitude") or 0.0),
        raw=j,
    )


def _parse_ip_api(j: dict) -> IPInfo:
    if j.get("status") != "success":
        raise RuntimeError(j.get("message", "ip-api.com failed"))
    return IPInfo(
        ip=j.get("query", ""),
        country_code=j.get("countryCode", ""),
        country_name=j.get("country", ""),
        city=j.get("city", ""),
        region=j.get("regionName", ""),
        timezone=j.get("timezone", ""),
        latitude=float(j.get("lat") or 0.0),
        longitude=float(j.get("lon") or 0.0),
        raw=j,
    )


_PARSERS = {
    "ipapi":  _parse_ipapi,
    "ipwho":  _parse_ipwho,
    "ip_api": _parse_ip_api,
}


def detect_ip(proxy: Optional[str] = None, timeout: float = 8.0) -> Optional[IPInfo]:
    """
    查询当前出网 IP 的地理信息。多端点兜底。

    Args:
        proxy: 可选代理 URL（与 Chrome 的 --proxy-server 同格式）
        timeout: 单个端点超时秒数

    Returns:
        ``IPInfo`` 或 ``None``（全部端点失败时）
    """
    opener = _build_opener(proxy)
    headers = {"User-Agent": "alterbrowser-ipadapt/0.2"}

    for url, parser_key in _ENDPOINTS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, timeout=timeout) as resp:
                body = resp.read()
            j = json.loads(body)
            info = _PARSERS[parser_key](j)
            if info.timezone:          # 成功标志：至少拿到 timezone
                _log.info("detect_ip OK via %s: %s %s/%s",
                          url, info.ip, info.country_code, info.timezone)
                return info
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, RuntimeError, ValueError,
                socket.timeout, TimeoutError, OSError) as e:
            _log.warning("detect_ip %s failed: %s", url, e)
            continue

    _log.error("detect_ip: all endpoints failed")
    return None


# ============================================================
# Profile 应用
# ============================================================

def apply_to_profile(profile, ip_info: IPInfo,
                     *,
                     adjust_timezone: bool = True,
                     adjust_geolocation: bool = True,
                     adjust_language: bool = True,
                     adjust_fonts: bool = True,
                     geolocation_accuracy_m: float = 100.0) -> dict:
    """
    将 IP 地理信息应用到 Profile 的各个维度。

    Args:
        profile: :class:`alterbrowser.profile.Profile`
        ip_info: :class:`IPInfo`
        adjust_timezone: 覆写 timezone + timezone_mode=CUSTOM
        adjust_geolocation: 覆写 geolocation + geolocation_mode=CUSTOM
        adjust_language: 按国家码选择合适的 language / accept_lang
        adjust_fonts: 将区域字体补丁追加到 ``fonts_custom``（仅当用户选 CUSTOM 或 MIX 模式）
        geolocation_accuracy_m: 覆写坐标时使用的精度（米）

    Returns:
        应用报告 dict：``{'timezone': bool, 'geolocation': bool,
        'language': bool, 'fonts_added': int}``
    """
    from .fonts import FontMode

    applied = {
        "timezone": False,
        "geolocation": False,
        "language": False,
        "fonts_added": 0,
    }

    if adjust_timezone and ip_info.timezone:
        profile.timezone = ip_info.timezone
        profile.timezone_mode = SourceMode.CUSTOM
        applied["timezone"] = True

    if adjust_geolocation and (ip_info.latitude is not None and ip_info.longitude is not None
                                and (ip_info.latitude != 0.0 or ip_info.longitude != 0.0)):
        profile.geolocation = (
            float(ip_info.latitude),
            float(ip_info.longitude),
            float(geolocation_accuracy_m),
        )
        profile.geolocation_mode = SourceMode.CUSTOM
        applied["geolocation"] = True

    if adjust_language and ip_info.country_code:
        mapping = language_for_country(ip_info.country_code)
        if mapping is not None:
            primary, accept = mapping
        else:
            # 未知国家 → 保底用 en-US（国际默认）
            primary, accept = "en-US", "en-US,en;q=0.9"
        profile.language = primary
        profile.accept_lang = accept
        applied["language"] = True

    if adjust_fonts and ip_info.country_code:
        extras = extra_fonts_for_country(ip_info.country_code)
        if extras:
            # 只在 CUSTOM 或 MIX 模式下追加；DEFAULT/SYSTEM 模式跳过避免意外
            if profile.fonts_mode in (FontMode.CUSTOM, FontMode.MIXED):
                existing = set(profile.fonts_custom or [])
                to_add = [f for f in extras if f not in existing]
                if to_add:
                    profile.fonts_custom = list(profile.fonts_custom or []) + to_add
                    applied["fonts_added"] = len(to_add)
            else:
                _log.debug(
                    "skip fonts extras for country=%s: fonts_mode=%s (need CUSTOM/MIX)",
                    ip_info.country_code, profile.fonts_mode,
                )

    return applied


def adapt_profile_to_ip(profile,
                        *,
                        proxy: Optional[str] = None,
                        timeout: float = 8.0,
                        adjust_timezone: bool = True,
                        adjust_geolocation: bool = True,
                        adjust_language: bool = True,
                        adjust_fonts: bool = True) -> Optional[IPInfo]:
    """
    一步到位：查询 IP → 应用到 Profile → 返回查询结果（或 None）。

    若 proxy 未显式传入，则使用 ``profile.proxy``。
    应用报告存于 ``profile._ip_adapt_applied``（仅内存，不序列化）。
    """
    effective_proxy = proxy if proxy is not None else profile.proxy
    info = detect_ip(proxy=effective_proxy, timeout=timeout)
    if info is None:
        return None
    report = apply_to_profile(
        profile, info,
        adjust_timezone=adjust_timezone,
        adjust_geolocation=adjust_geolocation,
        adjust_language=adjust_language,
        adjust_fonts=adjust_fonts,
    )
    # 透传应用报告（不存入 to_dict）
    try:
        profile._ip_adapt_applied = report
        profile._ip_adapt_info = info
    except Exception:
        pass
    return info
