"""Single-command unattended evaluation harness."""
import argparse, json, os, statistics, sys, time
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.pipeline import load_json, process_ticket
from src.retrieve import Retriever

def pct(values,p):
    if not values:return 0.0
    xs=sorted(values); return xs[min(len(xs)-1,max(0,int((len(xs)-1)*p)))]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True); ap.add_argument("--output",required=True)
    ap.add_argument("--docs",default=str(ROOT/"data"/"documentation.json"))
    args=ap.parse_args()
    tickets=load_json(args.input); docs=load_json(args.docs); retriever=Retriever(docs)
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    stem=Path(args.input).stem
    log=out/f"{stem}_decisions.jsonl"; results=out/f"{stem}_results.jsonl"; metrics=out/f"{stem}_metrics.json"
    for p in (log,results):
        if p.exists(): p.unlink()
    rows=[]; lat=[]
    for raw in tickets:
        try:
            r=process_ticket(raw,retriever,str(log)); rows.append(r); lat.append(r["latency_ms"])
        except Exception as e:
            # Failure isolation: malformed ticket still yields a logged escalation.
            tid=str(raw.get("ticket_id","UNKNOWN")) if isinstance(raw,dict) else "MALFORMED"
            r={"ticket_id":tid,"action_taken":"escalate","reason":"Processing exception safely isolated; manual review required.",
               "intent":"unclear_request","urgency":"medium","confidence":0.0,"retrieval_hit":False,"latency_ms":0.0,
               "answer":"","citations":[],"guardrail_findings":["processing_exception"]}
            from src.logging_store import append_decision
            append_decision(str(log),r); rows.append(r); lat.append(0.0)
        with open(results,"a",encoding="utf-8") as f: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    counts={k:sum(r.get("action_taken")==k for r in rows) for k in ["auto_respond","escalate","block"]}
    labelled=[(r,t) for r,t in zip(rows,tickets) if isinstance(t,dict) and isinstance(t.get("labels"),dict)]
    intents=sorted(set(t["labels"].get("intent","unknown") for _,t in labelled))
    per_class={}
    for label in intents:
        tp=sum(r.get("intent")==label and t["labels"].get("intent")==label for r,t in labelled)
        fp=sum(r.get("intent")==label and t["labels"].get("intent")!=label for r,t in labelled)
        fn=sum(r.get("intent")!=label and t["labels"].get("intent")==label for r,t in labelled)
        per_class[label]={"precision":round(tp/(tp+fp),4) if tp+fp else 0,
                          "recall":round(tp/(tp+fn),4) if tp+fn else 0,"support":tp+fn}
    fcr=sum(bool(t.get("history",{}).get("first_contact_resolution")) for t in tickets if isinstance(t,dict))/max(1,len(tickets))
    # Ground-truth history is historical baseline; automated action rate is reported separately.
    confmat={}
    for r,t in labelled:
        true=t["labels"].get("intent","unknown"); pred=r.get("intent","unknown")
        confmat.setdefault(true,{})[pred]=confmat.setdefault(true,{}).get(pred,0)+1
    guard=CounterGuard(rows)
    metrics_obj={
      "run":{"input":str(Path(args.input).name),"tickets_processed":len(rows),"run_timestamp_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
             "system_version":"1.0.0","hidden_evaluation_runs":0,"notes":"This run uses the supplied validation/development file; it is not the hidden assessment set."},
      "volume":{"tickets_processed":len(rows),"answered_automatically":counts["auto_respond"],"escalated":counts["escalate"],"blocked_by_guardrails":counts["block"]},
      "business":{"historical_first_contact_resolution_pct":round(100*fcr,2),
          "automated_resolution_proxy_pct":round(100*counts["auto_respond"]/max(1,len(rows)),2),
          "mean_response_time_minutes":None,"median_response_time_minutes":None,
          "escalation_rate_pct":round(100*counts["escalate"]/max(1,len(rows)),2),
          "csat_proxy_mean":round(statistics.mean([t.get("history",{}).get("csat_rating") for t in tickets if isinstance(t,dict) and isinstance(t.get("history",{}).get("csat_rating"),(int,float))]),2) if any(isinstance(t,dict) and isinstance(t.get("history",{}).get("csat_rating"),(int,float)) for t in tickets) else None},
      "technical":{"classification_precision_recall_per_class":per_class,"confusion_matrix":confmat,
          "macro_precision":round(statistics.mean(v["precision"] for v in per_class.values()),4) if per_class else 0,
          "macro_recall":round(statistics.mean(v["recall"] for v in per_class.values()),4) if per_class else 0,
          "retrieval_hit_rate_pct":round(100*sum(r.get("retrieval_hit",False) for r in rows)/max(1,len(rows)),2),
          "latency_median_ms":round(pct(lat,.5),3),"latency_p95_ms":round(pct(lat,.95),3)},
      "governance":{"decisions_logged":sum(1 for _ in open(log,encoding="utf-8")),"decision_log_matches_processed":sum(1 for _ in open(log,encoding="utf-8"))==len(rows),
          "guardrail_activations_by_type":guard,"private_data_detections":sum(v for k,v in guard.items() if k in ["email","api_secret","phone"])},
    }
    metrics.write_text(json.dumps(metrics_obj,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"processed":len(rows),"metrics":str(metrics),"decisions":str(log),"results":str(results)},indent=2))
def CounterGuard(rows):
    from collections import Counter
    c=Counter()
    for r in rows:
        c.update(r.get("guardrail_findings",[]))
    return dict(c)
if __name__=="__main__": main()
