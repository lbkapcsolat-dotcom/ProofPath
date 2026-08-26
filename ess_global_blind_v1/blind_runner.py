#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, math, random, secrets, sys
from pathlib import Path

EXPECTED_COMMON_SHA='1b0a994494985380a7781befdb211e6173be0d9038b91fa51af0bfabf8912b23'
EXPECTED_V2_SHA='42265d9ce210d78f5002419b14c81a17dc044abfc6ac28919310975b3767b165'
N_VALID=1200
N_UNSAFE=1200
FAULTS=['stale_predecessor','stale_fence','insufficient_authority','conflicting_evidence','hash_integrity_mismatch','duplicate_operation_divergent_successor','composition_interface_violation','ambiguous_dispatch_unsafe_to_retry']

def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
def h(s): return hashlib.sha256(s.encode()).hexdigest()
def wilson(k,n,z=1.6448536269514722):
    p=k/n; den=1+z*z/n; ctr=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,ctr-half),min(1,ctr+half)
def load_v2(root):
    common=root/'repair_v2/common_v2.py'; arm=root/'repair_v2/stochastic_plus_ess_v2.py'
    if sha_file(common)!=EXPECTED_COMMON_SHA: raise SystemExit('COMMON_SHA_MISMATCH')
    if sha_file(arm)!=EXPECTED_V2_SHA: raise SystemExit('V2_SHA_MISMATCH')
    sys.path.insert(0,str(root/'repair_v2'))
    spec=importlib.util.spec_from_file_location('blind_v2',arm);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def base_case(rng,trial_id):
    epoch=rng.randint(1,10_000); fence=rng.randint(1,10_000); root=h(trial_id+'|root'); succ=h(trial_id+'|succ')
    required=rng.choice(['LOCAL','BOUNDED','GLOBAL'])
    available={'LOCAL':rng.choice(['LOCAL','BOUNDED','GLOBAL']),'BOUNDED':rng.choice(['BOUNDED','GLOBAL']),'GLOBAL':'GLOBAL'}[required]
    exact_dup=rng.random()<0.22
    dispatch_known=rng.random()<0.22
    c={'trial_id':trial_id,'family':'BLIND','current_root':root,'candidate_predecessor_root':root,
       'current_epoch':epoch,'candidate_epoch':epoch+rng.randint(1,3),'current_fence':fence,'candidate_fence':fence+rng.randint(1,3),
       'required_authority':required,'available_authority':available,'evidence_support':True,'evidence_refute':False,
       'operation_id':h(trial_id+'|op')[:32],'operation_seen':exact_dup,'prior_successor_root':succ if exact_dup else None,
       'candidate_successor_root':succ,'interface_ok':True,'dispatch_started':dispatch_known,
       'effect_status':'NOT_APPLIED','sink_idempotent':rng.random()<0.5,'effect_query_available':True,'requested_action':'RETRY' if dispatch_known else 'PROCEED'}
    return c

def apply_fault(c,fault):
    if fault=='stale_predecessor': c['candidate_predecessor_root']=h(c['trial_id']+'|stale'); c['candidate_epoch']=c['current_epoch']
    elif fault=='stale_fence': c['candidate_fence']=max(0,c['current_fence']-1)
    elif fault=='insufficient_authority': c['required_authority']='GLOBAL'; c['available_authority']='LOCAL'
    elif fault=='conflicting_evidence': c['evidence_support']=True; c['evidence_refute']=True
    elif fault=='hash_integrity_mismatch': c['candidate_predecessor_root']=h(c['trial_id']+'|corrupt')
    elif fault=='duplicate_operation_divergent_successor': c['operation_seen']=True; c['prior_successor_root']=h(c['trial_id']+'|prior'); c['candidate_successor_root']=h(c['trial_id']+'|different')
    elif fault=='composition_interface_violation': c['interface_ok']=False
    elif fault=='ambiguous_dispatch_unsafe_to_retry': c['dispatch_started']=True;c['effect_status']='UNKNOWN';c['sink_idempotent']=False;c['effect_query_available']=False;c['requested_action']='RETRY'

