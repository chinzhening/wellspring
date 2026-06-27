"""
Matches songs to media using fuzzy search against the local cache.
Writes YoutubeMatch and SpotifyMatch rows with match scores. No network calls.
"""

import logging

import regex as re
from sqlalchemy.orm import Session

from core.models import (
    Song,
    SpotifyCache,
    SpotifyMatch,
    YoutubeCache,
    YoutubeMatch,
)

logger = logging.getLogger(__name__)


def run(
    db: Session,
    refresh_matches: bool = False,
) -> None:
    """
    Args:
        refresh_matches:  Recompute YoutubeMatch / SpotifyMatch rows even if
            they already exist for a song.
    """
    songs = db.query(Song).all()
    youtube_cache = db.query(YoutubeCache).all()
    spotify_cache = db.query(SpotifyCache).all()

    if not songs:
        logger.warning("No songs found in DB, skipping match computation")
        raise ValueError("No songs found in DB")

    if not youtube_cache and not spotify_cache:
        logger.warning(
            "No media cache data available, skipping match computation"
        )
        raise ValueError("No media cache data available")

    logger.info(f"Computing song -> media matches for {len(songs)} songs…")

    _compute_youtube_matches(db, youtube_cache, songs, refresh=refresh_matches)
    _compute_spotify_matches(db, spotify_cache, songs, refresh=refresh_matches)


# ===========================================================================
# Compute matches from cache
# ===========================================================================


def _compute_youtube_matches(
    db: Session,
    youtube_cache: list[YoutubeCache],
    songs: list[Song],
    refresh: bool = False,
) -> None:
    """
    Fuzzy-match each Song against YoutubeCache.  Writes YoutubeMatch rows.
    Skips songs that already have match rows unless refresh=True.
    """
    if not youtube_cache:
        logger.warning("YouTube cache is empty, skipping match computation")
        return

    video_dicts = [
        {"video_id": v.video_id, "title": v.title or ""} for v in youtube_cache
    ]

    songs_to_process = songs
    if not refresh:
        matched_song_ids = {
            row.song_id for row in db.query(YoutubeMatch.song_id).all()
        }
        songs_to_process = [s for s in songs if s.id not in matched_song_ids]

    if not songs_to_process:
        logger.info("YouTube matches already computed for all songs")
        return

    logger.info(f"Computing YouTube matches for {len(songs_to_process)} songs…")
    new_matches = 0

    for song in songs_to_process:
        if refresh:
            db.query(YoutubeMatch).filter_by(song_id=song.id).delete()

        matched = _match_song_to_videos(song.title, video_dicts)
        for m in matched:
            db.add(
                YoutubeMatch(
                    song_id=song.id,
                    video_id=m["video_id"],
                    match_score=m["score"],
                )
            )
            new_matches += 1

    db.commit()
    logger.info(f"Inserted {new_matches} YoutubeMatch rows")


def _compute_spotify_matches(
    db: Session,
    spotify_cache: list[SpotifyCache],
    songs: list[Song],
    refresh: bool = False,
) -> None:
    """
    Fuzzy-match each Song against SpotifyCache.  Writes SpotifyMatch rows.
    Skips songs that already have match rows unless refresh=True.
    """
    if not spotify_cache:
        logger.warning("Spotify cache is empty, skipping match computation")
        return

    songs_to_process = songs
    if not refresh:
        matched_song_ids = {
            row.song_id for row in db.query(SpotifyMatch.song_id).all()
        }
        songs_to_process = [s for s in songs if s.id not in matched_song_ids]

    if not songs_to_process:
        logger.info("Spotify matches already computed for all songs")
        return

    logger.info(f"Computing Spotify matches for {len(songs_to_process)} songs…")
    new_matches = 0

    for song in songs_to_process:
        if refresh:
            db.query(SpotifyMatch).filter_by(song_id=song.id).delete()

        best = max(
            spotify_cache,
            key=lambda t: _cjk_similarity(song.title, t.track_name or ""),
        )
        score = _cjk_similarity(song.title, best.track_name or "")

        if score < 0.4:
            logger.debug(f"  '{song.title}': no Spotify match above threshold")
            continue

        db.add(
            SpotifyMatch(
                song_id=song.id,
                track_id=best.track_id,
                match_score=score,
            )
        )
        new_matches += 1

    db.commit()
    logger.info(f"Inserted {new_matches} SpotifyMatch rows")


# ===========================================================================
# Fuzzy title matching helpers
# ===========================================================================

MATCH_THRESHOLD = 0.4
FILTER_BYPASS_THRESHOLD = 0.6
BRACKET_CONTENT_THRESHOLD = 0.5
MV_PATTERN = re.compile(
    r"(Worship MV|Official Lyric[s]? MV|Live Worship MV)", re.IGNORECASE
)

_OPEN = r"《【〖「『\[（("
_CLOSE = r"》】〗」』\]）)"


def _levenshtein(a: str, b: str) -> int:
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


def _cjk_similarity(a: str, b: str) -> float:
    return 1 - _levenshtein(a, b) / max(len(a), len(b), 1)


def _extract_cjk(s: str) -> str:
    matches = re.findall(r"[\p{IsHan}\p{IsHiragana}\p{IsKatakana}]+", s)
    return max(matches, key=len) if matches else ""


def _extract_bracket_content(title: str) -> str:
    m = re.match(rf"^[{_OPEN}](.+?)[{_CLOSE}]", title)
    return m.group(1).strip() if m else ""


def _strip_bracket_prefix(title: str) -> str:
    pattern = rf"^[\s{_OPEN}{_CLOSE}]+.*?[\s{_OPEN}{_CLOSE}]+\s*"
    return re.sub(pattern, "", title).strip()


def _score_video(song: str, video: dict) -> float:
    cjk_song = _extract_cjk(song)
    raw = video["title"]
    stripped = _strip_bracket_prefix(raw)
    bracket = _extract_bracket_content(raw)
    until_space = raw.split()[0] if raw else ""

    scores = [
        _cjk_similarity(song, raw),
        _cjk_similarity(song, stripped),
        _cjk_similarity(song, until_space),
        _cjk_similarity(cjk_song, stripped),
        _cjk_similarity(cjk_song, raw),
        _cjk_similarity(cjk_song, until_space),
    ]
    if bracket:
        bracket_score = max(
            _cjk_similarity(song, bracket),
            _cjk_similarity(cjk_song, bracket),
        )
        if bracket_score >= BRACKET_CONTENT_THRESHOLD:
            scores.append(bracket_score)

    return max(scores)


def _filter_youtube_results(items: list[dict]) -> list[dict]:
    if not items:
        return []
    high_conf = [
        i for i in items if i.get("score", 0) >= FILTER_BYPASS_THRESHOLD
    ]
    if high_conf:
        return high_conf
    filtered = [
        i
        for i in items
        if MV_PATTERN.search(i["title"]) or "Instrumental" in i["title"]
    ]
    return filtered if filtered else items[:1]


def _match_song_to_videos(
    song_title: str, all_videos: list[dict]
) -> list[dict]:
    """Return filtered, scored video dicts for a single song title."""
    # Cache scores for all videos, then filter/sort in one pass to avoid
    # multiple iterations
    scored = [
        {**v, "score": round(_score_video(song_title, v), 2)}
        for v in all_videos
    ]
    matched = [s for s in scored if s["score"] >= MATCH_THRESHOLD]
    matched.sort(key=lambda x: x["score"], reverse=True)
    return _filter_youtube_results(matched)
