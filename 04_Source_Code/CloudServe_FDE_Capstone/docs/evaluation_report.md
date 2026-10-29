# Evaluation Report — CloudServe Support Automation

## Run provenance
Run the supplied validation set with `python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/`. The harness writes a timestamped metrics record plus per-ticket results and decision log. The committed generated result is the reproducible output from this repository build. It is not the hidden assessment run; the hidden set is not included in the pack.

## How to interpret the results
- **Volume:** processed tickets must equal the sum of auto-respond, escalate and block decisions.
- **First-contact resolution:** historical ticket metadata is a baseline field; it is not the causal outcome of this new system. The auto-response share is only a proxy, not proof of resolution.
- **Response time:** no live customer or model call is used, so customer-facing time-to-first-reply and CSAT uplift cannot be inferred. The harness reports pipeline latency in milliseconds, including lexical retrieval and validation.
- **Classification:** precision and recall are calculated per intent against supplied labels. The deterministic keyword classifier is a baseline; rare classes and paraphrases may perform poorly.
- **Retrieval:** hit rate means at least one document exceeded the retrieval threshold. A hit does not prove the cited passage fully supports every claim.
- **Governance:** decision log coverage should be exactly 100%; PII detections and guardrail findings are counted automatically.

## Limitations and next steps
The figures above should be treated with caution because the classifier confidence is a heuristic rather than calibrated probability, the response generator uses excerpts rather than a language model, and historical business outcomes do not establish the effect of this implementation. This report does not claim a measured improvement to the 42% first-contact-resolution baseline, the 8–12 hour historical reply time or the 3.2/5 historical CSAT. A human review of at least 50 responses by two independent assessors is still required to estimate hallucination rate and citation accuracy. The 80-ticket validation set is not the hidden assessment set; report any hidden-set run count accurately when the assessor runs it.

## AI assistance disclosure
ChatGPT assisted with drafting and debugging implementation scaffolding and documentation. The code is intended as an explainable baseline; the author should review, test, adapt, and be able to explain each component. Discovery findings and personal reflection must be written from the actual interview transcripts and observed data, not invented. Replace or supplement this section with a truthful account of any additional tools used.
