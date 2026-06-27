// lib/tone.ts

const TONE_MARKS: Record<string, readonly string[]> = {
  a: ["ā", "á", "ǎ", "à"],
  e: ["ē", "é", "ě", "è"],
  i: ["ī", "í", "ǐ", "ì"],
  o: ["ō", "ó", "ǒ", "ò"],
  u: ["ū", "ú", "ǔ", "ù"],
  ü: ["ǖ", "ǘ", "ǚ", "ǜ"],
};

const VOWELS = "aeiouü";

/**
 * Converts a single numbered pinyin syllable to tone marks.
 *
 * ni3   -> nǐ
 * hao3  -> hǎo
 * zhong1 -> zhōng
 * lv4   -> lǜ
 * lu:4  -> lǜ
 */
export function toneSyllable(input: string): string {
  const match = input.match(/^(.+?)([0-5])$/);

  if (!match) {
    return input;
  }

  const [, base, toneStr] = match;
  const tone = Number(toneStr);

  const markedBase = base
    .replace(/u:/g, "ü")
    .replace(/v/g, "ü");

  // Neutral tone
  if (tone === 0 || tone === 5) {
    return markedBase;
  }

  let index = -1;

  // Priority: a > e > ou > last vowel
  if ((index = markedBase.indexOf("a")) !== -1) {
    // use a
  } else if ((index = markedBase.indexOf("e")) !== -1) {
    // use e
  } else if (markedBase.includes("ou")) {
    index = markedBase.indexOf("o");
  } else {
    for (let i = markedBase.length - 1; i >= 0; i--) {
      if (VOWELS.includes(markedBase[i])) {
        index = i;
        break;
      }
    }
  }

  if (index === -1) {
    return markedBase; // No vowel found, return as is
  }

  const vowel = markedBase[index] as keyof typeof TONE_MARKS;
  const marked = TONE_MARKS[vowel][tone - 1];

  return markedBase.slice(0, index) + marked + markedBase.slice(index + 1);
}

/**
 * Converts all numbered pinyin syllables in a string.
 *
 * "ni3 hao3 ma5"
 * -> "nǐ hǎo ma"
 */
export function toneText(text: string): string {
  return text.replace(
    /[A-Za-züÜv:]+[0-5]/g,
    (match) => toneSyllable(match)
  );
}

/**
 * Separates pinyin syllables with spaces.
 *
 * "ni3 hao3 ma5"
 * -> "ni3 hao3 ma5"
 */
export function separatePinyin(pinyin: string): string {
  return pinyin
    .trim()
    .replace(/([1-5])(?=[a-z])/gi, "$1 ");
}