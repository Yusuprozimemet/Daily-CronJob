"""Pulls top daily posts from configured subreddits via Reddit's public RSS.

Reddit discontinued self-service OAuth API access for new developers, so the
old client_credentials path needs an app id/secret that can no longer be
created. The public per-subreddit RSS/Atom feeds (e.g. /r/Python/top.rss) stay
open, need no credentials, and are plenty for a daily digest. They only require
a descriptive User-Agent — Reddit 429s the default urllib/requests one.
"""
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

import config

FEED_URL = "https://www.reddit.com/r/{sub}/top.rss?t=day&limit={limit}"
_ATOM = "{http://www.w3.org/2005/Atom}"


def _text(entry: ET.Element, tag: str) -> str:
    el = entry.find(f"{_ATOM}{tag}")
    return (el.text or "").strip() if el is not None and el.text else ""


def fetch() -> list[dict]:
    headers = {"User-Agent": config.REDDIT_USER_AGENT}

    items: list[dict] = []
    for sub in config.SUBREDDITS:
        url = FEED_URL.format(sub=sub, limit=config.REDDIT_LIMIT)
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[reddit] r/{sub} failed: {exc}")
            continue

        for entry in root.findall(f"{_ATOM}entry"):
            # Atom <id> is "t3_<post_id>"; keep the rd: prefix for dedup parity.
            raw_id = _text(entry, "id").rsplit("_", 1)[-1]
            if not raw_id:
                continue
            link_el = entry.find(f"{_ATOM}link")
            url = link_el.get("href", "") if link_el is not None else ""
            desc = BeautifulSoup(_text(entry, "content"), "html.parser").get_text(
                " ", strip=True
            )
            items.append(
                {
                    "id": f"rd:{raw_id}",
                    "source": "Reddit",
                    "title": _text(entry, "title"),
                    "url": url,
                    "desc": desc[:300],
                    "meta": f"r/{sub}",
                }
            )
    return items
