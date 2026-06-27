"""
Aggregates YoutubeMatch and SpotifyMatch rows into a SongStat row per song.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from core.models import (
    Song,
    SongStat,
    SpotifyCache,
    SpotifyMatch,
    YoutubeCache,
    YoutubeMatch,
)

logger = logging.getLogger(__name__)


def run(db: Session) -> None:
    """
    Reads from the match tables and caches, writes to SongStat.
    """
    songs = db.query(Song).all()
    youtube_cache = db.query(YoutubeCache).all()
    spotify_cache = db.query(SpotifyCache).all()
    if not songs:
        logger.warning("No songs found in DB, skipping stats computation.")
        return
    if not youtube_cache:
        logger.warning(
            "No YouTube cache entries found in DB, stats will be incomplete."
        )
    if not spotify_cache:
        logger.warning(
            "No Spotify cache entries found in DB, stats will be incomplete."
        )

    logger.info(
        f"Computing stats for {len(songs)} songs with {len(youtube_cache)}"
        f" YouTube cache entries and {len(spotify_cache)} Spotify cache entries."
    )

    _compute_song_stats(db, songs)


def _compute_song_stats(db: Session, songs: list[Song]) -> None:
    """
    Build/refresh SongStat rows from YoutubeMatch + SpotifyMatch.

    Strategy:
    - YouTube: sum views across all matched videos; pick the highest-view match
      as the canonical youtube_match_id.
    - Spotify: pick the single best-score SpotifyMatch as spotify_match_id.
    - One SongStat row per song (upsert).
    """
    yt_cache_view: dict[str, int] = {
        row.video_id: (row.views or 0) for row in db.query(YoutubeCache).all()
    }

    spot_cache_view: dict[str, int] = {
        row.track_id: (row.playcount or 0)
        for row in db.query(SpotifyCache).all()
    }

    yt_matches_by_song: dict[int, list[YoutubeMatch]] = defaultdict(list)
    spot_matches_by_song: dict[int, list[SpotifyMatch]] = defaultdict(list)

    for m in db.query(YoutubeMatch).all():
        yt_matches_by_song[m.song_id].append(m)

    for m in db.query(SpotifyMatch).all():
        spot_matches_by_song[m.song_id].append(m)

    now = datetime.now(UTC)
    upsert_rows: list[dict] = []

    for song in songs:
        yt_matches = yt_matches_by_song.get(song.id, [])
        spot_matches = spot_matches_by_song.get(song.id, [])

        if not yt_matches and not spot_matches:
            continue

        # ── YouTube aggregation ──────────────────────────────────────────
        youtube_views = None
        top_yt_match_id = None

        if yt_matches:
            youtube_views = 0
            top_views = -1

            for m in yt_matches:
                views = yt_cache_view.get(m.video_id, 0)

                if views > top_views:
                    top_views = views
                    top_yt_match_id = m.id

                youtube_views += views

        # ── Spotify aggregation ──────────────────────────────────────────
        top_spot_match_id = None
        top_spot_playcount = None

        if spot_matches:
            top_spot = max(
                spot_matches,
                key=lambda m: m.match_score or 0,
            )
            top_spot_match_id = top_spot.id
            top_spot_playcount = spot_cache_view.get(top_spot.track_id, 0)

        upsert_rows.append(
            {
                "song_id": song.id,
                "youtube_match_id": top_yt_match_id,
                "spotify_match_id": top_spot_match_id,
                "youtube_views": youtube_views,
                "spotify_playcount": top_spot_playcount,
                "updated_at": now,
            }
        )

    _upsert_song_stats(db, upsert_rows)

    db.commit()


def _upsert_song_stats(db: Session, rows: list[dict]) -> None:
    """
    Bulk upsert SongStat rows by song_id.
    Assumes song_id has a UNIQUE constraint.
    """
    if not rows:
        return

    stmt = pg_insert(SongStat).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[SongStat.song_id],
        set_={
            "youtube_match_id": stmt.excluded.youtube_match_id,
            "spotify_match_id": stmt.excluded.spotify_match_id,
            "youtube_views": stmt.excluded.youtube_views,
            "spotify_playcount": stmt.excluded.spotify_playcount,
            "updated_at": stmt.excluded.updated_at,
        },
    )

    db.execute(stmt)
