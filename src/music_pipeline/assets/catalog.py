from dagster import MaterializeResult, MetadataValue, asset


@asset(group_name="catalog")
def song_catalog(
    sop_songs_normalized,
    song_youtube_matches,
    song_spotify_matches,
):
    catalog = []
    youtube_map = {match["song_id"]: [] for match in song_youtube_matches}
    spotify_map = {match["song_id"]: [] for match in song_spotify_matches}

    for match in song_youtube_matches:
        youtube_map[match["song_id"]].append(match["video_id"])

    for match in song_spotify_matches:
        spotify_map[match["song_id"]].append(match["track_id"])

    for song in sop_songs_normalized:
        song_id = song["song_id"]
        catalog_entry = {
            "song_id": song_id,
            "raw_title": song.get("raw_title"),
            "youtube_match": youtube_map.get(song_id, []),
            "spotify_match": spotify_map.get(song_id, []),
        }
        catalog.append(catalog_entry)

    return MaterializeResult(
        value=catalog,
        metadata={
            "num_records": len(catalog),
            "samples": MetadataValue.json(catalog[:5]),
        },
    )
