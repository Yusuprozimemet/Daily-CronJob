"""Pulls current Hacker News front-page stories via the Algolia HN API.

The official Firebase API needs one request per story id; Algolia's search
endpoint returns the whole front page (title, url, points, comments) in a
single unauthenticated call, which is all we need for a digest.
"""
import requests

import config

# tags=front_page returns the stories currently on the HN front page.
SEARCH_URL = "https://hn.algolia.com/api/v1/search"
ITEM_URL = "https://news.ycombinator.com/item?id={id}"


def fetch() -> list[dict]:
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"tags": "front_page", "hitsPerPage": config.HN_LIMIT},
            headers={"User-Agent": "daily-digest"},
            timeout=20,
        )
        resp.raise_for_status()
        hits = resp.json()["hits"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        print(f"[hackernews] fetch failed: {exc}")
        return []

    items: list[dict] = []
    for hit in hits:
        obj_id = hit.get("objectID")
        if not obj_id:
            continue
        discussion = ITEM_URL.format(id=obj_id)
        items.append(
            {
                "id": f"hn:{obj_id}",
                "source": "Hacker News",
                "title": hit.get("title") or "(untitled)",
                # Ask/Show HN posts have no external url; link to the thread.
                "url": hit.get("url") or discussion,
                "desc": (hit.get("story_text") or "")[:300],
                "meta": f"▲ {hit.get('points', 0)} · {hit.get('num_comments', 0)} comments",
            }
        )
    return items
