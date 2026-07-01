import { Lyrics, RenderGroup } from "@/types/song";
import { LyricLine } from "./LyricLine";
import { Term } from "@/types/term";

interface LyricProps {
  lyrics: Lyrics;
  terms: Term[];
  showPinyin: boolean;
}

export function Lyric({
  lyrics,
  terms,
  showPinyin,
}: LyricProps) {

  const seenTerms = new Set<string>();
  const lineRenderGroups = new Map<number, RenderGroup[]>();

  for (const line of lyrics.lines) {
    for (const group of line.renderGroups) {
      if (seenTerms.has(group.termId)) continue;
      seenTerms.add(group.termId);

      let groups = lineRenderGroups.get(line.lineNumber);
      if (!groups) {
        groups = [];
        lineRenderGroups.set(line.lineNumber, groups);
      }

      groups.push(group);
    }
  }

  return (
    <div className="flex flex-col gap-3 lg:gap-6">
      {lyrics.lines.map((line) => (
        <LyricLine
          key={line.lineNumber}
          terms={terms}
          line={line}
          groups={lineRenderGroups.get(line.lineNumber) ?? []}
          showPinyin={showPinyin}
        />
      ))}
    </div>
  );
}