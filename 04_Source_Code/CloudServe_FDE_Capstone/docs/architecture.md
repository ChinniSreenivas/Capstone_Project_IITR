# Architecture and Traceability

## Data flow
`Input JSON → normalize → classify → retrieve → route → draft → validate → response or escalation → JSONL decision log → metrics report`

| Requirement | Implementation | Evidence |
|---|---|---|
| FR-01 Normalize four channels | `src/ingest.py` | `tests/test_pipeline.py::test_all_channels_normalize` |
| FR-02 Intent, urgency, confidence and alternatives | `src/classify.py` | `test_empty_ticket_fallback` |
| FR-03 Traceable retrieval with relevance cutoff | `src/retrieve.py` | `test_retrieval_resolves_document_ids` |
| FR-04 Deterministic route threshold | `src/route.py` | `test_pipeline_deterministic_route` |
| FR-05 Cited structured draft | `src/generate.py` | inspect result JSONL |
| FR-06 Blocking response validation | `src/guardrails.py` | private email and invalid citation tests |
| FR-07 Decision logging | `src/logging_store.py`, `src/pipeline.py` | decisions count reconciles with run size |
| FR-08 Unattended evaluation and metrics | `evaluation/harness.py` | generated metrics JSON |
| FR-09 HTTP interface | `src/api.py` | `/health`, `/tickets` |

## Routing policy
The confidence threshold is 0.68. Critical urgency, empty content, sensitive financial/security requests, low classifier confidence, and missing retrieval evidence are escalated. A blocked generated answer is never sent. The confidence score is a heuristic and should not be interpreted as calibrated probability.

## Failure handling
The evaluation harness catches per-ticket processing exceptions and emits a logged escalation record rather than dropping the ticket. The pipeline does not call an external provider, so provider timeouts/rate limits are not on its runtime path. Production deployment still needs request timeouts, queueing, retries with backoff, alerting and an independently operated kill switch.
