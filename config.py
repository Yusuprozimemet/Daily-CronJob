"""Central config. Loads .env locally; in CI the vars come from GitHub secrets.

Fails loudly if a required key is missing, so local and CI behave the same.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # no-op in CI where .env doesn't exist

# --- NVIDIA / summarizer ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
# meta/llama-3.3-70b-instruct (~6s/call) — GLM-5.1's NIM free-tier endpoint
# hangs (even tiny calls time out), so we use the proven fast model instead.
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

# --- Email ---
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Reddit (public RSS feeds; no credentials needed) ---
# Reddit ended self-service OAuth API access, so we read the open per-subreddit
# RSS feeds instead. A descriptive User-Agent is required or Reddit returns 429.
REDDIT_USER_AGENT = "github-digest/1.0 by daily-cronjob"

# --- GitHub releases ---
# Optional: a token raises the rate limit from 60 to 5000 req/hr. In Actions
# the built-in GITHUB_TOKEN is passed automatically. Not required locally.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Sources ---
# Favorite repos to watch for new releases. Format: "owner/repo".
FAVORITE_REPOS = [
    "anthropics/claude-code",
    "openai/openai-python",
    "astral-sh/uv",
]
# GitHub-project sources: subs for sharing/discovering repos and projects,
# plus SaaS/startup/indie-builder subs where founders share what they're building.
# (ProgrammerHumor only occasionally has showcase posts — kept low-priority.)
SUBREDDITS = [
    "coolgithubprojects",
    "opensource",
    "SaaS",
    "indiehackers",
    "SideProject",
    "Startup_Ideas",
]
REDDIT_LIMIT = 5  # per subreddit, top posts of the day
HN_LIMIT = 5  # top stories from the Hacker News front page

_REQUIRED = {
    "NVIDIA_API_KEY": NVIDIA_API_KEY,
    "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
    "EMAIL_FROM": EMAIL_FROM,
    "EMAIL_TO": EMAIL_TO,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
}


def validate() -> None:
    missing = [name for name, value in _REQUIRED.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required config: "
            + ", ".join(missing)
            + "\nSet them in .env (local) or GitHub repo secrets (CI)."
        )
