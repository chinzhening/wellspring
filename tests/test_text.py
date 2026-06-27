from core import text


def test_clean_lyrics_basic():
    assert text.clean_lyrics("hello world") == "hello world"


def test_clean_lyrics_html_entities():
    assert text.clean_lyrics("A&nbsp;&nbsp;B") == "A B"
    assert text.clean_lyrics("A&nbsp;B") == "A B"


def test_clean_lyrics_nbsp_char():
    assert text.clean_lyrics("A\u00a0B") == "A B"
    assert text.clean_lyrics("A\u00a0\u00a0B") == "A B"


def test_clean_lyrics_control_chars():
    assert text.clean_lyrics("A\u0000B\u0001C") == "ABC"


def test_clean_lyrics_line_breaks():
    input_text = "line1\n\n\nline2\n\n\n\nline3"
    expected = "line1\nline2\nline3"
    assert text.clean_lyrics(input_text) == expected


def test_clean_lyrics_chinese_english_spacing():
    result = text.clean_lyrics("你好A世界B")
    assert result == "你好 A 世界 B"


def test_clean_lyrics_tmixed_real_case():
    input_text = "祢在高處&nbsp;大有能力\u00a0萬物甦醒A來敬拜B"
    result = text.clean_lyrics(input_text)

    assert "祢在高處" in result
    assert "大有能力" in result
    assert "A 來" in result or "A 來" in result.replace(
        " ", " "
    )  # tolerant check


def test_clean_lyrics_real_lyrics_block():
    input_text = """
夜星在天上閃閃爍

月娘光光照溪邊

大樹下  風微微

聽到樹蟬在吟詩

上帝賞賜的平安冥

耶和華是我的安慰

倚靠祂攏免驚什麼

雖遇到風颱天

祂給我心有平靜

將平安放在我的內心

我過死蔭山谷  也無驚災害

祂會與我佇地  用話來安慰我

有恩典和慈愛同我相作伴

有平安隨我一世人
"""

    result = text.clean_lyrics(input_text)

    # 1a. preserves structure (no collapse into single line)
    assert "\n" in result

    # 1b. removes double newlines
    assert "\n\n" not in result

    # 2. does NOT explode into empty string
    assert len(result) > 0

    # 3. key lyrics still exist
    assert "夜星在天上閃閃爍" in result
    assert "耶和華是我的安慰" in result
    assert "有平安隨我一世人" in result

    # 4. no excessive whitespace explosion
    assert "  " not in result.replace("\n", "")


def test_clean_text():
    assert text.clean_text("  Hello   World  ") == "Hello World"
    assert text.clean_text("Line1\nLine2\n\nLine3") == "Line1 Line2 Line3"
    assert text.clean_text("A\u0000B\u0001C") == "ABC"
