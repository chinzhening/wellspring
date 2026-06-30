import Link from "next/link";

import { toneText } from "@/lib/pinyin";

import { ChineseCharacter } from "./ChineseCharacter";
import { Word } from "./Word";
import { RenderGroup as RenderGroupType, Token } from "@/types/song";
import { Term } from "@/types/term";

interface RenderGroupProps {
  group: RenderGroupType;
  tokens: Token[];
  traditionalMode: boolean;
  showPinyin: boolean;
  term: Term;
}

export function RenderGroup({
  group,
  tokens,
  traditionalMode,
  showPinyin,
  term,
}: RenderGroupProps) {
  return (
    <div className="group relative inline-flex my-1">
      <Link
        href={`/terms/${group.termId}`}
        className="
          flex items-end gap-1
          rounded-md border border-border
          bg-surface-secondary
          px-1 py-1
          transition-colors
          hover:border-accent
          hover:bg-accent-light
        "
      >
        {tokens.map((token, index) =>
          token.type === "hanzi" ? (
            <ChineseCharacter
              key={token.id ?? index}
              simplified={token.simplified ?? token.surface}
              traditional={token.traditional ?? token.surface}
              pinyin={token.pinyin ?? ""}
              traditionalMode={traditionalMode}
              showPinyin={showPinyin}
            />
          ) : (
            <Word
              key={token.id ?? index}
              surface={token.surface}
            />
          )
        )}
      </Link>

      <div
        className="
          pointer-events-none absolute left-1/2 top-full z-50 mt-2
          hidden w-80 -translate-x-1/2
          rounded-lg border border-border
          bg-surface
          p-2 lg:p-4
          shadow-xl
          group-hover:block
        "
      >
        <div className="flex items-baseline justify-between gap-3">
          <div className="text-xl font-semibold">
            {traditionalMode ? term.traditional : term.simplified}
          </div>

          <div className="font-mono text-sm text-muted-foreground">
            {toneText(term.pinyin)}
          </div>
        </div>

        <p className="mt-2 text-sm">{term.definition}</p>

        {term.context && (
          <div className="mt-3 border-t border-border pt-3">
            <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Context
            </div>

            <p className="text-sm italic">{term.context}</p>
          </div>
        )}

        {term.song_count > 0 && (
          <div className="mt-3 text-xs text-muted-foreground">
            Appears in {term.song_count} song
            {term.song_count === 1 ? "" : "s"}
          </div>
        )}
      </div>
    </div>
  );
}