"use client";

import { ChineseCharacter } from "@/components/ChineseCharacter";
import { Term as TermType } from "@/types/term";

type Props = {
  term: TermType;
};

export default function Term({ term }: Props) {
  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-12">
      <header className="space-y-4 text-center">
        <ChineseCharacter
          traditional={term.traditional}
          simplified={term.simplified}
          pinyin={term.pinyin}
          showPinyin={true}
        />

        <div>
          <p className="mt-2 text-xl">{term.definition}</p>
        </div>
      </header>

      {term.context && (
        <section className="rounded-xl border p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Context
          </h2>

          <p className="text-2xl leading-relaxed">{term.context}</p>
        </section>
      )}

      {term.explanation && (
        <section className="rounded-xl border p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Explanation
          </h2>

          <p className="leading-8">{term.explanation}</p>
        </section>
      )}

      <section className="flex gap-6 rounded-xl border p-6 text-sm text-muted-foreground">
        <div>
          <div className="font-medium text-foreground">Occurrences</div>
          <div>
            {term.song_count} song{term.song_count !== 1 && "s"}
          </div>
        </div>

        <div>
          <div className="font-medium text-foreground">Difficulty</div>
          <div>Tier {term.tier}</div>
        </div>
      </section>
    </main>
  );
}
