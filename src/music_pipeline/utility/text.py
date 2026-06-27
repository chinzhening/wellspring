import html
import unicodedata

import regex as re


def sanitize_html(text: str) -> str:
    """Sanitizes HTML content by unescaping entities, normalizing Unicode, and
    removing all HTML tags while preserving the text content.
    """
    if not isinstance(text, str):
        return ""

    # Unescape HTML entities
    text = html.unescape(text)

    # Normalize Unicode characters to NFKC form
    text = unicodedata.normalize("NFKC", text)

    # Remove all HTML tags using regex
    text = re.sub(r"<[^>]+>", "", text)

    return text.strip()


def clean_lyrics(text: str) -> str:
    """Cleans the lyrics text by unescaping HTML, normalizing Unicode,
    removing control characters (except newlines and spaces), collapsing
    horizontal whitespace, fixing spacing between CJK and Latin characters, and
    normalizing multiple newlines.
    """
    if not isinstance(text, str):
        return ""

    # Replace <br> tags with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)

    text = (
        text.replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
    )
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")

    # Remove control chars BUT KEEP \n and space
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Collapse ONLY horizontal whitespace (not spaces between characters blindly)
    text = re.sub(r"[ \t]+", " ", text)

    # Fix spacing between CJK and Latin characters
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])([\u4e00-\u9fff])", r"\1 \2", text)

    # Normalize multiple newlines >= 2 to just 1
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def clean_text(text: str) -> str:
    """Cleans general text by unescaping HTML, normalizing Unicode, removing all
    control characters, collapsing all whitespace to single spaces, and
    stripping leading/trailing whitespace.
    """
    if not isinstance(text, str):
        return ""

    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)

    # Replace all whitespace (including newlines) with single spaces,
    text = re.sub(r"\s+", " ", text)

    # Remove all control characters
    text = re.sub(r"\p{C}", "", text)

    # Remove punctuation such as brackets, quotes, etc. that may interfere with matching.
    text = re.sub(r"[\p{P}]", "", text)

    return text.strip()


def extract_cjk(s: str) -> str:
    filtered = re.sub(r"[^\p{Han}\p{Hiragana}\p{Katakana}]", "", s)
    return filtered


def extract_latin(s: str) -> str:
    return "".join(re.findall(r"[A-Za-z]+", s))


# Bracket content extraction and stripping for better matching
_OPEN = r"《【〖「『\[（("
_CLOSE = r"》】〗」』\]）)"


def extract_bracket_content(text: str) -> str:
    """Extracts content within the first pair of matching brackets."""
    m = re.match(rf"^[{_OPEN}](.+?)[{_CLOSE}]", text)
    return m.group(1).strip() if m else ""


def split_bracket(text: str) -> tuple[str, str]:
    """Strips any leading content enclosed in brackets."""
    m = re.match(rf"^[{_OPEN}](.+?)[{_CLOSE}]", text)
    if not m:
        return "", text

    bracket_content = m.group(1).strip()
    rest = text[m.end() :].strip()

    return bracket_content, rest


# Fuzzy Matching
def cjk_sim(a: str, b: str) -> float:
    """Computes a similarity score between two CJK strings based on substring
    containment and Levenshtein similarity, with special handling for short
    strings.
    """

    if not a or not b:
        return 0.0

    # True substring containment: reward highly, but scale slightly
    # by how much of the longer string the short one actually covers
    if a in b or b in a:
        shorter, longer = (a, b) if len(a) < len(b) else (b, a)
        length_ratio = len(shorter) / len(longer)
        return 0.6 + 0.4 * length_ratio

    return best_substring_sim(a, b)


def best_substring_sim(a: str, b: str) -> float:
    """Best Levenshtein similarity of `a` against any contiguous
    window of `b` close to len(a). Avoids penalizing short titles
    for the unrelated length of a long compilation title."""
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a  # ensure a is the shorter string

    n = len(a)
    best = 0.0
    # slide a window of length n (+/- a little slack) across b
    for i in range(len(b) - n + 1):
        window = b[i : i + n]
        dist = levenshtein(a, window)
        sim = 1.0 - dist / max(n, 1)
        if sim > best:
            best = sim
    return best


def levenshtein(a: str, b: str) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)
            )
        prev = curr
    return prev[-1]


def levenshtein_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    distance = levenshtein(a, b)
    return 1.0 - distance / max(len(a), len(b), 1)


_FILLER_PHRASES = [
    "官方歌詞版",  # official lyrics version
    "讚美之泉",  # stream of praise
    "敬拜讚美",  # worship praise
    "現場敬拜",  # live worship
    "精選片段",  # selected excerpts
    "MV",
    # instrumental / karaoke variants — new category
    "卡拉版",
    "卡拉OK",
    "無人聲",
    "純樂器",
    "伴奏",
    "伴唱",
    "官方敬拜",
]


def remove_filler_phrases(text: str) -> str:
    for phrase in _FILLER_PHRASES:
        text = text.replace(phrase, "")
    return text.strip()


def chars_to_key(text: str) -> str:
    """Serializable representation of a character set."""
    return "".join(sorted(set(text)))
