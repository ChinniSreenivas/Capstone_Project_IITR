"""Normalize heterogeneous support tickets into a stable internal schema."""
from datetime import datetime, timezone
import hashlib

CHANNELS = {"email", "chat", "documentation_comment", "forum"}

def normalize_ticket(raw):
    if not isinstance(raw, dict):
        raw = {}
    channel = str(raw.get("channel") or "unknown").strip().lower()
    # Accept common aliases without losing the source channel.
    aliases = {"live_chat":"chat", "documentation comments":"documentation_comment",
               "docs_comment":"documentation_comment", "community_forum":"forum"}
    channel = aliases.get(channel, channel)
    body = str(raw.get("body") or "")
    subject = str(raw.get("subject") or "")
    ticket_id = str(raw.get("ticket_id") or "T-" + hashlib.sha256((channel+subject+body).encode()).hexdigest()[:12])
    received = raw.get("received_at")
    if not received:
        received = datetime.now(timezone.utc).isoformat()
    return {
        "ticket_id": ticket_id, "channel": channel, "original_channel": str(raw.get("channel") or "unknown"),
        "subject": subject, "body": body, "text": (subject + "\n" + body).strip(),
        "received_at": str(received), "customer_id": str(raw.get("customer_id") or ""),
        "customer_tier": str(raw.get("customer_tier") or "unknown"),
        "customer_region": str(raw.get("customer_region") or "unknown"),
        "language_fluency": str(raw.get("language_fluency") or "unknown"),
        "original": raw
    }
