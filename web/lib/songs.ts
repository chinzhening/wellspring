// web/lib/songs.ts

import { promises as fs } from "fs";
import path from "path";
import { Song } from "@/types/song";

const SONGS_DIR = path.join(process.cwd(), "..", "data", "songs");

interface RawSong {
  song_id: string;
  title: string;
  album: string;
  composer: string;
  lyricist: string;
  series: string;
  key: string;

  spotify_id: string | null;
  spotify_title: string | null;
  spotify_url: string | null;

  youtube_id: string | null;
  youtube_title: string | null;
  youtube_url: string | null;

  lyrics_clean: string;
  lyrics_tokenized: {
    version: number;
    lines: {
      line_number: number;
      text: string;
      tokens: {
        id: string | null;
        position: number;
        type: "hanzi" | "word";
        surface: string;
        lemma: string;
        traditional: string | null;
        simplified: string | null;
        pinyin: string | null;
      }[];
      render_groups: {
        term_id: string;
        term: string;
        start: number;
        end: number;
      }[];
    }[];
  };
}

export async function getAllSongs(): Promise<Song[]> {
  const files = await fs.readdir(SONGS_DIR);
  const songs: Song[] = [];

  for (const file of files) {
    if (file.endsWith(".json")) {
      const json = await fs.readFile(path.join(SONGS_DIR, file), "utf8");
      songs.push(parseSong(json));
    }
  }

  return songs;
}

export async function getSong(songId: string): Promise<Song> {
  const file = path.join(SONGS_DIR, `${songId}.json`);
  const json = await fs.readFile(file, "utf8");

  return parseSong(json);
}

export function parseSong(json: string): Song {
  const raw: RawSong = JSON.parse(json);

  return {
    songId: raw.song_id,
    title: raw.title,
    album: raw.album,
    composer: raw.composer,
    lyricist: raw.lyricist,
    series: raw.series,
    key: raw.key,

    spotify: raw.spotify_id
      ? {
          id: raw.spotify_id,
          title: raw.spotify_title!,
          url: raw.spotify_url!,
        }
      : null,

    youtube: raw.youtube_id
      ? {
          id: raw.youtube_id,
          title: raw.youtube_title!,
          url: raw.youtube_url!,
        }
      : null,

    lyrics: {
      clean: raw.lyrics_clean,
      tokenized: {
        version: raw.lyrics_tokenized.version,
        lines: raw.lyrics_tokenized.lines.map((line) => ({
          lineNumber: line.line_number,
          text: line.text,

          tokens: line.tokens.map((token) => ({
            id: token.id,
            position: token.position,
            type: token.type,
            surface: token.surface,
            lemma: token.lemma,
            traditional: token.traditional,
            simplified: token.simplified,
            pinyin: token.pinyin,
          })),

          renderGroups: line.render_groups.map((group) => ({
            termId: group.term_id,
            term: group.term,
            start: group.start,
            end: group.end,
          })),
        })),
      },
    },
  };
}