import {
  LyricLine as LyricLineType,
  RenderGroup as RenderGroupType,
} from "@/types/song";
import { ChineseCharacter } from "./ChineseCharacter";
import { Word } from "./Word";
import { RenderGroup } from "./RenderGroup";
import { Term } from "@/types/term";

interface LyricLineProps {
  line: LyricLineType;
  terms: Term[];
  groups: RenderGroupType[];
  showPinyin: boolean;
}

export function LyricLine({ line, terms, groups, showPinyin }: LyricLineProps) {
  const children = [];

  let i = 0;

  while (i < line.tokens.length) {
    const group = groups.find((g) => g.start === i);

    if (group) {
      children.push(
        <RenderGroup
          key={group.termId}
          group={group}
          tokens={line.tokens.slice(group.start, group.end + 1)}
          showPinyin={showPinyin}
          term={
            terms.find((t) => t.id === group.termId) ?? {
              id: group.termId,
              traditional: "",
              simplified: "",
              pinyin: "",
              script: "traditional",
              definition: "Definition not found.",
              context: "",
              explanation: "",
              song_count: 0,
              score: 0,
              tier: 0,
            }
          }
        />,
      );

      i = group.end + 1;
      continue;
    }

    const token = line.tokens[i];

    children.push(
      token.type === "hanzi" ? (
        <ChineseCharacter
          key={token.id ?? i}
          simplified={token.simplified ?? token.surface}
          traditional={token.traditional ?? token.surface}
          pinyin={token.pinyin ?? ""}
          showPinyin={showPinyin}
        />
      ) : (
        <Word key={token.id ?? i} surface={token.surface} />
      ),
    );

    i++;
  }

  return (
    <div
      className="
      flex flex-wrap items-baseline-last
      gap-x-1 lg:gap-x-2"
    >
      {children}
    </div>
  );
}
