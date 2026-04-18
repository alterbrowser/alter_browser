"""AlterBrowser(archetype=...) 模糊匹配 kwarg 测试"""
import pytest
from alterbrowser import AlterBrowser
from alterbrowser.archetype import find_archetype_smart, ARCHETYPES


# ============================================================
# find_archetype_smart
# ============================================================

def test_find_archetype_exact():
    assert find_archetype_smart("macbook_air_m2_2022") == "macbook_air_m2_2022"


def test_find_archetype_short_name():
    assert find_archetype_smart("macbook") is not None
    assert "macbook" in find_archetype_smart("macbook")


def test_find_archetype_space_normalized():
    """带空格也能匹配"""
    assert "macbook_air" in find_archetype_smart("macbook air")


def test_find_archetype_dell():
    result = find_archetype_smart("dell")
    assert result is not None and "dell" in result


def test_find_archetype_random_returns_valid_id():
    got = find_archetype_smart("random", seed=1)
    assert got in ARCHETYPES


def test_find_archetype_random_different_seeds():
    """不同 seed 的 random 大概率不同（允许偶然相同）"""
    ids = {find_archetype_smart("random", seed=s) for s in range(1, 20)}
    assert len(ids) >= 2


def test_find_archetype_unknown():
    assert find_archetype_smart("xyz_nonexistent_brand") is None


def test_find_archetype_empty():
    assert find_archetype_smart("") is None
    assert find_archetype_smart(None) is None


# ============================================================
# AlterBrowser(archetype=...) integration
# ============================================================

def test_browser_archetype_short_name():
    sb = AlterBrowser(archetype="macbook")
    assert sb.profile.archetype_id and "macbook" in sb.profile.archetype_id
    assert sb.profile.platform == "MacIntel"


def test_browser_archetype_random():
    sb = AlterBrowser(archetype="random")
    assert sb.profile.archetype_id in ARCHETYPES


def test_browser_archetype_unknown_raises():
    with pytest.raises(ValueError, match="匹配不到"):
        AlterBrowser(archetype="xyz123")


def test_user_kwargs_override_archetype():
    """显式 kwargs 覆盖 archetype 派生的字段"""
    sb = AlterBrowser(archetype="macbook", platform="Win32", language="zh-CN")
    assert sb.profile.platform == "Win32"
    assert sb.profile.language == "zh-CN"


def test_archetype_with_shorthand_city():
    """archetype 和 shorthand city 可叠加使用"""
    sb = AlterBrowser(archetype="dell", city="Tokyo")
    assert "dell" in sb.profile.archetype_id
    assert sb.profile.timezone == "Asia/Tokyo"
    assert sb.profile.language == "ja-JP"


def test_browser_no_archetype_still_works():
    """不传 archetype 也应正常工作"""
    sb = AlterBrowser(gpu="RTX 5090")
    assert sb.profile.archetype_id is None
    assert "RTX 5090" in sb.profile.gpu_renderer
