
"""Deterministic support-ticket classifier with transparent confidence scores."""

import re

INTENT_TERMS = {
    "account_access": [
        "access", "permission", "role", "invitation", "user",
        "account locked", "restore access",
    ],
    "authentication": [
        "login", "log in", "password", "credential", "mfa",
        "authenticator", "recovery code", "authentication",
        "sign in", "sign-in", "invalid credentials",
    ],
    "api_key_issue": [
        "api key", "token", "rotate secret", "api credential",
        "401 unauthorized",
    ],
    "deployment_failure": [
        "deploy", "deployment", "build", "dependency",
        "release", "production", "pipeline",
    ],
    "billing": [
        "bill", "invoice", "charge", "payment",
        "subscription", "refund",
    ],
    "performance": [
        "slow", "latency", "timeout", "performance",
        "response time", "degraded",
    ],
    "data_issue": [
        "data", "missing", "corrupt", "export", "import",
        "sync", "database",
    ],
    "integration": [
        "integration", "webhook", "connect", "sdk", "api",
        "endpoint",
    ],
    "sso_configuration": [
        "sso", "single sign-on", "saml",
        "identity provider", "oidc",
    ],
    "security": [
        "security", "exposed", "breach", "unauthorized",
        "vulnerability",
    ],
    "bug_report": [
        "bug", "error", "exception", "crash", "broken",
        "unexpected",
    ],
    "feature_request": [
        "feature", "would like", "please add", "support for",
    ],
    "unclear_request": [
        "following up", "need help", "not working",
    ],
}

URGENT = [
    "outage", "production down", "all users", "data loss",
    "security breach", "critical",
]
HIGH = [
    "urgent", "blocked", "production", "failed", "failure",
    "deadline", "401", "error",
]
LOW = ["question", "how do i", "documentation", "suggestion"]

# Explicit patterns prevent noisy training labels from overriding
# obvious password and login requests.
AUTH_PATTERNS = [
    r"\bpassword reset\b",
    r"\breset (?:my|the|a) password\b",
    r"\bforgot (?:my|the) password\b",
    r"\b(?:cannot|can't|unable to) log in\b",
    r"\b(?:cannot|can't|unable to) login\b",
    r"\b(?:cannot|can't|unable to) sign in\b",
    r"\binvalid credentials\b",
    r"\blogin (?:issue|problem|failure)\b",
    r"\bauthentication failure\b",
    r"\bpassword.{0,30}(?:not working|incorrect|rejected)\b",
]


def _urgency(text):
    if any(term in text for term in URGENT):
        return "critical"
    if any(term in text for term in HIGH):
        return "high"
    if any(term in text for term in LOW):
        return "low"
    return "medium"


def _result(intent, confidence, urgency, method, alternatives=None):
    return {
        "intent": intent,
        "urgency": urgency,
        "confidence": round(confidence, 3),
        "alternatives": alternatives or [
            {"value": intent, "confidence": round(confidence, 3)}
        ],
        "method": method,
    }


def classify(ticket, examples=None):
    """Classify a normalized ticket without trusting noisy labels blindly."""
    text = (
        ticket.get("text")
        or ticket.get("body")
        or ""
    ).strip().lower()

    if not text:
        return _result(
            "unclear_request", 0.25, "medium", "empty_fallback"
        )

    urgency = _urgency(text)

    # 1. High-precision rules for explicit authentication problems.
    if any(re.search(pattern, text) for pattern in AUTH_PATTERNS):
        return _result(
            "authentication",
            0.85,
            urgency,
            "password_login_rule_v1",
        )

    # 2. Keyword scoring for the remaining tickets.
    scores = {}
    for intent, terms in INTENT_TERMS.items():
        scores[intent] = sum(
            2 if " " in term else 1
            for term in terms
            if term in text
        )

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    )
    best, raw_score = ranked[0]
    total = sum(scores.values())

    # 3. Use the labelled development set only when keyword
    #    rules cannot identify an intent.
    if raw_score == 0 and examples:
        query_tokens = set(re.findall(r"[a-z0-9_'-]+", text))
        votes = {}

        for example in examples:
            labels = example.get("labels") or {}
            label = labels.get("intent")
            example_text = (
                str(example.get("subject") or "")
                + " "
                + str(example.get("body") or "")
            ).lower()
            example_tokens = set(
                re.findall(r"[a-z0-9_'-]+", example_text)
            )

            if not label or not query_tokens or not example_tokens:
                continue

            overlap = len(query_tokens & example_tokens)
            similarity = overlap / len(query_tokens | example_tokens)

            if similarity > 0:
                votes[label] = votes.get(label, 0.0) + similarity

        if votes:
            best = sorted(
                votes.items(),
                key=lambda item: (-item[1], item[0]),
            )[0][0]
            confidence = 0.55
            return _result(
                best,
                confidence,
                urgency,
                "development_set_fallback_v1",
            )

    if raw_score == 0:
        return _result(
            "unclear_request",
            0.30,
            urgency,
            "deterministic_keyword_score_v2",
        )

    # This is a heuristic confidence score, not a calibrated probability.
    confidence = min(
        0.90,
        0.50 + 0.35 * raw_score / (total or 1),
    )

    alternatives = [
        {
            "value": label,
            "confidence": round(score / total, 3),
        }
        for label, score in ranked[:3]
        if score > 0
    ]

    return _result(
        best,
        confidence,
        urgency,
        "deterministic_keyword_score_v2",
        alternatives,
    )
