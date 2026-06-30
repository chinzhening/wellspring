import Link from "next/link";

import { ChineseCharacter } from "./ChineseCharacter";

import { Term } from "@/types/term";

interface TermCardProps {
  term: Term;
  traditionalMode: boolean;
  showPinyin: boolean;
}

export function TermCard({
  term,
  traditionalMode,
  showPinyin,
}: TermCardProps) {
  return (
    <Link
      href={`/terms/${term.id}`}
      className="
        block rounded-xl border border-border
        bg-surface p-4
        transition-colors
        hover:border-accent
        hover:bg-accent-light
      "
    >
      {/* Heading */}
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-semibold">
          <ChineseCharacter
            traditional={term.traditional}
            simplified={term.simplified}
            pinyin={term.pinyin}
            traditionalMode={traditionalMode}
            showPinyin={showPinyin}
          />
        </h2>

      </div>

      {/* Definition */}
      <p className="mt-3 text-sm">
        {term.definition}
      </p>

      {/* Footer */}
      <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {term.song_count} song{term.song_count === 1 ? "" : "s"}
        </span>
      </div>
    </Link>
  );
}