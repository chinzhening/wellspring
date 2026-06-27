"""
scrape_media.py — fetch and cache raw stats from YouTube and Spotify.

Populates two cache tables (one row per video / per track) that downstream
stages read without making further network calls.  These are the only
functions in the pipeline that hit external APIs.

YouTube
    Calls the YouTube Data API to collect playlist membership and per-video
    stats, then upserts into youtube_cache.

Spotify
    Scrapes the artist discography page via Playwright to collect track
    details and play counts, then upserts into spotify_cache.

Both phases are cheap to re-run. Use refresh_youtube_cache or
refresh_spotify_cache to force a re-fetch; otherwise each phase skips
if its table is already populated.
"""

import logging
from datetime import UTC, datetime

from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from core.config import settings
from core.models import (
    Song,
    SpotifyCache,
    YoutubeCache,
)

logger = logging.getLogger(__name__)

CHANNEL_ID = "UC00EceQGGCMucNvwOS-jQ7A"
SPOTIFY_ARTIST_ID = "4doyJAIKxTGN2II0QpgUjT"


def run(
    db: Session,
    refresh_youtube_cache: bool = False,
    refresh_spotify_cache: bool = False,
) -> None:
    """
    Scrape media stats for all songs in the database.

    Args:
        refresh_youtube_cache: Re-fetch YouTube API data (playlist + per-video
            stats) even if cache rows already exist.
        refresh_spotify_cache: Re-scrape Spotify artist page even if cache rows
            already exist.
    """
    songs = db.query(Song).all()
    if not songs:
        logger.warning("No songs in DB, skipping media scrape")
        return

    logger.info(f"Starting media scrape for {len(songs)} songs…")

    _refresh_youtube_cache(db, refresh=refresh_youtube_cache)
    _refresh_spotify_cache(db, refresh=refresh_spotify_cache)


# ---------------------------------------------------------------------------
# YouTube cache  (one row per video)
# ---------------------------------------------------------------------------


def _refresh_youtube_cache(db: Session, refresh: bool = False) -> None:
    """
    Fetch every video in the channel playlist, then fetch view counts for any
    video not yet in the cache (or all videos if refresh=True).  Each video is
    stored as its own YoutubeCache row keyed on video_id.
    """
    if not settings.youtube_api_key:
        logger.warning(
            "YOUTUBE_API_KEY not set, skipping YouTube cache refresh"
        )
        return

    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    # -- 1a. Get full video list from the channel's uploads playlist ----------
    logger.info("Fetching channel video list from YouTube API…")
    playlist_videos = _get_all_playlist_videos(youtube)
    logger.info(f"  {len(playlist_videos)} videos in channel playlist")

    # -- 1b. Determine which video_ids need stats fetched --------------------
    if refresh:
        needs_fetch = [v["video_id"] for v in playlist_videos]
    else:
        cached_ids: set[str] = {
            row.video_id for row in db.query(YoutubeCache.video_id).all()
        }
        needs_fetch = [
            v["video_id"]
            for v in playlist_videos
            if v["video_id"] not in cached_ids
        ]

    if needs_fetch:
        logger.info(f"  Fetching stats for {len(needs_fetch)} videos…")
        stats_map = _get_video_stats(youtube, needs_fetch)
        _upsert_youtube_cache(db, playlist_videos, stats_map)
    else:
        logger.info("  YouTube cache is up-to-date, skipping API fetch")


def _get_all_playlist_videos(youtube) -> list[dict]:
    """Return [{video_id, title}, …] for the channel's uploads playlist."""
    res = (
        youtube.channels().list(part="contentDetails", id=CHANNEL_ID).execute()
    )
    uploads_id = res["items"][0]["contentDetails"]["relatedPlaylists"][
        "uploads"
    ]

    videos, next_page = [], None
    while True:
        res = (
            youtube.playlistItems()
            .list(
                part="snippet",
                playlistId=uploads_id,
                maxResults=50,
                pageToken=next_page,
            )
            .execute()
        )
        for item in res["items"]:
            videos.append(
                {
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                }
            )
        next_page = res.get("nextPageToken")
        if not next_page:
            break
    return videos


def _get_video_stats(youtube, video_ids: list[str]) -> dict[str, dict]:
    """
    Batch-fetch statistics+snippet for the given video IDs.
    Returns {video_id: {title, views, url}}.
    """
    stats: dict[str, dict] = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        res = (
            youtube.videos()
            .list(part="statistics,snippet", id=",".join(batch))
            .execute()
        )
        for item in res["items"]:
            vid = item["id"]
            stats[vid] = {
                "title": item["snippet"]["title"],
                "views": int(item["statistics"].get("viewCount", 0)),
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
    return stats


def _upsert_youtube_cache(
    db: Session,
    playlist_videos: list[dict],
    stats_map: dict[str, dict],
) -> None:
    """
    Upsert one YoutubeCache row per video.  Playlist title is used as fallback
    when the stats API doesn't return an entry (e.g. deleted/private videos).
    """
    now = datetime.now(UTC)
    rows = []
    for v in playlist_videos:
        vid = v["video_id"]
        stat = stats_map.get(vid, {})
        rows.append(
            {
                "video_id": vid,
                "title": stat.get("title") or v["title"],
                "views": stat.get("views"),
                "url": stat.get(
                    "url", f"https://www.youtube.com/watch?v={vid}"
                ),
                "published_at": stat.get("published_at"),
                "scraped_at": now,
            }
        )

    if not rows:
        return

    stmt = pg_insert(YoutubeCache).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["video_id"],
        set_={
            "title": stmt.excluded.title,
            "views": stmt.excluded.views,
            "url": stmt.excluded.url,
            "scraped_at": stmt.excluded.scraped_at,
            "published_at": stmt.excluded.published_at,
        },
    )
    db.execute(stmt)
    db.commit()
    logger.info(f"  Upserted {len(rows)} rows into youtube_cache")


