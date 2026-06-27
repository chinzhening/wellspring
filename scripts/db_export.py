import csv
import os

from core.config import settings
from core.db import SessionLocal
from core.models import Lyric, Song, SongStat, SpotifyMatch, YoutubeMatch


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _open_csv(filename: str):
    """Return an open file handle for writing to the export directory."""
    _ensure_dir(settings.export_dir)
    path = os.path.join(settings.export_dir, filename)
    return open(path, "w", newline="", encoding="utf-8"), path


def export_songs() -> None:
    with SessionLocal() as db:
        songs = (
            db.query(Song, SongStat, YoutubeMatch, SpotifyMatch)
            .outerjoin(SongStat, SongStat.song_id == Song.id)
            .outerjoin(
                YoutubeMatch, YoutubeMatch.id == SongStat.youtube_match_id
            )
            .outerjoin(
                SpotifyMatch, SpotifyMatch.id == SongStat.spotify_match_id
            )
            .all()
        )

        f, path = _open_csv("songs.csv")
        with f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "title",
                    "composer",
                    "lyricist",
                    "album",
                    "series",
                    "key",
                    "source_url",
                    "scraped_at",
                    "youtube_views",
                    "youtube_url",
                    "spotify_playcount",
                    "spotify_url",
                ]
            )
            for song, stat, yt, spot in songs:
                writer.writerow(
                    [
                        song.id,
                        song.title,
                        song.composer,
                        song.lyricist,
                        song.album,
                        song.series,
                        song.key,
                        song.source_url,
                        song.scraped_at,
                        stat.youtube_views if stat else None,
                        f"https://www.youtube.com/watch?v={yt.video_id}"
                        if yt
                        else None,
                        stat.spotify_playcount if stat else None,
                        f"https://open.spotify.com/track/{spot.track_id}"
                        if spot
                        else None,
                    ]
                )

    print(f"Exported {len(songs)} songs → {path}")


def export_lyrics() -> None:
    with SessionLocal() as db:
        lyrics = db.query(Lyric).all()

        f, path = _open_csv("lyrics.csv")
        with f:
            writer = csv.writer(f)
            writer.writerow(["song_id", "traditional", "simplified", "pinyin"])
            for lyric in lyrics:
                writer.writerow(
                    [
                        lyric.song_id,
                        lyric.traditional,
                        lyric.simplified,
                        lyric.pinyin,
                    ]
                )

    print(f"Exported {len(lyrics)} lyrics → {path}")


if __name__ == "__main__":
    export_songs()
    export_lyrics()
