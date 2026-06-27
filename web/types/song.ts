export interface Song {
  songId: string;
  title: string;
  album: string;
  composer: string;
  lyricist: string;
  series: string;
  key: string;

  spotify?: MediaLink | null;
  youtube?: MediaLink | null;

  lyrics: {
    clean: string;
    tokenized: Lyrics;
  };
}

export interface MediaLink {
  id: string;
  title: string;
  url: string;
}

export interface Lyrics {
  version: number;
  lines: LyricLine[];
}

export interface LyricLine {
  lineNumber: number;
  text: string;
  tokens: Token[];
  renderGroups: RenderGroup[];
}

export interface Token {
  id: string | null;
  position: number;

  type: "hanzi" | "word";

  surface: string;
  lemma: string;

  traditional: string | null;
  simplified: string | null;
  pinyin: string | null;
}

export interface RenderGroup {
  termId: string;
  term: string;

  /** Inclusive token index */
  start: number;

  /** Inclusive token index */
  end: number;
}