from music_pipeline.assets.terms import (
    _chinese_to_pinyin,
    _simplified_to_traditional,
    _traditional_to_simplified,
)

# -------------------------
# OpenCC tests
# -------------------------


def test_to_simplified():
    result = _traditional_to_simplified("繁體中文")
    assert isinstance(result, str)
    assert result == "繁体中文"


def test_to_traditional():
    result = _simplified_to_traditional("简体中文")
    assert isinstance(result, str)
    assert result == "簡體中文"


# -------------------------
# Pinyin tests
# -------------------------


def test_to_pinyin_basic():
    result = _chinese_to_pinyin("中文")
    assert isinstance(result, str)
    assert result.strip() != ""
