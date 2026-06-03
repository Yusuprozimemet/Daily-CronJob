"""Adds a one-sentence "why it matters" note to each item via NVIDIA NIM.

Summaries are batched: instead of one API call per item (which tripped NIM's
free-tier rate limit and left many items with empty summaries), all items in a
chunk go in a single prompt and the model returns one numbered line each. ~31
items become 2-3 calls per run.
"""
import re
import time

from openai import OpenAI, RateLimitError

import config

# How many items to summarize per API call. Kept modest so the model's reply
# stays within the output-token budget and numbered parsing stays reliable.
_BATCH_SIZE = 12

# Built lazily on first use so importing this module doesn't require the API
# key. That lets config.validate() report a missing key cleanly in main()
# instead of OpenAI() blowing up with a cryptic error at import time.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        # 120s timeout + no retries so one slow call fails fast instead of
        # hanging the whole run (SDK default is 600s x 3 retries).
        _client = OpenAI(
            api_key=config.NVIDIA_API_KEY,
            base_url=config.NVIDIA_BASE_URL,
            timeout=120,
            max_retries=0,
        )
    return _client


PROMPT = """You write concise "why it matters" notes for a developer digest.

For EACH numbered item below, write ONE sentence telling a developer what's
notable (for a release: what changed and why it matters). Be specific and
concrete. No hype, no preamble.

Return EXACTLY one line per item, in the same order, formatted as:
<number>. <sentence>

Items:
{items}"""

_LINE = re.compile(r"^\s*(\d+)[.):]\s*(.+)$")


def _parse(reply: str, count: int) -> list[str]:
    """Map the model's numbered lines back to item positions (1-based)."""
    by_index: dict[int, str] = {}
    for line in reply.splitlines():
        m = _LINE.match(line)
        if m:
            by_index[int(m.group(1))] = m.group(2).strip()
    return [by_index.get(i + 1, "") for i in range(count)]


def _summarize_batch(items: list[dict]) -> list[str]:
    listing = "\n".join(
        f"{i + 1}. [{it['source']} · {it['meta']}] {it['title']}"
        f" — {it['desc'] or '(no description)'}"
        for i, it in enumerate(items)
    )
    for attempt in range(2):  # one retry: there are only a few calls per run
        try:
            resp = _get_client().chat.completions.create(
                model=config.NVIDIA_MODEL,
                messages=[
                    {"role": "user", "content": PROMPT.format(items=listing)}
                ],
                temperature=0.4,
                max_tokens=min(1024, 70 * len(items)),
            )
            return _parse(resp.choices[0].message.content or "", len(items))
        except RateLimitError:
            if attempt == 0:
                time.sleep(15)  # let the free-tier quota window roll over
                continue
            print(f"[summarizer] batch of {len(items)} rate-limited, gave up")
        except Exception as exc:  # don't let one bad call sink the whole digest
            print(f"[summarizer] batch of {len(items)} failed: {exc}")
            break
    return [""] * len(items)


def enrich(items: list[dict]) -> list[dict]:
    if not items:
        return items
    # Sequential chunks — gentle on the rate limit, only a handful of calls.
    summaries: list[str] = []
    for start in range(0, len(items), _BATCH_SIZE):
        summaries.extend(_summarize_batch(items[start : start + _BATCH_SIZE]))
    for item, summary in zip(items, summaries):
        item["why_it_matters"] = summary
    return items
