"""FontGenerator 单元测试"""
import pytest

from alterbrowser.fonts import FontMode, FontGenerator, CORE_WINDOWS


def test_font_mode_parse():
    assert FontMode.parse("default") == FontMode.DEFAULT
    assert FontMode.parse("custom") == FontMode.CUSTOM
    assert FontMode.parse("mix") == FontMode.MIXED
    assert FontMode.parse("system") == FontMode.SYSTEM_REAL
    assert FontMode.parse(FontMode.DEFAULT) == FontMode.DEFAULT


def test_font_mode_invalid():
    with pytest.raises(ValueError):
        FontMode.parse("nonsense")


def test_mixed_style_deterministic():
    """同 seed 生成完全相同的字体列表"""
    fg1 = FontGenerator(seed=12345)
    fg2 = FontGenerator(seed=12345)
    assert fg1.mixed_style() == fg2.mixed_style()


def test_mixed_style_different_seeds():
    fg1 = FontGenerator(seed=100)
    fg2 = FontGenerator(seed=200)
    assert fg1.mixed_style() != fg2.mixed_style()


def test_mixed_style_contains_core():
    """核心 Windows 字体必须都在"""
    fg = FontGenerator(seed=42)
    fonts = fg.mixed_style()
    for core in CORE_WINDOWS:
        assert core in fonts, f"missing core font: {core}"


def test_mixed_style_size():
    """混合风格字体数量在合理范围"""
    fg = FontGenerator(seed=42)
    fonts = fg.mixed_style()
    assert 60 <= len(fonts) <= 140


def test_preset_win10_minimal():
    fg = FontGenerator(seed=1)
    fonts = fg.preset("win10_minimal")
    assert len(fonts) == len(CORE_WINDOWS)
    for f in CORE_WINDOWS:
        assert f in fonts


def test_preset_unknown():
    fg = FontGenerator(seed=1)
    with pytest.raises(ValueError):
        fg.preset("nonexistent_preset")


def test_generate_dispatches():
    fg = FontGenerator(seed=1)
    assert fg.generate(FontMode.DEFAULT) is None
    custom = fg.generate(FontMode.CUSTOM, custom=["Arial"])
    assert custom == ["Arial"]
    mix = fg.generate(FontMode.MIXED)
    assert isinstance(mix, list)
    assert len(mix) > 50


def test_custom_requires_list():
    fg = FontGenerator(seed=1)
    with pytest.raises(ValueError):
        fg.generate(FontMode.CUSTOM, custom=None)
