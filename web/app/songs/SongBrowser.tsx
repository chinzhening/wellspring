"use client";

import { useState } from "react";

import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";

import { SongCard } from "@/components/SongCard";
import { Song } from "@/types/song";

interface SongBrowserProps {
  songs: Song[];
  pageSize: number;
}

function getPageWindow(page: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const start = Math.max(2, Math.min(page - 1, totalPages - 3));
  const end = Math.min(totalPages - 1, start + 2);
  const adjustedStart = Math.max(2, end - 2);

  return [1, adjustedStart, adjustedStart + 1, end, totalPages].filter(
    (value, index, values) => values.indexOf(value) === index,
  );
}

export default function SongBrowser({ songs, pageSize }: SongBrowserProps) {
  const totalSongs = songs.length;
  const totalPages = Math.max(1, Math.ceil(totalSongs / pageSize));
  const [page, setPage] = useState(1);

  const firstSongNumber = totalSongs === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastSongNumber = Math.min(totalSongs, firstSongNumber + pageSize - 1);
  const pageWindow = getPageWindow(page, totalPages);
  const visibleSongs = songs.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground/70">
            Library
          </p>
          <h1 className="text-3xl font-bold lg:text-4xl">Songs</h1>
          <p className="text-sm text-muted-foreground">
            Showing {firstSongNumber}-{lastSongNumber} of {totalSongs}
          </p>
        </div>

        <p className="text-sm text-muted-foreground">
          Page {page} of {totalPages}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleSongs.map((song) => (
          <SongCard key={song.songId} song={song} showSocialLinks={false} />
        ))}
      </div>

      {totalPages > 1 && (
        <nav className="flex flex-wrap items-center justify-center gap-2 rounded-full p-2">
          <button
            type="button"
            onClick={() =>
              setPage((currentPage) => Math.max(1, currentPage - 1))
            }
            disabled={page === 1}
            className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium cursor-pointer ${
              page === 1
                ? "cursor-not-allowed text-muted-foreground/40"
                : "text-foreground/85"
            }`}
          >
            <ChevronLeft size={16} />
          </button>

          {pageWindow.map((pageNumber, index) => {
            const previousPage = pageWindow[index - 1];
            const showGap = index > 0 && previousPage !== pageNumber - 1;

            return (
              <div key={pageNumber} className="flex items-center gap-2">
                {showGap && (
                  <MoreHorizontal
                    size={16}
                    className="text-muted-foreground/60"
                  />
                )}
                {pageNumber === page ? (
                  <span className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground">
                    {pageNumber}
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => setPage(pageNumber)}
                    className="rounded-full px-4 py-2 text-sm font-medium text-foreground/80"
                  >
                    {pageNumber}
                  </button>
                )}
              </div>
            );
          })}

          <button
            type="button"
            onClick={() =>
              setPage((currentPage) => Math.min(totalPages, currentPage + 1))
            }
            disabled={page === totalPages}
            className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium cursor-pointer ${
              page === totalPages
                ? "cursor-not-allowed text-muted-foreground/40"
                : "text-foreground/85"
            }`}
          >
            <ChevronRight size={16} />
          </button>
        </nav>
      )}
    </div>
  );
}
