from dagster import MaterializeResult, MetadataValue, asset


@asset(group_name="indexing")
def term_song_index(
    song_terms_normalized,
    sop_songs_normalized,
) -> MaterializeResult:
    index = []
    term_map = {term["traditional"]: [] for term in song_terms_normalized}

    for song in sop_songs_normalized:
        for term in term_map.keys():
            if term in song.get("lyrics_clean", []):
                term_map[term].append(song["song_id"])

    for term in song_terms_normalized:
        index.append(
            {
                "term_id": term["id"],
                "song_ids": term_map.get(term["traditional"], []),
            }
        )

    return MaterializeResult(
        value=index,
        metadata={
            "num_records": len(index),
            "samples": MetadataValue.json(index[:5]),
        },
    )
