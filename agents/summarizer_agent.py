"""Adds a one-sentence summary to each item via the NVIDIA GLM-5.1 API."""
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

import config

# Each summary is an independent network call, so fan them out instead of
# waiting on them one by one. Capped low to stay polite to the API.
_MAX_WORKERS = 8

# Built lazily on first use so importing this module doesn't require the API
# key. That lets config.validate() report a missing key cleanly in main()
# instead of OpenAI() blowing up with a cryptic error at import time.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.NVIDIA_API_KEY, base_url=config.NVIDIA_BASE_URL
        )
    return _client


PROMPT = """Given this {source}:
Title: {title}
Description: {desc}

In ONE sentence, tell a developer what's notable here (for a release: what
changed and why it matters). Be specific and concrete. No hype, no preamble."""


def _summarize_one(item: dict) -> str:
    try:
        resp = _get_client().chat.completions.create(
            model=config.NVIDIA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        source=item["source"],
                        title=item["title"],
                        desc=item["desc"] or "(no description)",
                    ),
                }
            ],
            temperature=0.4,
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # don't let one bad call sink the whole digest
        print(f"[summarizer] {item['id']} failed: {exc}")
        return ""


def enrich(items: list[dict]) -> list[dict]:
    if not items:
        return items
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(items))) as pool:
        summaries = pool.map(_summarize_one, items)
    for item, summary in zip(items, summaries):
        item["why_it_matters"] = summary
    return items
