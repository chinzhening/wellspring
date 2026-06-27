from dagster import MaterializeResult, MetadataValue, asset

from ..utility.text import cjk_sim, levenshtein_sim


@asset(group_name="matching")
def song_youtube_matches(
    sop_songs_normalized, youtube_videos_normalized
) -> MaterializeResult:
    output = []

    for song in sop_songs_normalized:
        song_cjk_char_set = set(song["cjk_title"])
        candidates = (
            entry
            for entry in youtube_videos_normalized
            if set(entry["cjk_bracket"] + entry["cjk_stripped_suffix"])
            & song_cjk_char_set
        )
        for video in candidates:
            match = _score_song_video(song, video)
            if match:
                output.append(match)

    return MaterializeResult(
        value=output,
        metadata={
            "num_records": len(output),
            "samples": MetadataValue.json(output[:5]),
        },
    )


@asset(group_name="matching")
def song_spotify_matches(
    sop_songs_normalized, spotify_tracks_normalized
) -> MaterializeResult:
    output = []

    for song in sop_songs_normalized:
        song_chars = set(song.get("cjk_title", "")) | set(
            song.get("latin_title", "").lower()
        )

        candidates = (
            track
            for track in spotify_tracks_normalized
            if song_chars
            & (
                set(track.get("cjk_title", ""))
                | set(track.get("latin_title", "").lower())
            )
        )

        for track in candidates:
            match = _score_song_track(song, track)
            if match:
                output.append(match)

    return MaterializeResult(
        value=output,
        metadata={
            "num_records": len(output),
            "samples": MetadataValue.json(output[:5]),
        },
    )


def _score_song_video(song: dict, video: dict) -> dict | None:
    song_cjk = song.get("cjk_title", "")

    v_bracket = video.get("cjk_bracket", "")
    v_stripped = video.get("cjk_stripped_suffix", "")
    v_title = video.get("cjk_title", "")

    # -------------------------------------------------------
    # 1. EXACT / SUBSTRING MATCH (HIGHEST CONFIDENCE)
    # -------------------------------------------------------
    if song_cjk and (song_cjk in v_bracket or song_cjk in v_stripped):
        return {
            "song_id": song["song_id"],
            "video_id": video["id"],
            "score": 1.0,
            "reason": "substring_match",
            "details": {
                "song_cjk": song_cjk,
                "v_bracket": v_bracket,
                "v_stripped": v_stripped,
            },
        }

    # -------------------------------------------------------
    # 2. BRACKET MATCH (VERY STRONG SIGNAL)
    # -------------------------------------------------------
    if v_bracket:
        sim = cjk_sim(song_cjk, v_bracket)
        if sim >= 0.85:
            return {
                "song_id": song["song_id"],
                "video_id": video["id"],
                "score": sim,
                "reason": "bracket_title_match",
                "details": {"song_cjk": song_cjk, "v_bracket": v_bracket},
            }

    # -------------------------------------------------------
    # 3. STRIPPED TITLE MATCH (PRIMARY FALLBACK)
    # -------------------------------------------------------
    if v_stripped:
        sim = cjk_sim(song_cjk, v_stripped)
        if sim >= 0.80:
            return {
                "song_id": song["song_id"],
                "video_id": video["id"],
                "score": sim,
                "reason": "stripped_title_match",
                "details": {"song_cjk": song_cjk, "v_stripped": v_stripped},
            }

    # -------------------------------------------------------
    # 4. FULL TITLE MATCH (NOISIER)
    # -------------------------------------------------------
    sim = cjk_sim(song_cjk, v_title)
    if sim >= 0.75:
        return {
            "song_id": song["song_id"],
            "video_id": video["id"],
            "score": sim,
            "reason": "full_title_match",
            "details": {"song_cjk": song_cjk, "v_title": v_title},
        }

    # -------------------------------------------------------
    # 5. REJECT
    # -------------------------------------------------------
    return None


def _score_song_track(song: dict, track: dict) -> dict | None:
    song_cjk = song.get("cjk_title", "")
    song_latin = song.get("latin_title", "")

    t_cjk = track.get("cjk_title", "")
    t_latin = track.get("latin_title", "")

    # ---------------------------------------------------
    # 1. EXACT MATCH (either script) — highest confidence
    # ---------------------------------------------------
    if song_cjk and t_cjk and song_cjk == t_cjk:
        return {
            "song_id": song["song_id"],
            "track_id": track["track_id"],
            "score": 1.0,
            "reason": "exact_match_cjk",
            "details": {"song_cjk": song_cjk, "t_cjk": t_cjk},
        }

    if song_latin and t_latin and song_latin.lower() == t_latin.lower():
        return {
            "song_id": song["song_id"],
            "track_id": track["track_id"],
            "score": 1.0,
            "reason": "exact_match_latin",
            "details": {"song_latin": song_latin, "t_latin": t_latin},
        }

    # ---------------------------------------------------
    # 2. FUZZY MATCH (Levenshtein) — high threshold,
    #    since Spotify titles are clean (no boilerplate,
    #    no compilation/medley noise like YouTube)
    # ---------------------------------------------------
    best_sim = 0.0
    best_reason = None

    if song_cjk and t_cjk:
        sim = cjk_sim(song_cjk, t_cjk)
        if sim > best_sim:
            best_sim, best_reason = sim, "cjk_match"

    if song_latin and t_latin:
        sim = levenshtein_sim(song_latin.lower(), t_latin.lower())
        if sim > best_sim:
            best_sim, best_reason = sim, "latin_match"

    if best_sim >= 0.90:  # higher bar than YouTube's 0.75-0.85
        return {
            "song_id": song["song_id"],
            "track_id": track["track_id"],
            "score": best_sim,
            "reason": best_reason,
            "details": {
                "song_cjk": song_cjk,
                "t_cjk": t_cjk,
                "song_latin": song_latin,
                "t_latin": t_latin,
            },
        }

    return None