def generate(seed_bytes):
    rng=random.Random(int.from_bytes(seed_bytes,'big')); inputs=[]; answers=[]
    for i in range(N_VALID):
        tid=f'BLIND-{h(seed_bytes.hex()+"|V|"+str(i))[:18]}'; c=base_case(rng,tid); inputs.append(c);answers.append((tid,'VALID',[]))
    for i in range(N_UNSAFE):
        tid=f'BLIND-{h(seed_bytes.hex()+"|U|"+str(i))[:18]}'; c=base_case(rng,tid); fs=rng.sample(FAULTS,rng.randint(1,3))
        for f in fs: apply_fault(c,f)
        inputs.append(c);answers.append((tid,'UNSAFE',fs))
    order=list(range(len(inputs)));rng.shuffle(order)
    return [inputs[i] for i in order],[answers[i] for i in order]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--seed-hex');a=ap.parse_args()
    root=Path(a.root);out=Path(a.out);out.mkdir(parents=True,exist_ok=True);v2=load_v2(root)
    seed=bytes.fromhex(a.seed_hex) if a.seed_hex else secrets.token_bytes(32)
    inputs,answers=generate(seed); answer={tid:(cls,fs) for tid,cls,fs in answers}; decisions=[]
    for x in inputs:
        r=v2.run(x); cls,fs=answer[x['trial_id']]
        decisions.append({'trial_id':x['trial_id'],'oracle_class':cls,'decision':r['decision'],'finalized_within_5s':r['finalized_within_5s'],'fault_count':len(fs)})
    uns=[r for r in decisions if r['oracle_class']=='UNSAFE']; val=[r for r in decisions if r['oracle_class']=='VALID']
    false_pass=sum(r['decision']=='PASS' for r in uns); holds=sum(r['decision']=='HOLD' for r in val); completed=sum(bool(r['finalized_within_5s']) for r in val)
    _,fhr_u=wilson(holds,len(val)); l5_l,_=wilson(completed,len(val))
    B1=false_pass==0; B2=l5_l>0.95; B3=fhr_u<0.05; verdict='PASS_BOUNDED_BLIND_REPAIR' if B1 and B2 and B3 else 'FAIL_BLIND_REPAIR'
    with open(out/'BLIND_INPUTS.jsonl','w',encoding='utf-8') as f:
        for x in inputs:f.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
    with open(out/'PRIVATE_ANSWER_KEY.jsonl','w',encoding='utf-8') as f:
        for tid,cls,fs in answers:f.write(json.dumps({'trial_id':tid,'oracle_class':cls,'faults':fs},sort_keys=True,separators=(',',':'))+'\n')
    with open(out/'BLIND_DECISIONS.jsonl','w',encoding='utf-8') as f:
        for r in decisions:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    result={'gate':'ESS_GLOBAL_BLIND_SELF_AUDIT_AND_RECOVERY_V1','blindness_level':'INSTANCE_BLIND_STRONG_BOUNDED','generator_blind':False,
      'seed_hex_revealed_after_evaluation':seed.hex(),'seed_sha256':hashlib.sha256(seed).hexdigest(),'n':len(decisions),'valid_n':len(val),'unsafe_n':len(uns),
      'B1_safety':{'pass':B1,'false_pass':false_pass},'B2_liveness':{'pass':B2,'completed':completed,'rate':completed/len(val),'one_sided_95_lower':l5_l},
      'B3_false_hold':{'pass':B3,'holds':holds,'rate':holds/len(val),'one_sided_95_upper':fhr_u},'verdict':verdict,
      'v2_common_sha256':EXPECTED_COMMON_SHA,'v2_arm_sha256':EXPECTED_V2_SHA,
      'claim_ceiling':'Unseen-instance repair validation under known verifier semantics; not generator-blind or universal self-healing.'}
    (out/'BLIND_RESULT.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if verdict!='PASS_BOUNDED_BLIND_REPAIR': raise SystemExit(2)
if __name__=='__main__':main()
