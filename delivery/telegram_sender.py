"""Sends the digest to Telegram as a Markdown message."""
import requests

import config

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096  # Telegram per-message limit


def _format(items: list[dict]) -> str:
    lines = [f"*Daily Digest* — {len(items)} new item(s)\n"]
    for item in items:
        lines.append(f"[{item['title']}]({item['url']})")
        lines.append(f"_{item['source']} · {item['meta']}_")
        if item.get("why_it_matters"):
            lines.append(item["why_it_matters"])
        lines.append("")
    return "\n".join(lines)


def _send_chunk(text: str) -> None:
    resp = requests.post(
        API.format(token=config.TELEGRAM_BOT_TOKEN),
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    resp.raise_for_status()


def send(items: list[dict]) -> None:
    if not items:
        return
    text = _format(items)
    # Split on item boundaries if over the limit.
    while len(text) > MAX_LEN:
        cut = text.rfind("\n\n", 0, MAX_LEN)
        cut = cut if cut > 0 else MAX_LEN
        _send_chunk(text[:cut])
        text = text[cut:].lstrip()
    _send_chunk(text)
    print(f"[telegram] sent {len(items)} item(s)")
