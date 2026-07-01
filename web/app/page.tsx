import { getSong } from "@/lib/songs";
import Link from "next/link";

export default async function Page() {
  const songIds = [
    "cca62e147ad920c0", // 將天敞開
    "577144d212900b3b", // 不需要理由
    "e774ffa93decbd0d", // 讚美中信心不斷升起
    "5428a263652cb34a", // Stay
    "e8ad37fac4ab8b4f", // 能不能
    "af409a26d4b37882", // Yes, Amen (是祢的應許)
    "edf5e4752d9878e8", // 雨過會天晴
    "11d82b73d864d96c", // 照亮我生命的光
    "b1c80a1250556eff", // 這是我們的敬拜
    "474754172216102c", // 為榮耀的創造
    "28d76f7d6e3a6d68", // 是祢耶稣
    "119c41e45ad3a46f", // 就是現在
    "5dee4e0457385ca8", // 我已經與基督同釘十架
    "eab9b0f24458c945", // 定睛在耶穌身上
    "741f01f70b74ce45", // 從我興起
  ];

  const songs = await Promise.all(songIds.map((id) => getSong(id)));

  return (
    <main className="mx-auto max-w-3xl px-6 pt-8 pb-32 mb-32">
      <h1 className="mb-8 text-3xl font-bold">Songs</h1>

      <div className="space-y-4">
        {songs.map((song) => (
          <Link
            key={song.songId}
            href={`/songs/${song.songId}`}
            className="block rounded-xl border border-border bg-surface p-5 transition-colors hover:border-accent hover:bg-surface-secondary"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-2xl lg:text-2xl font-semibold">
                  {song.title}
                </h2>

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {song.composer && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-secondary px-3 py-1 text-xs font-medium text-muted-foreground">
                      <span className="text-[10px] uppercase tracking-wide text-muted-foreground/70">
                        Artist
                      </span>
                      {song.composer}
                    </span>
                  )}

                  {song.album && (
                    <span className="hidden md:inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-secondary px-3 py-1 text-xs font-medium text-muted-foreground">
                      <span className="text-[10px] uppercase tracking-wide text-muted-foreground/70">
                        Album
                      </span>
                      {song.album}
                    </span>
                  )}
                </div>

                {song.lyrics.clean && (
                  <p className="mt-3 line-clamp-3 whitespace-pre-line text-sm text-muted-foreground">
                    {song.lyrics.clean}
                  </p>
                )}
              </div>

              <span className="shrink-0 pt-1 text-sm text-muted-foreground">
                →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}