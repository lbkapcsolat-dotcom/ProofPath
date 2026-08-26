#!/usr/bin/env python3
import hashlib,json,random
MODEL_ID="ESS_GLOBAL_BLIND_STOCHASTIC_POLICY_V2"
def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def _u01(t,s):
    seed=int.from_bytes(hashlib.sha256(f"{MODEL_ID}|{t}|{s}".encode()).digest()[:8],"big")
    return random.Random(seed).random()
def propose(x):
    # Stochastic proposal metadata is explicitly non-authoritative.
    risk=0.08
    if x["candidate_predecessor_root"]!=x["current_root"]:risk+=0.28
    if x["candidate_epoch"]<=x["current_epoch"]:risk+=0.20
    if x["candidate_fence"]<=x["current_fence"]:risk+=0.28
    if x["available_authority"]=="LOCAL" and x["required_authority"]=="GLOBAL":risk+=0.25
    if x["evidence_support"] and x["evidence_refute"]:risk+=0.22
    if not x["interface_ok"]:risk+=0.25
    if x["operation_seen"] and x.get("prior_successor_root") not in (None,x["candidate_successor_root"]):risk+=0.30
    if (x["dispatch_started"] and x["effect_status"]=="UNKNOWN" and x["requested_action"]=="RETRY"
        and not (x["sink_idempotent"] or x["effect_query_available"])):risk+=0.30
    risk=max(0.0,min(0.98,risk));d=_u01(x["trial_id"],"proposal")
    suggestion="HOLD" if d<risk*0.82 else ("REJECT" if d<risk else "PASS")
    c={"trial_id":x["trial_id"],"model_id":MODEL_ID,
       "candidate_successor_root":x["candidate_successor_root"],"operation_id":x["operation_id"],
       "non_authoritative_suggestion":suggestion}
    c["candidate_hash"]=hashlib.sha256(canonical(c).encode()).hexdigest()
    return c