# ---------------------------------------------------------------------------
# Spotify cache  (one row per track — unchanged logic, aligned field names)
# ---------------------------------------------------------------------------


def _refresh_spotify_cache(db: Session, refresh: bool = False) -> None:
    """Scrape the Spotify artist discography page and upsert SpotifyCache rows."""
    if not refresh and db.query(SpotifyCache).first():
        logger.info("Spotify cache already populated, skipping scrape")
        return

    logger.info("Scraping Spotify artist page…")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=[
                "--incognito",
                "--disable-blink-features=AutomationControlled",
            ],
            headless=False,
            slow_mo=100,
        )
        page = browser.new_page()
        track_rows = _scrape_spotify_tracks(page)
        browser.close()

    if not track_rows:
        logger.warning("No Spotify tracks scraped")
        return

    stmt = pg_insert(SpotifyCache).values(list(track_rows.values()))
    stmt = stmt.on_conflict_do_update(
        index_elements=["track_id"],
        set_={
            "track_name": stmt.excluded.track_name,
            "album_name": stmt.excluded.album_name,
            "track_number": stmt.excluded.track_number,
            "duration_ms": stmt.excluded.duration_ms,
            "playcount": stmt.excluded.playcount,
            "scraped_at": stmt.excluded.scraped_at,
        },
    )
    db.execute(stmt)
    db.commit()
    logger.info(f"Upserted {len(track_rows)} rows into spotify_cache")


# ---------------------------------------------------------------------------
# Spotify scraping logic — Playwright orchestration only
# ---------------------------------------------------------------------------


def _scrape_spotify_tracks(page) -> dict[str, dict]:
    """Navigate and scroll the artist discography page, collecting intercepted tracks."""
    seen: set[str] = set()
    rows: dict[str, dict] = {}
    handler = _make_spotify_response_handler(seen=seen, rows=rows)

    page.on("response", handler)
    page.goto(
        f"https://open.spotify.com/artist/{SPOTIFY_ARTIST_ID}/discography/all"
    )
    _scroll_discography_page(page, rows)
    page.remove_listener("response", handler)

    return rows


def _scroll_discography_page(page, rows: dict) -> None:
    """Scroll the main view until no new tracks arrive."""
    main_view = page.locator("#main-view")
    main_view.wait_for(state="visible", timeout=5000)
    main_view.scroll_into_view_if_needed()
    main_view.hover()

    prev_count = 0
    while True:
        page.wait_for_timeout(1000)
        page.mouse.wheel(0, 3000)

        if len(rows) == prev_count:
            break

        prev_count = len(rows)


# ---------------------------------------------------------------------------
# Response handler factory — wires together parsing, extraction, and building
# ---------------------------------------------------------------------------


def _make_spotify_response_handler(
    seen: set[str],
    rows: dict[str, dict],
):
    """Return a response listener that accumulates track rows into `rows`."""

    def handle_response(response):
        if "api-partner.spotify.com/pathfinder/v2/query" not in response.url:
            return

        data = _parse_spotify_response(response)
        if data is None:
            return

        extracted = _extract_spotify_tracks(data, response)
        if extracted is None:
            return

        album_name, items = extracted

        try:
            for item in items:
                row = _build_spotify_track_row(
                    item.get("track", {}), album_name
                )
                if row is None:
                    continue

                track_id, track_data = row
                if track_id in seen:
                    continue

                seen.add(track_id)
                rows[track_id] = track_data

        except Exception:
            logger.exception(
                "Error processing Spotify API response: %s", response.url
            )

    return handle_response


# ---------------------------------------------------------------------------
# Data parsing and extraction
# ---------------------------------------------------------------------------


def _parse_spotify_response(response) -> dict | None:
    try:
        return response.json()
    except Exception:
        logger.exception(
            "Failed to parse Spotify API response: %s", response.url
        )
        return None


def _extract_spotify_tracks(
    data: dict,
    response,
) -> tuple[str, list[dict]] | None:
    try:
        album = data.get("data", {}).get("albumUnion", {})
        return (
            album.get("name", ""),
            album.get("tracksV2", {}).get("items", []),
        )
    except Exception:
        logger.exception(
            "Unexpected Spotify API payload shape: %s", response.url
        )
        try:
            logger.debug("Spotify response payload: %s", response.text()[:2000])
        except Exception:
            pass
        return None


def _build_spotify_track_row(
    track: dict,
    album_name: str,
) -> tuple[str, dict] | None:
    uri = track.get("uri", "")
    if not uri:
        return None

    track_id = uri.split(":")[-1]

    return (
        track_id,
        {
            "track_id": track_id,
            "track_name": track.get("name"),
            "album_name": album_name,
            "track_number": track.get("trackNumber"),
            "duration_ms": track.get("duration", {}).get("totalMilliseconds"),
            "playcount": (
                int(track["playcount"]) if track.get("playcount") else None
            ),
            "scraped_at": datetime.now(UTC),
        },
    )
