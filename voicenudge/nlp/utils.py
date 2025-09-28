import re, os
import dateparser
from datetime import datetime, timedelta
import pytz
import spacy

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

def clean_text(text: str) -> str:
    """Normalize text by trimming, lowering, removing extra spaces."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def parse_task(text: str):
    """
    Parse a task string into a title and due datetime.
    Example: "Buy milk tomorrow at 6pm"
    Returns: {"title": "buy milk", "due_at": datetime or None}
    """
    tzname = os.getenv("TIMEZONE", "Asia/Kolkata")
    tz = pytz.timezone(tzname)
    now = datetime.now(tz)

    # --- Try parsing with dateparser first ---
    due_at = dateparser.parse(
        text,
        languages=["en"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": now,
            "RETURN_AS_TIMEZONE_AWARE": True,
        }
    )

    # --- Fallback if dateparser fails ---
    if not due_at and "tomorrow" in text:
        # Look for patterns like "6 pm" / "10 am"
        match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3).lower()

            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            due_at = (now + timedelta(days=1)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        else:
            # Default to tomorrow 9 AM
            due_at = (now + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )

    # --- Title extraction ---
    doc = nlp(text)
    tokens = [t.lemma_.lower() for t in doc if not t.is_stop and t.is_alpha]
    title = " ".join(tokens) if tokens else text

    return {
        "title": title.strip(),
        "due_at": due_at.isoformat() if due_at else None
    }
