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

    return text.strip()
