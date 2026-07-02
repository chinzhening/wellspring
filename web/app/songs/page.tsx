export const dynamic = "force-static";

import { getAllSongs } from "@/lib/songs";
import SongBrowser from "./SongBrowser";

const PAGE_SIZE = 12;

export default async function Page() {
  const songs = (await getAllSongs()).sort((left, right) =>
    left.title.localeCompare(right.title, "en", { sensitivity: "base" }),
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 lg:px-8">
      <SongBrowser songs={songs} pageSize={PAGE_SIZE} />
    </div>
  );
}