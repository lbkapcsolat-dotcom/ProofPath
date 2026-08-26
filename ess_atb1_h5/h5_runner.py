#!/usr/bin/env python3
import argparse,csv,hashlib,importlib.util,json,random,sys,tempfile
from pathlib import Path

MASTER_SEED=20260826
EXPECTED_ADAPTER_SHA256="853023d0c7e720432c710be7051362aa3bff532989dce7f44f063bb1bb08c033"
EXPECTED_SCHEDULE_SHA256="f7b1cab83a16e0779a87d5748d0c83c24847bc307c2971f75d42fa6c021b4cd7"
WINDOWS=["W0_BEFORE_DISPATCH","W1_AFTER_DISPATCH_BEFORE_RESPONSE","W2_AFTER_RESPONSE_BEFORE_PERSIST","W3_AFTER_CAS_BEFORE_RECEIPT","W4_AFTER_RECEIPT_BEFORE_FINALIZATION","W5_AFTER_FINALIZATION_BEFORE_CALLER_RESPONSE"]
REGIMES=[("C1_SINGLE_EXECUTOR",1),("C2_EIGHT_EXECUTORS",8)]

def sha256_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def h(s):return hashlib.sha256(s.encode()).hexdigest()

def regenerate_schedule(path):
 rng=random.Random(MASTER_SEED+1000);rows=[];counter=0
 for w in WINDOWS:
  for regime,n_exec in REGIMES:
   for _ in range(1000):
    counter+=1;fault_seed=rng.randrange(1,2**63);trial_id=f"FAULT-{counter:05d}"
    rows.append({"trial_id":trial_id,"window":w,"concurrency_regime":regime,"executor_count":n_exec,"fault_seed":fault_seed,"operation_id":h(f"{trial_id}|{fault_seed}|op")[:32],"crash_offset_fraction":round(random.Random(fault_seed).random(),12)})
 with open(path,"w",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
 return rows

def load_adapter(path):
 spec=importlib.util.spec_from_file_location("frozen_fault_adapter",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--window",required=True);ap.add_argument("--executors",required=True,type=int);ap.add_argument("--out",required=True);a=ap.parse_args()
 adapter=Path(__file__).with_name("fault_adapter.py")
 actual_adapter=sha256_file(adapter)
 if actual_adapter!=EXPECTED_ADAPTER_SHA256:raise SystemExit(f"ADAPTER_SHA_MISMATCH {actual_adapter}")
 with tempfile.TemporaryDirectory() as td:
  sp=Path(td)/"schedule.csv";rows=regenerate_schedule(sp);actual_schedule=sha256_file(sp)
  if actual_schedule!=EXPECTED_SCHEDULE_SHA256:raise SystemExit(f"SCHEDULE_SHA_MISMATCH {actual_schedule}")
  selected=[r for r in rows if r["window"]==a.window and int(r["executor_count"])==a.executors]
  if len(selected)!=1000:raise SystemExit(f"CELL_COUNT_MISMATCH {len(selected)}")
  mod=load_adapter(adapter);out=[]
  for i,r in enumerate(selected,1):
   try:
    x=mod.run(r["window"],int(r["executor_count"]),r["operation_id"])
    rec={**r,**x,"adapter_sha256":actual_adapter,"schedule_sha256":actual_schedule,"error":""}
   except BaseException as e:
    rec={**r,"authoritative_effect_count":"","manipulation_check_pass":False,"finalized":False,"receipt_phase":"","root":"","epoch":"","fence":"","adapter_sha256":actual_adapter,"schedule_sha256":actual_schedule,"error":repr(e)}
    out.append(rec);break
   out.append(rec)
   if i%100==0:print(f"PROGRESS {a.window} n={a.executors} {i}/1000",flush=True)
 fields=list(out[0]);Path(a.out).parent.mkdir(parents=True,exist_ok=True)
 with open(a.out,"w",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader();wr.writerows(out)
 if len(out)!=1000 or any(str(r.get("manipulation_check_pass")).lower() not in ("true","1") for r in out):raise SystemExit("CELL_INCOMPLETE_OR_MANIPULATION_FAILURE")
 print(json.dumps({"window":a.window,"executors":a.executors,"rows":len(out),"counterexamples":sum(int(r["authoritative_effect_count"])>1 for r in out),"adapter_sha256":actual_adapter,"schedule_sha256":actual_schedule},sort_keys=True))

if __name__=="__main__":main()
