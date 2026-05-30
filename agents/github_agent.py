"""Checks favorite repos for new releases via the GitHub REST API.

Dedup (storage.py) keys on the release tag, so a repo only appears in the
digest the day it ships a new version.
"""
import requests

import config

RELEASE_URL = "https://api.github.com/repos/{repo}/releases/latest"


def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "daily-digest",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return headers


def fetch() -> list[dict]:
    headers = _headers()
    items: list[dict] = []
    for repo in config.FAVORITE_REPOS:
        try:
            resp = requests.get(
                RELEASE_URL.format(repo=repo), headers=headers, timeout=20
            )
            if resp.status_code == 404:
                continue  # repo has no published releases
            resp.raise_for_status()
            rel = resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[github] {repo} failed: {exc}")
            continue

        tag = rel.get("tag_name")
        if not tag:
            continue
        items.append(
            {
                "id": f"rel:{repo}:{tag}",
                "source": "GitHub Release",
                "title": f"{repo} {tag}",
                "url": rel.get("html_url", f"https://github.com/{repo}/releases"),
                "desc": (rel.get("body") or "").strip()[:500],
                "meta": f"released {(rel.get('published_at') or '')[:10]}",
            }
        )
    return items
