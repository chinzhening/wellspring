import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { GlassCard } from "@/components/GlassCard";
import { Song } from "@/types/song";

interface SongCardProps {
  song: Song;
  showSocialLinks?: boolean;
}

export function SongCard({ song, showSocialLinks = true }: SongCardProps) {
  return (
    <GlassCard className="flex h-full w-full max-w-150 flex-col p-5">
      <div className="flex h-full flex-col justify-between gap-6">
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 space-y-3">
              <Link href={`/songs/${song.songId}`} className="block">
                <h2 className="line-clamp-2 text-2xl font-semibold tracking-tight lg:text-3xl">
                  {song.title}
                </h2>
              </Link>

              <div className="flex flex-col gap-2 text-sm">
                {song.composer && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 font-medium text-foreground/85">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground/70">
                      Artist
                    </span>
                    <span className="min-w-0 truncate max-w-[16ch]">
                      {song.composer}
                    </span>
                  </span>
                )}

                {song.album && (
                  <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1 font-medium text-foreground/85">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground/70">
                      Album
                    </span>
                    <span className="min-w-0 truncate max-w-[16ch]">
                      {song.album}
                    </span>
                  </span>
                )}
              </div>
            </div>

            <Link
              href={`/songs/${song.songId}`}
              className="shrink-0 p-2 text-foreground/80"
              aria-label={`Open ${song.title}`}
            >
              <ChevronRight size={18} />
            </Link>
          </div>

          {song.lyrics.clean && (
            <p className="line-clamp-4 whitespace-pre-line text-sm leading-6 text-muted-foreground/85">
              {song.lyrics.clean}
            </p>
          )}
        </div>

        <div className="space-y-3">
          {showSocialLinks && (
            <div className="flex flex-wrap gap-2 text-sm">
              {song.spotify && (
                <a
                  href={song.spotify.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-full border border-green-500/25 bg-green-500/12 px-3 py-1 font-medium text-green-700 backdrop-blur-md dark:text-green-400"
                >
                  Spotify
                </a>
              )}

              {song.youtube && (
                <a
                  href={song.youtube.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-full border border-red-500/25 bg-red-500/12 px-3 py-1 font-medium text-red-700 backdrop-blur-md dark:text-red-400"
                >
                  YouTube
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
