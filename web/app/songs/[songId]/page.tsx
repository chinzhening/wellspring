export const dynamic = "force-static";

import { notFound } from "next/navigation";
import { getTermsForSong } from "@/lib/terms";
import { getAllSongs, getSong } from "@/lib/songs";

import { Term } from "@/types/term";
import { TermCard } from "@/components/TermCard";
import { GlassCard } from "@/components/GlassCard";
import { Lyric } from "@/components/Lyric";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";

export async function generateStaticParams() {
  const songs = await getAllSongs();

  return songs.map((song) => ({
    songId: song.songId,
  }));
}

export default async function Page({
  params,
}: {
  params: Promise<{ songId: string }>;
}) {
  const { songId } = await params;

  const song = await getSong(songId);
  const terms: Term[] = await getTermsForSong(songId);

  if (!song) {  
    notFound();
  }

  return (
    <div className="
      mx-auto my-10
      flex flex-col min-h-screen
      max-w-3xl lg:max-w-5xl
      px-8 lg:px-16
      gap-4 lg:gap-8"
    >
      {/* Navigation Back */}
      <Link
        href={`/songs`}
        className="border-border border bg-surface p-3 rounded-full max-w-11 hover:border-accent hover:bg-surface-secondary transition-colors"
      >
        <span className="text-sm text-muted-foreground">
          <ChevronLeft size={20} />
        </span>
      </Link>
      

      {/* Song Metadata */}
      <GlassCard className="flex w-full max-w-100 aspect-square p-6">
        <div className="flex h-full w-full flex-col justify-between gap-6">
          <div className="space-y-4">
            <h1 className="max-w-[12ch] text-4xl font-bold leading-tight tracking-tight lg:text-5xl">
              {song.title}
            </h1>
          </div>

          <div className="flex flex-col gap-5">
            {/* Left: Metadata */}
            <div className="flex flex-wrap gap-3 text-base lg:text-lg">
              {song.composer && (
                <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 font-medium text-foreground/85 backdrop-blur-md">
                  <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground/70">
                    Artist
                  </span>
                  <span className="min-w-0 truncate max-w-[18ch]">
                    {song.composer}
                  </span>
                </span>
              )}

              {song.album && (
                <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 font-medium text-foreground/85 backdrop-blur-md">
                  <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground/70">
                    Album
                  </span>
                  <span className="min-w-0 truncate max-w-[18ch]">
                    {song.album}
                  </span>
                </span>
              )}
            </div>

            {/* Right: External links */}
            <div className="flex flex-wrap items-center gap-3 md:justify-end text-md">
              {song.spotify && (
                <a
                  href={song.spotify.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-full border border-green-500/25 bg-green-500/12 px-4 py-2 font-medium text-green-700 backdrop-blur-md dark:text-green-400"
                >
                  Spotify
                </a>
              )}

              {song.youtube && (
                <a
                  href={song.youtube.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-full border border-red-500/25 bg-red-500/12 px-4 py-2 font-medium text-red-700 backdrop-blur-md dark:text-red-400"
                >
                  YouTube
                </a>
              )}
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Lyrics */}
      <Lyric
        lyrics={song.lyrics.tokenized}
        terms={terms}
        showPinyin={true}
      />
      
      {/* Term */}
      <div className="mt-3 border-t border-border pt-6">
        <h2 className="my-4"> <span className="font-bold text-2xl">Terms</span> <span className="ml-1 text-lg opacity-70"> ({terms.length})</span> </h2>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,280px))] gap-4">
          {terms.map((term) => (
            <TermCard key={term.id} term={term} showPinyin={true} />
            )
          )}  
        </div>
        
      </div>
    </div>
  );
}