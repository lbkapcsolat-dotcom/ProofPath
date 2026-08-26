#!/usr/bin/env python3
import csv,glob,hashlib,json,sys
from pathlib import Path
EXPECTED_ADAPTER_SHA256="853023d0c7e720432c710be7051362aa3bff532989dce7f44f063bb1bb08c033"
EXPECTED_SCHEDULE_SHA256="f7b1cab83a16e0779a87d5748d0c83c24847bc307c2971f75d42fa6c021b4cd7"
files=sorted(glob.glob("downloaded/**/*.csv",recursive=True))
rows=[]
for p in files:
 with open(p,newline="",encoding="utf-8") as f:rows.extend(csv.DictReader(f))
ids=[r["trial_id"] for r in rows]
unique=len(set(ids));manip=sum(str(r.get("manipulation_check_pass","")).lower() in ("true","1") for r in rows)
counter=[r for r in rows if r.get("authoritative_effect_count","") not in ("",None) and int(r["authoritative_effect_count"])>1]
sha_ok=all(r.get("adapter_sha256")==EXPECTED_ADAPTER_SHA256 and r.get("schedule_sha256")==EXPECTED_SCHEDULE_SHA256 for r in rows)
complete=(len(rows)==12000 and unique==12000 and manip==12000 and sha_ok)
status="PASS" if complete and not counter else ("FAIL" if counter else "HOLD_INCOMPLETE")
Path("merged").mkdir(exist_ok=True)
if rows:
 with open("merged/FAULT_RESULTS.csv","w",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
res={"gate":"ESS_ATB_1_H5_EXACT_FAULT_EXECUTION_ENVIRONMENT_RECOVERY_V1","H5":status,"rows":len(rows),"unique_trial_ids":unique,"manipulation_pass":manip,"counterexamples":len(counter),"adapter_sha256":EXPECTED_ADAPTER_SHA256,"schedule_sha256":EXPECTED_SCHEDULE_SHA256,"exact_frozen_identity":sha_ok}
Path("merged/H5_RESULT.json").write_text(json.dumps(res,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
print(json.dumps(res,indent=2))
if status!="PASS":sys.exit(2)
