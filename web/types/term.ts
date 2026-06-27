export type Term = {
  id: string;
  traditional: string;
  simplified: string;
  pinyin: string;
  script: "traditional" | "simplified";
  definition: string;
  context: string;
  explanation: string;
  song_count: number;
  score: number;
  tier: number;
};
