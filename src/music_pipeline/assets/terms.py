import hashlib
import time
from typing import Literal

import opencc
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from pydantic import BaseModel, Field, RootModel, ValidationError
from pypinyin import Style, lazy_pinyin

from ..resources import GeminiResource

batch_size = 10
model = "gemini-3.1-flash-lite"
retry_attempts = 3
retry_delay = 15
prompt = """
You are a Chinese Christian worship music expert.
Extract important or potentially difficult *chinese* terms from the lyrics below that a
non-native singer may struggle to understand.

Extract terms that are:
- Theological or doctrinal (e.g. 救恩, 恩典)
- Worship-specific phrases
- Classical, literary, or archaic Chinese expressions

Rules:
- Extract the term exactly as it appears in the lyrics, do not convert between scripts.
- Break compound phrases into their smallest meaningful units where possible (e.g. "恩典慈愛" → "恩典", "慈愛").
- Prefer 2-4 character terms but do not truncate meaningful phrases.
- Set `script` to "traditional", "simplified", or "unknown".
- `definition` must be ≤12 words, worship-context aware, in English.
- `context` must be the exact line from the lyrics containing the term.
- `explanation` is optional — use it for nuance, theological significance, or common mistranslations.
"""
# Response Schema


class TermCandidate(BaseModel):
    term: str = Field(
        description="Chinese term exactly as it appears in the lyrics."
    )
    script: Literal["traditional", "simplified", "unknown"]
    definition: str = Field(
        description="Concise English definition, ≤12 words, worship-context aware."
    )
    context: str = Field(
        default="",
        description="Exact line from the lyrics containing this term.",
    )
    explanation: str = Field(
        default="",
        description="Optional notes on nuance or theological significance.",
    )


class TermCandidates(RootModel[list[TermCandidate]]):
    pass


@asset(group_name="enrichment")
def song_terms_raw(
    context: AssetExecutionContext, gemini: GeminiResource, sop_songs_normalized
) -> MaterializeResult:
    client = gemini.client()

    terms = []
    terms_seen = set()

    n = len(sop_songs_normalized)
    total_batches = (n + batch_size - 1) // batch_size

    for i in range(0, n, batch_size):
        batch = sop_songs_normalized[i : i + batch_size]
        batch_num = i // batch_size + 1

        context.log.info(f"Processing batch {batch_num}/{total_batches} ...")

        time.sleep(5)

        term_candidates = extract_batch(context, client, batch)

        if not term_candidates:
            context.log.warning(
                f"Batch {batch_num} returned no term candidates."
            )
            continue

        context.log.info(
            f"Batch {batch_num} returned {len(term_candidates)} term candidates."
        )

        # Deduplicate terms across batches
        for term in term_candidates:
            if term["term"] not in terms_seen:
                terms.append(term)
                terms_seen.add(term["term"])

    return MaterializeResult(
        value=terms,
        metadata={
            "num_records": len(terms),
            "samples": MetadataValue.json(terms[:5]),
        },
    )


def extract_batch(context: AssetExecutionContext, client, batch) -> list:
    for a in range(retry_attempts):
        try:
            data = "\n\n".join(
                f"Song ID: {song['song_id']}\nLyrics:\n{song['lyrics_clean']}"
                for song in batch
            )
            contents = f"{prompt}\n\n{data}"
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": {
                        "type": "array",
                        "items": TermCandidate.model_json_schema(),
                    },
                },
            )

            if response.text is None:
                context.log.warning("Gemini returned empty response")
                continue

            try:
                raw = TermCandidates.model_validate_json(response.text)
                return raw.model_dump()
            except ValidationError as e:
                context.log.error(
                    f"Failed to parse Gemini response {response.text}: {e}"
                )
                continue
        except Exception as e:
            context.log.warning(f"Attempt {a + 1} failed: {e}")
            if a < retry_attempts - 1:
                context.log.info(f"Retrying after {retry_delay} seconds...")
                time.sleep(retry_delay)

    context.log.error("All retry attempts exhausted for batch.")
    return []


@asset(group_name="enrichment")
def song_terms_normalized(
    context: AssetExecutionContext, song_terms_raw
) -> MaterializeResult:
    normalized_terms = []
    for term in song_terms_raw:
        term_raw = term.get("term", "")
        term_id = _generate_term_id(term_raw.strip())

        script = term.get("script", "unknown")

        if script == "traditional":
            traditional = term_raw
            simplified = _traditional_to_simplified(term_raw)
        elif script == "simplified":
            traditional = _simplified_to_traditional(term_raw)
            simplified = term_raw
        else:
            context.log.warning(
                "Unknown script '%s' for term '%s'",
                script,
                term_raw,
            )
            continue

        pinyin = _chinese_to_pinyin(traditional)

        normalized_term = {
            "id": term_id,
            "traditional": traditional,
            "simplified": simplified,
            "pinyin": pinyin,
            "script": script,
            "definition": term["definition"],
            "context": term["context"],
            "explanation": term.get("explanation", ""),
        }
        normalized_terms.append(normalized_term)

    return MaterializeResult(
        value=normalized_terms,
        metadata={
            "num_records": len(normalized_terms),
            "samples": MetadataValue.json(normalized_terms[:5]),
        },
    )


# Helper Functions

_T2S = opencc.OpenCC("t2s")
_S2T = opencc.OpenCC("s2t")


def _generate_term_id(term: str) -> str:
    return hashlib.sha1(term.encode()).hexdigest()[:16]


def _traditional_to_simplified(term: str) -> str:
    return _T2S.convert(term)


def _simplified_to_traditional(term: str) -> str:
    return _S2T.convert(term)


def _chinese_to_pinyin(term: str) -> str:
    return "".join(
        lazy_pinyin(
            term,
            style=Style.TONE3,
        )
    )
