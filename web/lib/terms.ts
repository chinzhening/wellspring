import { promises as fs } from "fs";
import path from "path";
import { Term } from "@/types/term";

export async function getTerm(termId: string): Promise<Term | null> {
  try {
    const filePath = path.join(
      process.cwd(),
      "..",
      "data",
      "terms",
      `${termId}.json`
    );

    const file = await fs.readFile(filePath, "utf8");
    return JSON.parse(file) as Term;
  } catch {
    return null;
  }
}

type SongTermIndexEntry = {
  term_id: string;
  song_id: string;
}

type TermIndexEntry = {
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

export async function getAllTerms(): Promise<TermIndexEntry[]> {
  const index = await fs.readFile(
    path.join(process.cwd(), "..", "data", "index", "term.json"),
    "utf8"
  );
  return JSON.parse(index) as TermIndexEntry[];
}

export async function getTermsForSong(songId: string): Promise<Term[]> {
  const index = await fs.readFile(
    path.join(process.cwd(), "..", "data", "index", "song_term.json"),
    "utf8"
  );
  const indexData = JSON.parse(index) as SongTermIndexEntry[];

  const termIds = indexData
    .filter((entry) => entry.song_id === songId)
    .map((entry) => entry.term_id);
  
  const terms: Term[] = await Promise.all(
    termIds.map(async (termId) => {
      const filePath = path.join(
        process.cwd(),
        "..",
        "data",
        "terms",
      `${termId}.json`
    );
    const file = await fs.readFile(filePath, "utf8");
    return JSON.parse(file) as Term;
  })
);

  return terms;
}