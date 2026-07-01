"use client";

import { useState } from "react";
import { Lyric } from "@/components/Lyric";
import { Song as SongType } from "@/types/song";
import { Term } from "@/types/term";

interface SongProps {
  song: SongType
  terms: Term[];
}

export default function Song({ song, terms }: SongProps) {
  const [traditionalMode, setTraditionalMode] = useState(false);
  const showPinyin = true;

  return (
    <main className="
      mx-auto mt-10
      flex flex-col min-h-screen
      max-w-3xl lg:max-w-5xl
      px-8 lg:px-16
      gap-4 lg:gap-8
      mb-64"
    >
      <header className="space-y-4">
        <h1 className="text-4xl lg:text-5xl font-bold">{song.title}</h1>

        <div className="grid gap-4 md:grid-cols-2">
          {/* Left: Metadata */}
          <div className="
            flex flex-wrap
            items-center gap-2
            text-lg lg:text-xl"
          >
            {song.composer && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-secondary px-3 py-1 font-medium text-muted-foreground">
                <span className="text-lg uppercase tracking-wide text-muted-foreground/70">
                  Artist
                </span>
                <span className="truncate min-w-0 max-w-[16ch]">
                  {song.composer}
                </span>
              </span>
            )}

            {song.album && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-secondary px-3 py-1 font-medium text-muted-foreground">
                <span className="text-lg uppercase tracking-wide text-muted-foreground/70">
                  Album
                </span>
                <span className="truncate min-w-0 max-w-[16ch]">
                  {song.album}
                </span>
              </span>
            )}
          </div>

          {/* Right: External links */}
          <div className="flex flex-wrap items-center gap-2 md:justify-end text-md">
            {song.spotify && (
              <a
                href={song.spotify.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full border border-green-600/30 bg-green-500/10 px-3 py-1 font-medium text-green-700 transition-colors hover:bg-green-500/20 dark:text-green-400"
              >
                Spotify
              </a>
            )}

            {song.youtube && (
              <a
                href={song.youtube.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full border border-red-600/30 bg-red-500/10 px-3 py-1 font-medium text-red-700 transition-colors hover:bg-red-500/20 dark:text-red-400"
              >
                YouTube
              </a>
            )}
          </div>
        </div>
      </header>

      <div className="flex gap-3">
        <button
          onClick={() => setTraditionalMode((v) => !v)}
          className="rounded-md border border-border bg-surface px-4 py-2"
        >
          {traditionalMode ? "Traditional" : "Simplified"}
        </button>
      </div>

      <Lyric
        lyrics={song.lyrics.tokenized}
        terms={terms}
        traditionalMode={traditionalMode}
        showPinyin={showPinyin}
      />
    </main>
  );
}