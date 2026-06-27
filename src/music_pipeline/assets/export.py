import json
from pathlib import Path

import polars as pl
from dagster import MaterializeResult, asset

DATA_DIR = Path("data")


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


@asset(group_name="export")
def export_songs_json(
    songs_serving: pl.DataFrame,
    song_lyrics_serving: pl.DataFrame,
) -> MaterializeResult:
    out_dir = DATA_DIR / "songs"

    combined = songs_serving.join(song_lyrics_serving, on="song_id", how="left")

    for song in combined.iter_rows(named=True):
        write_json(
            out_dir / f"{song['song_id']}.json",
            song,
        )

    return MaterializeResult(
        metadata={
            "exported": songs_serving.height,
            "directory": str(out_dir),
        }
    )


@asset(group_name="export")
def export_terms_json(
    terms_serving: pl.DataFrame,
) -> MaterializeResult:
    out_dir = DATA_DIR / "terms"

    for row in terms_serving.iter_rows(named=True):
        write_json(
            out_dir / f"{row['id']}.json",
            row,
        )

    return MaterializeResult(
        metadata={
            "exported": terms_serving.height,
            "directory": str(out_dir),
        }
    )


@asset(group_name="export")
def export_song_index_json(
    songs_serving: pl.DataFrame, song_lyrics_serving: pl.DataFrame
) -> MaterializeResult:
    out_file = DATA_DIR / "index" / "song.json"

    combined = songs_serving.join(song_lyrics_serving, on="song_id", how="left")

    combined = combined.select(
        [
            "song_id",
            "title",
            "album",
            "composer",
            "lyricist",
            "series",
            "lyrics_clean",
        ]
    )

    write_json(
        out_file,
        songs_serving.to_dicts(),
    )

    return MaterializeResult(
        metadata={
            "rows": songs_serving.height,
            "path": str(out_file),
        }
    )


@asset(group_name="export")
def export_term_index_json(
    terms_serving: pl.DataFrame,
) -> MaterializeResult:
    out_file = DATA_DIR / "index" / "term.json"

    write_json(
        out_file,
        terms_serving.to_dicts(),
    )

    return MaterializeResult(
        metadata={
            "rows": terms_serving.height,
            "path": str(out_file),
        }
    )


@asset(group_name="export")
def export_song_term_index_json(
    song_terms_serving: pl.DataFrame,
) -> MaterializeResult:
    out_file = DATA_DIR / "index" / "song_term.json"

    write_json(
        out_file,
        song_terms_serving.to_dicts(),
    )

    return MaterializeResult(
        metadata={
            "rows": song_terms_serving.height,
            "path": str(out_file),
        }
    )
