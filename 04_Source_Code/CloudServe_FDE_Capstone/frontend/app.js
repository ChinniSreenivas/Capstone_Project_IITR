const API_BASE = "http://127.0.0.1:8000";
const $ = (id) => document.getElementById(id);
const state = { total: 0, auto: 0, escalated: 0, hits: 0, recent: [] };
function setApiStatus(online) { $("apiStatus").textContent = online ? "API connected" : "API unavailable"; document.querySelector(".status .status-dot").classList.toggle("online", online); }
async function checkApi() { try { const res = await fetch(`${API_BASE}/health`); if (!res.ok) throw new Error(); setApiStatus(true); } catch { setApiStatus(false); } }
function txt(value, fallback = "—") { return value === undefined || value === null || value === "" ? fallback : String(value); }
function actionLabel(action) { return ({auto_respond:"Auto response",escalate:"Escalated",block:"Blocked"})[action] || txt(action); }
function showResult(data) {
  $("resultSection").classList.remove("hidden");
  $("resultIntent").textContent = txt(data.intent || data.prediction?.value);
  $("resultAction").textContent = actionLabel(data.action_taken);
  $("resultConfidence").textContent = data.confidence !== undefined ? Number(data.confidence).toFixed(2) : txt(data.prediction?.confidence);
  $("resultRetrieval").textContent = data.retrieval_hit ? "Sources found" : "No source hit";
  $("resultStatus").textContent = actionLabel(data.action_taken);
  $("resultAnswer").textContent = data.answer || data.reason || "No automated answer was produced. Please follow the routing decision.";
  $("citationList").replaceChildren();
  (Array.isArray(data.citations) ? data.citations : []).forEach(c => { const span=document.createElement("span"); span.className="citation"; span.textContent=`${txt(c.doc_id,"Document")}${c.title ? " · "+c.title : ""}`; $("citationList").appendChild(span); });
  const needsHuman = data.action_taken === "escalate" || data.action_taken === "block";
  $("escalationBox").classList.toggle("hidden", !needsHuman);
  $("escalationBox").textContent = needsHuman ? `Human review required. ${txt(data.reason,"Please contact support for next steps.")}` : "";
  $("resultSection").scrollIntoView({behavior:"smooth",block:"start"});
}
function updateDashboard() {
  $("metricTotal").textContent=state.total; $("metricAuto").textContent=state.auto; $("metricEscalated").textContent=state.escalated; $("metricHits").textContent=state.hits;
  const tbody=$("recentRows"); tbody.replaceChildren();
  if(!state.recent.length){const tr=document.createElement("tr"),td=document.createElement("td");td.colSpan=5;td.className="empty-row";td.textContent="No tickets submitted in this session yet.";tr.appendChild(td);tbody.appendChild(tr);return;}
  state.recent.forEach(item=>{const tr=document.createElement("tr");[item.ticket_id,item.intent,actionLabel(item.action_taken),item.confidence==null?"—":Number(item.confidence).toFixed(2),item.retrieval_hit?"Yes":"No"].forEach((value,i)=>{const td=document.createElement("td");if(i===2){const pill=document.createElement("span");pill.className="table-pill"+(item.action_taken==="escalate"?" escalate":item.action_taken==="block"?" block":"");pill.textContent=value;td.appendChild(pill);}else td.textContent=txt(value);tr.appendChild(td);});tbody.appendChild(tr);});
}
$("ticketForm").addEventListener("submit", async event => {
  event.preventDefault(); const subject=$("subject").value.trim(), body=$("body").value.trim(); if(!subject||!body)return;
  const button=$("submitBtn"), message=$("formMessage"); button.disabled=true; button.querySelector("span").textContent="Processing…"; message.className="form-message";message.textContent="Sending your ticket to CloudServe…";
  const payload={ticket_id:$("ticketId").value.trim()||`CS-${Date.now().toString().slice(-7)}`,channel:$("channel").value,subject,body,received_at:new Date().toISOString(),customer_tier:$("tier").value,customer_region:$("region").value,language_fluency:"English"};
  try{
    const response=await fetch(`${API_BASE}/tickets`,{method:"POST",headers:{"Content-Type":"application/json","Accept":"application/json"},body:JSON.stringify(payload)});
    const data=await response.json().catch(()=>({})); if(!response.ok)throw new Error(data.detail||`API returned HTTP ${response.status}`);
    showResult(data);state.total++;if(data.action_taken==="auto_respond")state.auto++;if(data.action_taken==="escalate"||data.action_taken==="block")state.escalated++;if(data.retrieval_hit)state.hits++;
    state.recent.unshift({ticket_id:data.ticket_id||payload.ticket_id,intent:data.intent||data.prediction?.value,action_taken:data.action_taken,confidence:data.confidence??data.prediction?.confidence,retrieval_hit:Boolean(data.retrieval_hit)});state.recent=state.recent.slice(0,8);updateDashboard();
    message.className="form-message success";message.textContent=`Ticket ${payload.ticket_id} processed successfully. See the result below.`;
  }catch(error){message.className="form-message error";message.textContent=`Could not submit ticket: ${error.message}. Confirm the FastAPI server is running and CORS is enabled.`;}
  finally{button.disabled=false;button.querySelector("span").textContent="Submit ticket";}
});
$("resetStats").addEventListener("click",()=>{state.total=state.auto=state.escalated=state.hits=0;state.recent=[];updateDashboard();});checkApi();
