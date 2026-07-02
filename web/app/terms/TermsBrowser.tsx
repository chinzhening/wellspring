"use client";

import { useState } from "react";

import { Term } from "@/types/term";
import { TermCard } from "@/components/TermCard";

interface TermsBrowserProps {
  grouped: Record<1 | 2 | 3, Term[]>;
}

const TIERS = [1, 2, 3] as const;

export default function TermsBrowser({ grouped }: TermsBrowserProps) {
  const [selectedTier, setSelectedTier] = useState<(typeof TIERS)[number]>(1);

  return (
    <div className="space-y-6">
      <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground/70">
        Terms
      </p>
      <div className="flex gap-1">
        {TIERS.map((tier) => (
          <button
            key={tier}
            type="button"
            onClick={() => setSelectedTier(tier)}
            className={`
              rounded-lg px-2 lg:px-4 py-2 text-sm font-medium transition-colors text-nowrap
              ${
                selectedTier === tier
                  ? "bg-accent text-accent-foreground"
                  : "bg-surface-secondary hover:bg-accent-light"
              }
            `}
          >
            Tier {tier}
            <span className="ml-2 text-xs opacity-70">
              ({grouped[tier].length})
            </span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,280px))] justify-center gap-4">
        {grouped[selectedTier].map((term) => (
          <TermCard key={term.id} term={term} showPinyin={true} />
        ))}
      </div>
    </div>
  );
}
