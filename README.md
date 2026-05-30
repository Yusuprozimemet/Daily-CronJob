# Daily Digest

Watches your favorite GitHub repos for **new releases** and pulls top daily posts
from a few subreddits, summarizes each with the NVIDIA GLM-5.1 API, and delivers a
daily digest to **Telegram** and **email**. Runs on **GitHub Actions** at 06:00 UTC.

## Architecture

```
GitHub Actions (cron 06:00 UTC)
  └── main.py
       ├── agents/github_agent.py    → new releases of repos in FAVORITE_REPOS
       ├── agents/reddit_agent.py    → r/artificial, r/Python, r/SaaS, r/java (OAuth)
       ├── storage.py                → dedup vs seen.json (committed back)
       ├── agents/summarizer_agent.py→ NVIDIA GLM-5.1, one sentence per item
       ├── delivery/telegram_sender.py
       └── delivery/email_sender.py
```

## Local setup

```bash
# Git Bash:
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the values
python main.py
```

## Configuration

| Variable | Where to get it |
|---|---|
| `NVIDIA_API_KEY` | https://build.nvidia.com (rotate the old leaked one) |
| `GMAIL_APP_PASSWORD` | Google Account → Security → App passwords (needs 2FA on) |
| `EMAIL_FROM` / `EMAIL_TO` | your Gmail address |
| `TELEGRAM_BOT_TOKEN` | message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | message your bot, then `https://api.telegram.org/bot<TOKEN>/getUpdates` |
| `GITHUB_TOKEN` | optional; raises GitHub API rate limit. Auto-provided in Actions. |

Reddit needs no credentials — the digest reads the public per-subreddit RSS feeds.

### Which repos / subreddits

Edit `FAVORITE_REPOS` (format `owner/repo`) and `SUBREDDITS` in [config.py](config.py).

### Reddit

Reddit ended self-service OAuth API access, so the digest reads the open
per-subreddit RSS feeds (`/r/<sub>/top.rss`) instead — no app or keys to set up.

## Dedup

`seen.json` tracks delivered item IDs (release tag per repo, post id per Reddit
post), committed back by the Action so nothing is sent twice. A repo only appears
the day it ships a new release.
