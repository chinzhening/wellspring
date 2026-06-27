import polars as pl
from dagster import MaterializeResult, asset


@asset(group_name="serving")
def terms_serving(song_terms_normalized, term_stats) -> MaterializeResult:
    terms = pl.DataFrame(song_terms_normalized).join(
        pl.DataFrame(term_stats), on="id"
    )

    return MaterializeResult(
        value=terms,
        metadata={
            "rows": len(terms),
            "samples": terms.head(5).to_dicts(),
        },
    )


@asset(group_name="serving")
def songs_serving(
    sop_songs_normalized,
    song_spotify_matches,
    song_youtube_matches,
    spotify_tracks_normalized,
    youtube_videos_normalized,
) -> MaterializeResult:
    songs = pl.DataFrame(sop_songs_normalized)  # song_id
    spotify_matches = pl.DataFrame(song_spotify_matches)  # song_id -> track_id
    youtube_matches = pl.DataFrame(song_youtube_matches)  # song_id -> video_id
    spotify = pl.DataFrame(spotify_tracks_normalized)  # track_id
    youtube = pl.DataFrame(youtube_videos_normalized)  # video_id

    song_cols = [
        "song_id",
        "normalized_title",
        "normalized_album",
        "raw_composer",
        "raw_lyricist",
        "raw_series",
        "raw_key",
    ]
    songs = songs[song_cols].rename(
        {
            "normalized_title": "title",
            "normalized_album": "album",
            "raw_composer": "composer",
            "raw_lyricist": "lyricist",
            "raw_series": "series",
            "raw_key": "key",
        }
    )

    spotify = spotify[["track_id", "normalized_track_name"]].rename(
        {
            "normalized_track_name": "spotify_title",
            "track_id": "spotify_id",
        }
    )
    spotify_matches = spotify_matches[["song_id", "track_id", "score"]].rename(
        {"score": "spotify_score", "track_id": "spotify_id"}
    )

    youtube = youtube[["id", "title", "url"]].rename(
        {"id": "youtube_id", "title": "youtube_title", "url": "youtube_url"}
    )
    youtube_matches = youtube_matches[["song_id", "video_id", "score"]].rename(
        {"score": "youtube_score", "video_id": "youtube_id"}
    )

    best_spotify = (
        spotify_matches.group_by("song_id")
        .agg(pl.all().sort_by("spotify_score", descending=True).first())
        .join(spotify, on="spotify_id", how="left")
    )

    best_youtube = (
        youtube_matches.group_by("song_id")
        .agg(pl.all().sort_by("youtube_score", descending=True).first())
        .join(youtube, on="youtube_id", how="left")
    )

    songs = songs.join(best_spotify, on="song_id", how="left").join(
        best_youtube, on="song_id", how="left"
    )

    # add spotify_url
    songs = songs.with_columns(
        pl.when(pl.col("spotify_id").is_not_null())
        .then(
            pl.format("https://open.spotify.com/track/{}", pl.col("spotify_id"))
        )
        .otherwise(None)
        .alias("spotify_url")
    )

    # drop spotify_score and youtube_score
    songs = songs.drop(["spotify_score", "youtube_score"])

    return MaterializeResult(
        value=songs,
        metadata={
            "rows": songs.height,
            "samples": songs.head(5).to_dicts(),
        },
    )


@asset(group_name="serving")
def song_terms_serving(term_song_index) -> MaterializeResult:
    song_terms = []
    for item in term_song_index:
        song_terms.extend(
            [
                {"term_id": item["term_id"], "song_id": song_id}
                for song_id in item["song_ids"]
            ]
        )

    song_terms = pl.DataFrame(song_terms)

    return MaterializeResult(
        value=song_terms,
        metadata={
            "rows": len(song_terms),
            "samples": song_terms.head(5).to_dicts(),
        },
    )


@asset(group_name="serving")
def song_lyrics_serving(song_lyrics_tokenized) -> MaterializeResult:
    lyrics = []

    for item in song_lyrics_tokenized:
        song_id = item["song_id"]
        lyrics_clean = item["lyrics_clean"]
        lyrics_tokenized = item["lyrics_tokenized"]  # dict

        lyrics.append(
            {
                "song_id": song_id,
                "lyrics_clean": lyrics_clean,
                "lyrics_tokenized": lyrics_tokenized,
            }
        )

    lyrics = pl.DataFrame(lyrics)
    print(lyrics.head())

    return MaterializeResult(
        value=lyrics,
        metadata={
            "rows": len(lyrics),
            "samples": lyrics.head(5).to_dicts(),
        },
    )
