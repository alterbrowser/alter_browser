"""Profile 单元测试"""
import json
import os
import tempfile

import pytest

from alterbrowser.fonts import FontMode
from alterbrowser.profile import Profile, ProfileBatch
from alterbrowser.errors import ProfileValidationError, ProfileLoadError


def test_default_profile():
    p = Profile()
    # v0.3.1+: seed 默认不传时自动生成 (时间戳 + 熵)，为正整数
    assert isinstance(p.seed, int) and p.seed > 0
    assert p.brand == "Chrome"
    assert p.platform == "Win32"
    assert p.fonts_mode == FontMode.DEFAULT


def test_auto_seed_is_unique():
    """连续调用 Profile() 应该得到不同 seed"""
    seeds = {Profile().seed for _ in range(50)}
    assert len(seeds) >= 45  # 允许极少量碰撞


def test_explicit_seed_honored():
    """显式传 seed 不应被自动生成覆盖"""
    assert Profile(seed=42).seed == 42
    assert Profile(seed=0).seed == 0   # 0 是合法的显式值


def test_profile_with_seed():
    p = Profile(seed=12345)
    assert p.seed == 12345


def test_font_mode_string_parse():
    p = Profile(seed=1, fonts_mode="mix")
    assert p.fonts_mode == FontMode.MIXED

    p = Profile(seed=1, fonts_mode=FontMode.CUSTOM)
    assert p.fonts_mode == FontMode.CUSTOM


def test_invalid_seed():
    with pytest.raises(ProfileValidationError):
        Profile(seed=-1)


def test_invalid_battery():
    with pytest.raises(ProfileValidationError):
        Profile(seed=1, battery_level=1.5)


def test_invalid_geolocation():
    with pytest.raises(ProfileValidationError):
        Profile(seed=1, geolocation=(100, 200))   # 超 WGS84 范围

    with pytest.raises(ProfileValidationError):
        Profile(seed=1, geolocation=(1,))   # 长度不对


def test_invalid_screen():
    with pytest.raises(ProfileValidationError):
        Profile(seed=1, screen_width=100)

    with pytest.raises(ProfileValidationError):
        Profile(seed=1, screen_height=20000)


def test_to_dict_and_from_dict():
    p1 = Profile(seed=42, platform="MacIntel", hardware_concurrency=12)
    d = p1.to_dict()
    assert d["seed"] == 42
    assert d["platform"] == "MacIntel"
    assert d["fonts_mode"] == "default"  # enum 序列化为 str

    p2 = Profile.from_dict(d)
    assert p2.seed == 42
    assert p2.platform == "MacIntel"
    assert p2.hardware_concurrency == 12


def test_save_and_load_roundtrip():
    p1 = Profile(seed=999, platform="Linux x86_64", name="test_profile", fonts_mode="mix")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        tmp_path = f.name
    try:
        p1.save(tmp_path)
        p2 = Profile.load(tmp_path)
        assert p2.seed == 999
        assert p2.platform == "Linux x86_64"
        assert p2.name == "test_profile"
        assert p2.fonts_mode == FontMode.MIXED
    finally:
        os.unlink(tmp_path)


def test_load_missing_file():
    with pytest.raises(ProfileLoadError):
        Profile.load("D:/nonexistent/path/file.json")


def test_clone():
    p1 = Profile(seed=100, platform="Win32")
    p2 = p1.clone(seed=200, platform="MacIntel")
    assert p1.seed == 100
    assert p1.platform == "Win32"
    assert p2.seed == 200
    assert p2.platform == "MacIntel"


def test_diff():
    p1 = Profile(seed=100, platform="Win32")
    p2 = Profile(seed=200, platform="Win32", hardware_concurrency=8)
    d = p1.diff(p2)
    assert "seed" in d
    assert d["seed"] == (100, 200)
    assert "platform" not in d   # 相同


def test_batch_from_seeds():
    batch = ProfileBatch.from_seeds([100, 200, 300])
    assert len(batch) == 3
    assert batch[0].seed == 100
    assert batch[2].seed == 300
    assert batch[1].name == "seed_200"


def test_batch_iteration():
    batch = ProfileBatch.from_seeds([1, 2, 3])
    seeds = [p.seed for p in batch]
    assert seeds == [1, 2, 3]


def test_auto_user_data_dir():
    p = Profile(seed=12345, name="abc")
    path = p.auto_user_data_dir()
    assert "abc" in path

    p2 = Profile(seed=12345)
    path2 = p2.auto_user_data_dir()
    assert "12345" in path2
