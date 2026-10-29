"""Response safety checks that can block output."""
import re
PII_PATTERNS=[
 ("email",re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",re.I)),
 ("api_secret",re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|(?:api[_ -]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,})\b",re.I)),
 ("phone",re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{8,}\d)(?!\d)")),
]
UNSAFE_COMMITMENTS=["we have issued a refund","the issue is fixed on our side","will be fixed by","guarantee a refund"]
def validate(ticket, answer, sources):
    text=answer or ""
    findings=[]
    for name,pat in PII_PATTERNS:
        if pat.search(text): findings.append(name)
    lower=text.lower()
    if any(x in lower for x in UNSAFE_COMMITMENTS): findings.append("unsupported_commitment")
    cited=set(re.findall(r"\[(DOC-[A-Z0-9-]+)\]",text))
    valid={s["doc_id"] for s in sources}
    invalid=sorted(cited-valid)
    if invalid: findings.append("invalid_citation")
    # Do not send any answer containing private-data pattern or unsafe commitment.
    blocked=any(x in findings for x in ("email","api_secret","phone","unsupported_commitment","invalid_citation"))
    return {"blocked":blocked,"findings":findings,"checks":{"pii":"fail" if any(x in findings for x in ("email","api_secret","phone")) else "pass",
            "grounding":"fail" if invalid else ("pass" if cited else "review"),
            "tone":"fail" if "unsupported_commitment" in findings else "pass"}}
