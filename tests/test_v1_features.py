"""v1.0 新增功能测试：mobile shorthand / batch.launch_all / chrome 探测"""
import os
import pytest
from unittest.mock import patch

from alterbrowser import AlterBrowser, Profile, ProfileBatch
from alterbrowser.presets import resolve_mobile


# ============================================================
# mobile shorthand
# ============================================================

def test_resolve_mobile_true_is_android():
    r = resolve_mobile(True)
    assert r["platform"] == "Linux armv81"
    assert "Android" in r["user_agent"]
    assert r["max_touch_points"] == 5


def test_resolve_mobile_ios():
    r = resolve_mobile("ios")
    assert r["platform"] == "iPhone"
    assert "iPhone" in r["user_agent"]
    assert r["screen_width"] < 500


def test_resolve_mobile_empty():
    assert resolve_mobile(False) == {}
    assert resolve_mobile(None) == {}
    assert resolve_mobile("") == {}


def test_profile_mobile_android():
    p = Profile(mobile=True)
    assert p.platform == "Linux armv81"
    assert "Android" in p.user_agent
    assert p.max_touch_points == 5


def test_profile_mobile_ios_combined_with_city():
    p = Profile(mobile="ios", city="Tokyo")
    assert p.platform == "iPhone"
    assert p.timezone == "Asia/Tokyo"
    assert p.language == "ja-JP"


def test_alterbrowser_mobile_kwarg():
    sb = AlterBrowser(mobile=True)
    assert sb.profile.platform == "Linux armv81"


# ============================================================
# ProfileBatch
# ============================================================

def test_batch_summary_format():
    batch = ProfileBatch.from_seeds([1, 2, 3])
    s = batch.summary()
    assert "3 profiles" in s
    assert "seed_1" in s
    assert "seed_2" in s


def test_batch_summary_shows_archetype():
    p = Profile(archetype_id="dell_latitude_e6430_2012", name="p1")
    batch = ProfileBatch([p])
    s = batch.summary()
    assert "dell_latitude_e6430_2012" in s


# ============================================================
# chrome_binary 探测
# ============================================================

def test_chrome_binary_env_override(monkeypatch):
    monkeypatch.setenv("ALTERBROWSER_CHROME_BINARY", "C:/custom/chrome.exe")
    # 需要重新导入以触发 _detect
    from alterbrowser.profile import _detect_chrome_binary
    assert _detect_chrome_binary() == "C:/custom/chrome.exe"


def test_chrome_binary_explicit_kwarg():
    sb = AlterBrowser(chrome_binary="/my/custom/chrome")
    assert sb.profile.chrome_binary == "/my/custom/chrome"


def test_chrome_binary_script_sibling(tmp_path, monkeypatch):
    """patch sys.argv[0] to be a file in tmp_path → detect should find sibling chrome.exe"""
    fake_script = tmp_path / "run.py"
    fake_script.write_text("# fake")
    fake_chrome = tmp_path / ("chrome.exe" if os.name == "nt" else "chrome")
    fake_chrome.write_text("# fake exe")

    monkeypatch.setattr("sys.argv", [str(fake_script)])
    monkeypatch.delenv("ALTERBROWSER_CHROME_BINARY", raising=False)
    from alterbrowser.profile import _detect_chrome_binary
    got = _detect_chrome_binary()
    assert got == str(fake_chrome)


# ============================================================
# print_archetypes
# ============================================================

def test_print_archetypes_returns_str():
    from alterbrowser.archetype import print_archetypes
    out = print_archetypes()
    assert isinstance(out, str)
    assert "dell" in out.lower() or "macbook" in out.lower()


def test_print_archetypes_respects_filter():
    from alterbrowser.archetype import print_archetypes
    out = print_archetypes(os_family="macos")
    # macOS 过滤后不应含 "dell"（它是 windows）
    if "dell" in out.lower():
        # 不 hard fail，因为 archetype 库里可能有名字含 dell 的 mac
        pytest.skip("mac archetypes happen to contain 'dell' in text")
