import math

from dagster import (
    MaterializeResult,
    MetadataValue,
    asset,
)


@asset(group_name="analytics")
def song_stats(
    song_catalog,
    spotify_tracks_normalized,
    youtube_videos_normalized,
) -> MaterializeResult:

    stats = {
        song["song_id"]: {
            "youtube_views": 0,
            "spotify_playcount": 0,
            "popularity_score": 0.0,
        }
        for song in song_catalog
    }

    yt_map, spot_map = {}, {}
    for song in song_catalog:
        youtube_ids = song.get("youtube_match", [])
        spotify_ids = song.get("spotify_match", [])
        for video_id in youtube_ids:
            if video_id not in yt_map:
                yt_map[video_id] = []
            yt_map[video_id].append(song["song_id"])

        for track_id in spotify_ids:
            if track_id not in spot_map:
                spot_map[track_id] = []
            spot_map[track_id].append(song["song_id"])

    for video in youtube_videos_normalized:
        video_id = video["id"]
        if video_id in yt_map:
            for song_id in yt_map[video_id]:
                stats[song_id]["youtube_views"] += video.get("views", 0)

    for track in spotify_tracks_normalized:
        track_id = track["track_id"]
        if track_id in spot_map:
            for song_id in spot_map[track_id]:
                stats[song_id]["spotify_playcount"] += track.get("playcount", 0)

    for _, data in stats.items():
        youtube_views = data["youtube_views"]
        spotify_playcount = data["spotify_playcount"]
        popularity_score = _compute_popularity(youtube_views, spotify_playcount)
        data["popularity_score"] = popularity_score

    stats = [
        {
            "song_id": song_id,
            "youtube_views": data["youtube_views"],
            "spotify_playcount": data["spotify_playcount"],
            "popularity_score": data["popularity_score"],
        }
        for song_id, data in stats.items()
    ]

    return MaterializeResult(
        value=stats,
        metadata={
            "num_records": len(stats),
            "samples": MetadataValue.json(stats[:5]),
        },
    )


def _compute_popularity(youtube_views: int, spotify_playcount: int) -> float:
    """Compute a popularity score based on YouTube views and Spotify playcount."""
    # Normalize the values to a scale of 0 to 100
    max_youtube_views = 1_000_000  # Example threshold for normalization
    max_spotify_playcount = 1_000_000  # Example threshold for normalization

    normalized_youtube = min(youtube_views / max_youtube_views, 1.0)
    normalized_spotify = min(spotify_playcount / max_spotify_playcount, 1.0)

    # Compute a weighted average (weights can be adjusted)
    popularity_score = (0.4 * normalized_youtube) + (0.6 * normalized_spotify)
    return popularity_score * 100


@asset(group_name="analytics")
def term_stats(term_song_index, song_stats) -> MaterializeResult:
    pop_map = {
        entry["song_id"]: entry["popularity_score"] for entry in song_stats
    }
    term_song_map = {
        entry["term_id"]: entry["song_ids"] for entry in term_song_index
    }

    stats = []

    for term_id, song_ids in term_song_map.items():
        term_score = score_term(song_ids, pop_map)
        stats.append(
            {"id": term_id, "song_count": len(song_ids), "score": term_score}
        )

    scores = [entry["score"] for entry in stats]
    tiers = assign_tier(scores)

    for entry, tier in zip(stats, tiers, strict=True):
        entry["tier"] = tier

    return MaterializeResult(
        value=stats,
        metadata={
            "num_records": len(stats),
            "samples": MetadataValue.json(stats[:5]),
        },
    )


def score_term(song_ids, pop_map):
    """Log-dampened sum of popularity weights."""
    weighted_freq = sum(pop_map.get(i, 0.0) / 100.0 for i in song_ids)
    return math.log1p(weighted_freq)


def assign_tier(scores):
    """Tier 1: top 15%, Tier 2: next 35%, Tier 3: bottom 50%"""
    sorted_scores = sorted(scores, reverse=True)
    n = len(sorted_scores)
    tier1_cutoff = sorted_scores[int(n * 0.15)] if n > 0 else 0
    tier2_cutoff = sorted_scores[int(n * 0.50)] if n > 0 else 0

    return [
        1 if score >= tier1_cutoff else 2 if score >= tier2_cutoff else 3
        for score in scores
    ]
