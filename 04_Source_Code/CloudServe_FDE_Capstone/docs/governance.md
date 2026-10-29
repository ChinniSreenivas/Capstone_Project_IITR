# Governance, Risk and Incident Response

## Risk register
| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Confident incorrect answer | High | High | Low-confidence/missing-source escalation; citation checks; sample human review | Engineering owner |
| R-02 | Private data in outbound text | Medium | Critical | Blocking email/phone/key patterns; never release blocked answer; audit log | Security owner |
| R-03 | Prompt injection in ticket body | Medium | High | Treat ticket body as data; no dynamic instruction execution; test adversarial cases | Engineering owner |
| R-04 | Unequal quality across customer groups | Medium | High | Segment by tier, language fluency, region and ticket length; review >5 point gaps | Product/support owner |
| R-05 | Stale documentation | Medium | High | Assign document owners, track review age, monthly corpus review and expiry alerts | Knowledge owner |
| R-06 | Provider outage | Low in offline baseline | Medium | No provider dependency; production LLM adapter must use timeout, bounded retry and fallback-to-human | Platform owner |
| R-07 | Latency under load | Medium | Medium | Measure p95, cap request sizes, load test and queue asynchronous work | Platform owner |
| R-08 | Cost increases | Low in offline baseline | Medium | Local baseline; if provider added, budget alerts, caching, per-ticket token limits | Product owner |

## Guardrails
- **Private data:** block if an email, phone-like number or API-secret pattern is found in the generated response.
- **Grounding:** citation identifiers must resolve to sources returned by retrieval. No retrieval result means escalation.
- **Unsupported commitments:** block refund/fix-date promises.
- **Scope and urgency:** security/financial/critical requests are routed to a human.
- **Confidence floor:** route below 0.68 to human review.

These are minimum baseline controls, not a guarantee of safety. Regex-based PII detection has false positives and false negatives; production use requires a more complete detector and human sampling.

## Decision logging
Each processed ticket writes one JSONL record with decision ID, timestamp, ticket ID, stage, input summary, model/version, predicted intent/confidence, alternatives, source IDs/scores, threshold, action/reason, guardrail results, prompt version and requirement IDs. Reconcile logged records to tickets processed for every run. Logs may contain customer data; restrict access, encrypt storage and set retention limits.

## Incident response
1. **Detect (on-call support/monitoring):** alert on sudden block/escalation spikes, PII finding, p95 latency, or log reconciliation failure. Target: within 5 minutes of alert.
2. **Contain (incident commander):** stop API process and switch the deployment to manual support. Target: under 5 minutes. This repository's immediate kill switch is process shutdown; a remote feature flag remains a production requirement.
3. **Assess (engineering + security):** identify affected ticket IDs from decision log; preserve logs; determine whether any answer escaped.
4. **Notify (support lead/security):** follow customer and regulatory notification policy; do not speculate before facts are confirmed.
5. **Remediate (engineering owner):** disable faulty route, fix rule/corpus/prompt, add regression tests, review all affected cases.
6. **Review (service owner):** write a post-incident review within two business days; track actions and verify kill-switch drill.

## Fairness audit plan
Report outcomes by customer tier, language fluency, region, channel and text length. The provided validation data is small; groups with fewer than 10 tickets should be marked insufficient sample rather than compared confidently. A >5 percentage-point resolution-quality gap triggers review. Current implementation is lexical and may disadvantage non-fluent English; this remains an open risk.

## Declaration
- This system must never disclose another customer's private data or invent a support action.
- The mechanism that enforces that is blocking output validation, citation resolution and escalation policy.
- The most likely residual harm is an unsupported or incomplete answer passing a heuristic guardrail.
- We would not deploy this without a calibrated classifier, expanded PII testing, human-reviewed quality sample, remote kill switch, access-controlled logs, and a successful production-readiness review.
