"""Orchestrates the daily digest: scrape -> dedup -> summarize -> deliver."""
import config
from agents import hacker_news_agent, reddit_agent, summarizer_agent
from delivery import email_sender, telegram_sender
from storage import filter_new, load_seen, save_seen

# GitHub releases collection is paused for now — focusing on Reddit + Hacker News.
# To re-enable: add `github_agent` back to the import above and the sources tuple.


def main() -> None:
    config.validate()

    # 1. Scrape sources (independent; failure of one shouldn't kill the run).
    items: list[dict] = []
    sources = (
        ("reddit", reddit_agent),
        ("hackernews", hacker_news_agent),
    )
    for name, agent in sources:
        try:
            fetched = agent.fetch()
            print(f"[{name}] fetched {len(fetched)} item(s)")
            items.extend(fetched)
        except Exception as exc:
            print(f"[{name}] fetch failed: {exc}")

    # 2. Dedup against previously delivered items.
    seen = load_seen()
    new_items = filter_new(items, seen)
    print(f"{len(new_items)} new of {len(items)} scraped")
    if not new_items:
        print("Nothing new. Done.")
        return

    # 3. Summarize.
    new_items = summarizer_agent.enrich(new_items)

    # 4. Deliver (each channel independent).
    for name, sender in (("telegram", telegram_sender), ("email", email_sender)):
        try:
            sender.send(new_items)
        except Exception as exc:
            print(f"[{name}] send failed: {exc}")

    # 5. Persist state only after delivery succeeded enough to try.
    seen.update(item["id"] for item in new_items)
    save_seen(seen)
    print("Done.")


if __name__ == "__main__":
    main()
