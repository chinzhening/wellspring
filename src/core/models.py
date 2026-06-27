from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector as PGVector
except ImportError:
    PGVector = None


class Base(DeclarativeBase):
    pass


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)  # 曲名
    composer: Mapped[str | None] = mapped_column(Text)  # 作曲
    lyricist: Mapped[str | None] = mapped_column(Text)  # 作詞
    album: Mapped[str | None] = mapped_column(Text)  # 專輯名稱
    series: Mapped[str | None] = mapped_column(Text)  # 專輯系列
    key: Mapped[str | None] = mapped_column(String(16))  # 調性

    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lyrics = relationship("Lyric", back_populates="song", uselist=False)
    stats = relationship(
        "SongStat",
        back_populates="song",
        uselist=False,
        cascade="all, delete-orphan",
    )

    youtube_matches = relationship(
        "YoutubeMatch", back_populates="song", cascade="all, delete-orphan"
    )
    spotify_matches = relationship(
        "SpotifyMatch", back_populates="song", cascade="all, delete-orphan"
    )

    song_terms = relationship("SongTerm", back_populates="song")


class Lyric(Base):
    __tablename__ = "lyrics"

    song_id: Mapped[int] = mapped_column(
        ForeignKey("songs.id"), primary_key=True
    )
    traditional: Mapped[str | None] = mapped_column(Text)
    simplified: Mapped[str | None] = mapped_column(Text)
    pinyin: Mapped[str | None] = mapped_column(Text)

    song = relationship("Song", back_populates="lyrics")


class SongStat(Base):
    __tablename__ = "song_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"), unique=True)

    youtube_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("youtube_matches.id"), nullable=True
    )
    spotify_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("spotify_matches.id"), nullable=True
    )

    youtube_views: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    spotify_playcount: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    song = relationship("Song", back_populates="stats")

    youtube_match = relationship(
        "YoutubeMatch", foreign_keys=[youtube_match_id]
    )
    spotify_match = relationship(
        "SpotifyMatch", foreign_keys=[spotify_match_id]
    )


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traditional: Mapped[str] = mapped_column(Text, unique=True)
    simplified: Mapped[str | None] = mapped_column(Text)
    pinyin: Mapped[str | None] = mapped_column(Text)
    definition: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[str | None] = (
        mapped_column(PGVector(1536))
        if PGVector is not None
        else mapped_column(Text)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    song_terms = relationship("SongTerm", back_populates="term")


class SongTerm(Base):
    __tablename__ = "song_terms"

    song_id: Mapped[int] = mapped_column(
        ForeignKey("songs.id"), primary_key=True
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id"), primary_key=True
    )
    presence_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # occurrences in this song

    song = relationship("Song", back_populates="song_terms")
    term = relationship("Term", back_populates="song_terms")

    __table_args__ = (UniqueConstraint("song_id", "term_id"),)


# ---------------------------------------------------------------------------
# Match tables  – one row per (song, video/track) candidate match
# ---------------------------------------------------------------------------


class YoutubeMatch(Base):
    __tablename__ = "youtube_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"))
    video_id: Mapped[str] = mapped_column(String(64))

    match_score: Mapped[float | None] = mapped_column(Float)
    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    song = relationship("Song", back_populates="youtube_matches")


class SpotifyMatch(Base):
    __tablename__ = "spotify_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"))
    track_id: Mapped[str] = mapped_column(String(64))

    match_score: Mapped[float | None] = mapped_column(
        Float
    )  # fuzzy similarity score
    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    song = relationship("Song", back_populates="spotify_matches")


# ---------------------------------------------------------------------------
# Cache tables – raw data from external APIs, minimise redundant network calls
# ---------------------------------------------------------------------------


class YoutubeCache(Base):
    """
    One row per YouTube video.  Populated by the stats scraper and used as the
    source of truth for fuzzy matching and view-count aggregation.
    """

    __tablename__ = "youtube_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    views: Mapped[int | None] = mapped_column(BigInteger)
    url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SpotifyCache(Base):
    __tablename__ = "spotify_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[str] = mapped_column(Text, unique=True)
    track_name: Mapped[str] = mapped_column(Text)
    album_name: Mapped[str | None] = mapped_column(Text)
    track_number: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    playcount: Mapped[int | None] = mapped_column(BigInteger)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
