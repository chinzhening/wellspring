import re

import ahocorasick
from dagster import MaterializeResult, MetadataValue, asset
from opencc import OpenCC
from pypinyin import Style, lazy_pinyin


@asset(group_name="enrichment")
def song_lyrics_tokenized(
    sop_songs_normalized, song_terms_normalized
) -> MaterializeResult:
    # Initialize Aho-Corasick automaton for term matching
    A = ahocorasick.Automaton()

    for term in song_terms_normalized:
        term_id = term["id"]
        traditional = term["traditional"]
        A.add_word(traditional, {"term_id": term_id, "term": traditional})

    A.make_automaton()

    tokenized_lyrics = []

    for song in sop_songs_normalized:
        lyrics_tokenized = tokenize_lyrics(
            song.get("lyrics_clean", ""),
            song["song_id"],
            automaton=A,
        )
        tokenized_lyrics.append(
            {
                "song_id": song["song_id"],
                "lyrics_clean": song.get("lyrics_clean", ""),
                "lyrics_tokenized": lyrics_tokenized,
            }
        )

    return MaterializeResult(
        value=tokenized_lyrics,
        metadata={
            "songs_processed": len(tokenized_lyrics),
            "samples": MetadataValue.json(tokenized_lyrics[:1]),
        },
    )


cc_t2s = OpenCC("t2s")
cc_s2t = OpenCC("s2t")


def is_chinese(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def token_to_json(
    token: str,
    position: int,
    song_id: str,
    line_number: int,
) -> dict:
    token_id = f"{song_id}:{line_number}:{position}"

    if is_chinese(token):
        simplified = cc_t2s.convert(token)
        traditional = cc_s2t.convert(token)

        return {
            "id": token_id,
            "position": position,
            "type": "hanzi",
            "surface": token,
            "lemma": simplified,
            "traditional": traditional,
            "simplified": simplified,
            "pinyin": " ".join(
                lazy_pinyin(
                    simplified,
                    style=Style.TONE3,  # ai4, wo3, ni3
                )
            ),
        }

    if token.isdigit():
        return {
            "position": position,
            "type": "number",
            "surface": token,
            "lemma": token,
        }

    return {
        "position": position,
        "type": "word",
        "surface": token,
        "lemma": token.lower(),
    }


TOKEN_PATTERN = re.compile(
    r"(\s+|[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[\u4e00-\u9fff]+|.)"
)


def tokenize_lyrics(
    lyrics_clean: str, song_id: str, automaton: ahocorasick.Automaton
) -> dict:
    lines = []

    for line_number, line in enumerate(lyrics_clean.splitlines(), start=1):
        line = line.strip()

        if not line:
            continue

        parts = TOKEN_PATTERN.findall(line)
        raw_tokens = []

        for part in parts:
            if is_chinese(part):
                raw_tokens.extend(list(part))
            else:
                raw_tokens.append(part)

        tokens = [
            token_to_json(token, pos, song_id, line_number)
            for pos, token in enumerate(raw_tokens)
        ]

        matches = []
        for end_idx, value in automaton.iter(line):
            term = value["term"]
            term_id = value["term_id"]
            start_idx = end_idx - len(term) + 1
            matches.append(
                {
                    "term_id": term_id,
                    "term": term,
                    "start": start_idx,
                    "end": end_idx,
                }
            )

        matches.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
        groups = []
        last_end = -1
        for match in matches:
            if match["start"] >= last_end:
                groups.append(match)
                last_end = match["end"]

        lines.append(
            {
                "line_number": line_number,
                "text": line,
                "tokens": tokens,
                "render_groups": groups,
            }
        )

    return {
        "version": 1,
        "lines": lines,
    }
