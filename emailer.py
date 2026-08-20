"""
Emailer — sends the Net Worth + Budget report to Gmail via SMTP.

One-time setup:
1. Turn on 2-Step Verification on the Gmail account you want to send FROM:
   https://myaccount.google.com/security
2. Create an App Password (choose "Mail" as the app):
   https://myaccount.google.com/apppasswords
   Google gives you a 16-character code — use that, not your normal password.
3. Add these to Streamlit secrets (.streamlit/secrets.toml locally, or the
   "Secrets" section in Streamlit Cloud settings):

   [email]
   sender_address = "youraddress@gmail.com"
   app_password = "xxxxxxxxxxxxxxxx"
   default_recipient = "youraddress@gmail.com"

That's it — no OAuth, no Google Cloud project needed.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st


def is_configured() -> bool:
    try:
        cfg = st.secrets["email"]
        return bool(cfg.get("sender_address")) and bool(cfg.get("app_password"))
    except Exception:
        return False


def default_recipient() -> str:
    try:
        cfg = st.secrets["email"]
        return cfg.get("default_recipient") or cfg.get("sender_address") or ""
    except Exception:
        return ""


def send_report(recipient: str, subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
    """Send an email via Gmail SMTP. Returns (success, message)."""
    if not is_configured():
        return False, "Email isn't set up yet — add sender_address and app_password under [email] in Streamlit secrets."
    if not recipient or "@" not in recipient:
        return False, "Enter a valid recipient email address."

    cfg = st.secrets["email"]
    sender = cfg["sender_address"]
    app_password = cfg["app_password"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True, f"Report sent to {recipient}."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail rejected the login — make sure app_password is a 16-character App Password, not your regular Gmail password."
    except Exception as e:
        return False, f"Couldn't send email: {e}"
