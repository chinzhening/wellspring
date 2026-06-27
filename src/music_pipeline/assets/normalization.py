import hashlib

from dagster import MaterializeResult, MetadataValue, asset

from ..utility.text import (
    clean_lyrics,
    clean_text,
    extract_cjk,
    extract_latin,
    remove_filler_phrases,
    split_bracket,
)


@asset(group_name="normalization")
def sop_songs_normalized(sop_songs_raw):
    normalized = []

    for song in sop_songs_raw:
        title = song.get("raw_title", "")
        composer = song.get("raw_composer", "")
        album = song.get("raw_album", "")
        lyrics = song.get("raw_lyrics", "")

        normalized_song = {
            # raw fields
            **song,
            # derived fields
            "normalized_title": clean_text(title),
            "normalized_album": clean_text(album),
            "lyrics_clean": clean_lyrics(lyrics),
            "song_id": _generate_song_id(title, composer, album),
            # fields for entity resolution
            "cjk_title": extract_cjk(title),
            "cjk_album": extract_cjk(album),
            "latin_title": extract_latin(title),
            "latin_album": extract_latin(album),
        }

        normalized.append(normalized_song)

    return MaterializeResult(
        metadata={
            "num_records": len(normalized),
            "sample": MetadataValue.json(normalized[0] if normalized else {}),
        },
        value=normalized,
    )


def _generate_song_id(title: str, composer: str, album: str) -> str:
    key = f"{title}|{composer}|{album}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


# Youtube


@asset(group_name="normalization")
def youtube_videos_normalized(youtube_videos_raw) -> MaterializeResult:
    normalized = []

    for video in youtube_videos_raw:
        title = video.get("title", "")
        normalized_title = clean_text(title)
        normalized_description = clean_text(video.get("description", ""))

        bracket, suffix = split_bracket(title)
        stripped_suffix = remove_filler_phrases(suffix)

        cjk_title = extract_cjk(title)
        cjk_stripped_suffix = extract_cjk(stripped_suffix)
        cjk_bracket = extract_cjk(bracket)

        normalized.append(
            {
                **video,
                # normalized fields
                "normalized_title": normalized_title,
                "normalized_description": normalized_description,
                # fields for entity resolution
                "bracket": bracket,
                "suffix": suffix,
                "stripped_suffix": stripped_suffix,
                # cjk and latin fields
                "cjk_title": cjk_title,
                "cjk_bracket": cjk_bracket,
                "cjk_stripped_suffix": cjk_stripped_suffix,
                # latin fields
                "latin_title": extract_latin(normalized_title),
                "latin_bracket": extract_latin(bracket),
                "latin_suffix": extract_latin(suffix),
            }
        )

    return MaterializeResult(
        value=normalized,
        metadata={
            "num_records": len(normalized),
            "samples": MetadataValue.json(normalized[:3] if normalized else {}),
        },
    )


# Spotify
@asset(group_name="normalization")
def spotify_tracks_normalized(spotify_songs_raw) -> MaterializeResult:
    normalized = []

    for track in spotify_songs_raw:
        normalized.append(
            {
                **track,
                "normalized_track_name": clean_text(track["track_name"]),
                # fields for entity resolution
                "cjk_title": extract_cjk(track["track_name"]),
                "latin_title": extract_latin(track["track_name"]),
                # TODO: proper parsing of playcount, it may not be an integer (bad case)
                "playcount": int(track.get("playcount", 0)),
            }
        )

    return MaterializeResult(
        value=normalized,
        metadata={
            "num_records": len(normalized),
            "samples": MetadataValue.json(normalized[:3] if normalized else {}),
        },
    )
