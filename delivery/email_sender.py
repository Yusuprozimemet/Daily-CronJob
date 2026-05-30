"""Sends the digest as an HTML email via Gmail SMTP (SSL)."""
import smtplib
import ssl
from datetime import date
from email.mime.text import MIMEText

import config

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _render_html(items: list[dict]) -> str:
    cards = []
    for item in items:
        why = (
            f'<p style="margin:6px 0;color:#444">{item["why_it_matters"]}</p>'
            if item.get("why_it_matters")
            else ""
        )
        cards.append(
            f"""
            <div style="margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #eee">
              <a href="{item['url']}" style="font-size:16px;font-weight:600;color:#0969da;text-decoration:none">
                {item['title']}
              </a>
              <div style="font-size:12px;color:#888;margin:4px 0">{item['source']} · {item['meta']}</div>
              {why}
            </div>"""
        )
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:auto">
      <h2>Daily Digest — {date.today():%b %d, %Y}</h2>
      <p style="color:#666">{len(items)} new item(s) today.</p>
      {''.join(cards)}
    </div>"""


def send(items: list[dict]) -> None:
    if not items:
        return
    msg = MIMEText(_render_html(items), "html", "utf-8")
    msg["Subject"] = f"Daily Digest — {len(items)} new ({date.today():%b %d})"
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(config.EMAIL_FROM, config.GMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"[email] sent {len(items)} item(s) to {config.EMAIL_TO}")
