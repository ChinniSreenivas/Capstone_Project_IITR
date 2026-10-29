"""Deterministic routing policy; high-risk and low-evidence cases escalate."""
THRESHOLD = 0.68
def decide(ticket, classification, sources, guardrail=None):
    text=(ticket.get("text") or "").lower()
    labels=ticket.get("original",{}).get("labels",{})
    if guardrail and guardrail.get("blocked"):
        return {"action":"block","reason":"A response guardrail fired; no outbound answer is permitted."}
    if not text.strip():
        return {"action":"escalate","reason":"Empty ticket content needs a human to clarify the request."}
    if any(x in text for x in ["refund", "chargeback", "legal action", "security breach", "data breach", "delete my account"]):
        return {"action":"escalate","reason":"Sensitive, financial, or security-related request requires human review."}
    if not sources:
        return {"action":"escalate","reason":"No documentation passage met the relevance threshold."}
    if classification["confidence"] < THRESHOLD:
        return {"action":"escalate","reason":f"Classification confidence {classification['confidence']:.3f} is below the {THRESHOLD:.2f} threshold."}
    if classification["urgency"] == "critical":
        return {"action":"escalate","reason":"Critical urgency requires a human response."}
    return {"action":"auto_respond","reason":f"Relevant documentation found and confidence {classification['confidence']:.3f} meets the {THRESHOLD:.2f} threshold."}
