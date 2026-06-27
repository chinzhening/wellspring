export const dynamic = "force-static";

import { notFound } from "next/navigation";
import { getTermsForSong } from "@/lib/terms";
import { getAllSongs, getSong } from "@/lib/songs";
import Song from "@/components/Song";

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
  const terms = await getTermsForSong(songId);

  if (!song) {  
    notFound();
  }

  return <Song song={song} terms={terms} />;
}