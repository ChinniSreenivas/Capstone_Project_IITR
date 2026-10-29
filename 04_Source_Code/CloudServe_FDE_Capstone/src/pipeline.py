"""End-to-end pipeline with per-ticket failure isolation."""
import json, time, os, re
from .ingest import normalize_ticket
from .classify import classify
from .retrieve import Retriever
from .route import decide, THRESHOLD
from .generate import draft
from .guardrails import validate
from .logging_store import append_decision

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

try:
    TRAINING_EXAMPLES = load_json(
        ROOT / "data" / "development_tickets.json"
    )
except Exception as exc:
    print(f"Warning: training examples could not be loaded: {exc}")
    TRAINING_EXAMPLES = None


def load_json(path):
    with open(path,encoding="utf-8") as f: return json.load(f)

def process_ticket(raw, retriever, log_path=None):
    start=time.perf_counter()
    ticket=normalize_ticket(raw)
    classification=classify(ticket, TRAINING_EXAMPLES)
    sources=retriever.search(ticket.get("text",""),top_k=3)
    decision=decide(ticket,classification,sources)
    generated={"answer":"","citations":[]}
    guard={"blocked":False,"findings":[],"checks":{"pii":"pass","grounding":"review","tone":"pass"}}
    if decision["action"]=="auto_respond":
        generated=draft(ticket,classification,sources)
        guard=validate(ticket,generated["answer"],sources)
        if guard["blocked"]:
            decision={"action":"block","reason":"Generated response failed a blocking safety validation."}
    if decision["action"]!="auto_respond":
        generated={"answer":"","citations":[]}
    elapsed=(time.perf_counter()-start)*1000
    record={
      "decision_id":f"DEC-{ticket['ticket_id']}-{int(time.time()*1000)}",
      "timestamp":ticket["received_at"],"ticket_id":ticket["ticket_id"],"channel":ticket["channel"],
      "stage":"validation" if guard["blocked"] else "routing","input_summary":ticket["text"][:300],
      "model":{"name":"local-deterministic-pipeline","version":"1.0.0"},
      "prediction":{"value":classification["intent"],"confidence":classification["confidence"]},
      "alternatives":classification["alternatives"],"sources_used":[{"doc_id":s["doc_id"],"score":s["score"]} for s in sources],
      "threshold_applied":THRESHOLD,"action_taken":decision["action"],"reason":decision["reason"],
      "guardrail_results":guard["checks"],"guardrail_findings":guard["findings"],
      "prompt_version":"PR-01 v1.0","requirement_ids":["FR-01","FR-02","FR-03","FR-04","FR-05"],
      "latency_ms":round(elapsed,3),"intent":classification["intent"],"urgency":classification["urgency"],
      "confidence":classification["confidence"],"retrieval_hit":bool(sources),
      "answer":generated["answer"],"citations":generated["citations"],
      "escalation_summary":(ticket["text"][:500] if decision["action"]=="escalate" else "")
    }
    if log_path: append_decision(log_path,record)
    return record
