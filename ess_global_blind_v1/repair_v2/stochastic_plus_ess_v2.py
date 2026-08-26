#!/usr/bin/env python3
import json,sys,time
from common_v2 import propose
ARM_ID="STOCHASTIC_PLUS_ESS_V2";RANK={"LOCAL":0,"BOUNDED":1,"GLOBAL":2}
def admit(x):
    hard=[];hold=[]
    if x["candidate_predecessor_root"]!=x["current_root"]:hard.append("PREDECESSOR_ROOT_MISMATCH")
    if x["candidate_epoch"]<=x["current_epoch"]:hard.append("NON_MONOTONIC_EPOCH")
    if x["candidate_fence"]<=x["current_fence"]:hard.append("STALE_OR_NON_MONOTONIC_FENCE")
    if RANK[x["available_authority"]]<RANK[x["required_authority"]]:hard.append("INSUFFICIENT_AUTHORITY")
    if x["evidence_support"] and x["evidence_refute"]:hold.append("UNRESOLVED_EVIDENCE_CONFLICT")
    if not x["interface_ok"]:hard.append("INTERFACE_VIOLATION")
    if x["operation_seen"] and x.get("prior_successor_root") not in (None,x["candidate_successor_root"]):hard.append("DIVERGENT_DUPLICATE_OPERATION")
    if (x["dispatch_started"] and x["effect_status"]=="UNKNOWN" and x["requested_action"]=="RETRY"
        and not (x["sink_idempotent"] or x["effect_query_available"])):hold.append("AMBIGUOUS_DISPATCH_NO_SAFE_RETRY_PROOF")
    if hard:return "REJECT",hard+hold
    if hold:return "HOLD",hold
    return "PASS",[]
def run(x):
    c=propose(x);t=time.perf_counter_ns();d,r=admit(x);ms=(time.perf_counter_ns()-t)/1e6
    fin=d=="PASS"
    return {"trial_id":x["trial_id"],"arm_id":ARM_ID,"decision":d,"finalized":fin,
      "finalized_within_5s":fin,"decision_latency_ms":ms,"incremental_ess_latency_ms":ms,
      "candidate_hash":c["candidate_hash"],"candidate_model_id":c["model_id"],
      "non_authoritative_suggestion":c["non_authoritative_suggestion"],"reasons":r}
if __name__=="__main__":print(json.dumps(run(json.load(sys.stdin)),sort_keys=True,separators=(",",":")))
