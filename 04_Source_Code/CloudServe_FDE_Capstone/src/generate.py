"""Grounded, structured response drafting. No external model is required."""
def draft(ticket, classification, sources):
    if not sources:
        return {"answer":"I’m unable to verify a reliable answer from the current support documentation. I’m escalating this to a support specialist for review.","citations":[]}
    top=sources[0]
    title=top["title"]
    passage=top["passage"]
    # Extract a concise first useful sentence; never claim an action was performed.
    sentences=[s.strip(" -*\n\t") for s in passage.replace("\n"," ").split(".") if len(s.strip())>35]
    guidance=sentences[0][:350] if sentences else title
    answer=(f"Thanks for contacting CloudServe. Based on the support documentation, the most relevant guidance is **{title}**: "
            f"{guidance.rstrip('.')} [${top['doc_id']}]")
    answer=answer.replace("[$","[")
    answer += "\n\nPlease try the documented checks that apply to your setup. If the issue continues, reply with the steps you tried and the outcome so a support specialist can investigate further."
    return {"answer":answer,"citations":[{"doc_id":top["doc_id"],"title":title,"score":top["score"]}]}
