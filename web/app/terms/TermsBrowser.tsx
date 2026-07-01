"use client";

import { useState } from "react";

import { Term } from "@/types/term";
import { TermCard } from "@/components/TermCard";

interface TermsBrowserProps {
  grouped: Record<1 | 2 | 3, Term[]>;
}

const TIERS = [1, 2, 3] as const;

export default function TermsBrowser({
  grouped,
}: TermsBrowserProps) {
  const [selectedTier, setSelectedTier] = useState<(typeof TIERS)[number]>(1);

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        {TIERS.map((tier) => (
          <button
            key={tier}
            type="button"
            onClick={() => setSelectedTier(tier)}
            className={`
              rounded-lg px-4 py-2 text-sm font-medium transition-colors
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

        <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,320px))] justify-center gap-4">
        {grouped[selectedTier].map((term) => (
            <TermCard
            key={term.id}
            term={term}
            showPinyin={true}
            />
        ))}
        </div>
    </div>
  );
}