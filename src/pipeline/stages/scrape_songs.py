import logging

from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session

from core.models import Lyric, Song
from core.text import clean_lyrics, clean_text

logger = logging.getLogger(__name__)

SOURCE_URL = "https://sop.org/songs/"


# ---------------------------------------------------------------------------
# Playwright scraping
# ---------------------------------------------------------------------------


def _get_table(page):
    table = page.query_selector("table#tablepress-3")
    if table is None:
        raise RuntimeError("Could not find table with id 'tablepress-3'")
    return table


def _get_headers(table) -> list[str]:
    headers = table.query_selector_all("thead tr th")
    if not headers:
        raise RuntimeError("Could not find table headers in thead tr th")
    return [h.inner_text().strip() for h in headers]


def _get_rows(table):
    rows = table.query_selector_all("tbody tr")
    if not rows:
        raise RuntimeError("Could not find any rows in the table body")
    return rows


def _extract_row_id(row) -> str:
    class_list = row.get_attribute("class")
    if class_list is None:
        raise RuntimeError("Row does not have a class attribute")
    return class_list.split("-")[-1]


def _extract_cell_data(cell) -> str:
    return cell.inner_html()


def _extract_row_data(row, headers: list[str]) -> dict:
    cells = row.query_selector_all("td")
    if len(cells) != len(headers):
        raise RuntimeError(
            f"Row has {len(cells)} cells but expected {len(headers)}"
        )
    return {
        headers[i]: _extract_cell_data(cells[i]) for i in range(len(headers))
    }


def _is_next_disabled(btn) -> bool:
    disabled = (
        btn.get_attribute("aria-disabled")
        or btn.get_attribute("tabindex") == "-1"
        or (
            (cls := btn.get_attribute("class")) is not None
            and "disabled" in cls.split()
        )
    )
    return disabled == "true"


# ---------------------------------------------------------------------------
# Column name mapping  (website header → model field)
# ---------------------------------------------------------------------------

HEADER_MAP = {
    "曲名": "title",
    "作曲": "composer",
    "作詞": "lyricist",
    "專輯名稱": "album",
    "專輯系列": "series",
    "調性": "key",
}
LYRICS_HEADER = "歌詞"


# ---------------------------------------------------------------------------
# Main stage entry point
# ---------------------------------------------------------------------------


def run(db: Session, refresh: bool = False) -> None:
    """Scrape sop.org song table and upsert into songs + lyrics tables."""

    existing_songs: dict[str, Song] = {
        str(song.source_id): song for song in db.query(Song).all()
    }
    logger.info(
        f"Found {len(existing_songs)} existing songs in DB, scraping new ones..."
    )

    raw_rows = _scrape_raw_rows()
    logger.info(f"Scraped {len(raw_rows)} rows from source")

    new_songs = 0
    for row in raw_rows:
        source_id = row.pop("source_id")
        song = existing_songs.get(source_id)
        if song is not None and not refresh:
            continue

        # Assumption: lyrics are in traditional Chinese, may need to convert if source changes in the future
        lyrics_traditional = clean_lyrics(row.pop(LYRICS_HEADER, ""))

        # Build Song
        song_fields = {
            model_field: clean_text(row.get(header, ""))
            for header, model_field in HEADER_MAP.items()
        }
        if song is None:
            song = Song(
                source_id=source_id, source_url=SOURCE_URL, **song_fields
            )
            db.add(song)
            db.flush()  # get song.id before inserting Lyric

            db.add(
                Lyric(
                    song_id=song.id,
                    traditional=lyrics_traditional,
                )
            )
            new_songs += 1

    db.commit()
    logger.info(f"Inserted {new_songs} new songs")


def _scrape_raw_rows() -> list[dict]:
    """Return raw rows as dicts with source_id and all header columns."""
    rows_out = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(SOURCE_URL)

        table = _get_table(page)
        headers = _get_headers(table)

        while True:
            for row in _get_rows(table):
                data = {
                    "source_id": _extract_row_id(row),
                    **_extract_row_data(row, headers),
                }
                rows_out.append(data)

            next_btn = page.query_selector("button.dt-paging-button.next")
            if next_btn is None or _is_next_disabled(next_btn):
                break
            next_btn.click()
            page.wait_for_timeout(100)

        browser.close()

    return rows_out
