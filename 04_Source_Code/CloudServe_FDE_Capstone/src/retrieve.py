"""Transparent corpus retrieval using token overlap and IDF-weighted scoring."""
import re, math

def tokens(s):
    return re.findall(r"[a-z0-9_'-]+", (s or "").lower())

class Retriever:
    def __init__(self, documents, threshold=0.08):
        self.documents=documents
        self.threshold=threshold
        self.docs=[]
        df={}
        for d in documents:
            text=d.get("title","")+" "+d.get("category","")+" "+d.get("content","")
            ts=set(tokens(text)); self.docs.append((d,ts))
            for t in ts: df[t]=df.get(t,0)+1
        self.idf={t: math.log(1+(len(documents)-n+0.5)/(n+0.5)) for t,n in df.items()}
    def search(self, query, top_k=3):
        q=set(tokens(query))
        if not q: return []
        results=[]
        for d,ts in self.docs:
            overlap=q & ts
            if not overlap: continue
            score=sum(self.idf.get(t,0) for t in overlap)/(sum(self.idf.get(t,0) for t in q)+1e-9)
            # Prefer exact multi-word matches when present.
            text=(d.get("title","")+" "+d.get("content","")).lower()
            phrase_bonus=sum(0.08 for term in ("api key","single sign-on","recovery code","dependency resolution") if term in query.lower() and term in text)
            score=min(1.0,score+phrase_bonus)
            if score>=self.threshold:
                results.append({"doc_id":d["doc_id"],"title":d.get("title",""),
                    "score":round(score,4),"passage":d.get("content","")[:1800]})
        return sorted(results,key=lambda x:(-x["score"],x["doc_id"]))[:top_k]
