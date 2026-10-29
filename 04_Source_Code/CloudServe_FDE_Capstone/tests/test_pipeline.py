import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.ingest import normalize_ticket
from src.classify import classify
from src.retrieve import Retriever
from src.pipeline import process_ticket
from src.guardrails import validate

def docs(): return json.loads((ROOT/"data"/"documentation.json").read_text(encoding="utf-8"))
def test_all_channels_normalize():
    for channel in ["email","chat","documentation_comment","forum"]:
        t=normalize_ticket({"channel":channel,"body":"login problem"})
        assert t["channel"]==channel and t["body"]=="login problem"
def test_empty_ticket_fallback():
    c=classify(normalize_ticket({"channel":"chat","body":""}))
    assert c["intent"]=="unclear_request" and 0<=c["confidence"]<=1
def test_retrieval_resolves_document_ids():
    rs=Retriever(docs()).search("multi factor authentication recovery code",3)
    ids={d["doc_id"] for d in docs()}
    assert rs and all(r["doc_id"] in ids for r in rs)
def test_guardrail_blocks_private_email():
    g=validate({}, "Please email another user at private@example.com [DOC-AUTH-001]", [{"doc_id":"DOC-AUTH-001"}])
    assert g["blocked"] and "email" in g["findings"]
def test_guardrail_blocks_invalid_citation():
    g=validate({}, "Do this [DOC-NOT-REAL]", [{"doc_id":"DOC-AUTH-001"}])
    assert g["blocked"]
def test_pipeline_deterministic_route():
    ret=Retriever(docs())
    raw={"ticket_id":"T-1","channel":"chat","body":"How can I recover my authenticator code?","labels":{}}
    a=process_ticket(raw,ret); b=process_ticket(raw,ret)
    assert a["action_taken"]==b["action_taken"] and a["intent"]==b["intent"]
def test_malformed_input_safe():
    ret=Retriever(docs())
    r=process_ticket({"ticket_id":"EMPTY","channel":"email","body":""},ret)
    assert r["action_taken"] in {"escalate","block","auto_respond"}
