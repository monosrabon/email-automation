import imaplib
import email
from email.header import decode_header
import os
import re
from dotenv import load_dotenv

# Load email credentials from .env
load_dotenv()
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

IMAP_SERVER = "imap.gmail.com"
OUTPUT_FOLDER = "emails"
MAX_EMAILS = 20


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\- ]", "_", text)
    return text[:50]


def get_email_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore"
                    )
                except:
                    pass
    else:
        if msg.get_content_type() == "text/plain":
            try:
                return msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8",
                    errors="ignore"
                )
            except:
                pass

    return ""


def decode_str(s):
    if not s:
        return ""
    decoded, enc = decode_header(s)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="ignore")
    return decoded


def fetch_emails():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    status, data = mail.search(None, "ALL")
    ids = data[0].split()[-MAX_EMAILS:]

    for num in ids:
        status, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_str(msg.get("Subject"))
        sender = decode_str(msg.get("From"))
        body = get_email_body(msg)

        if not body.strip():
            continue

        filename = f"{safe_filename(subject)}_{num.decode()}.txt"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"From: {sender}\n")
            f.write(f"Subject: {subject}\n\n")
            f.write(body)

        print(f"Saved: {filepath}")

    mail.logout()


if __name__ == "__main__":
    fetch_emails()
