from __future__ import annotations
import hashlib, json, re
from copy import deepcopy
from typing import Any

HEX64=re.compile(r'^[0-9a-f]{64}$')
ENGINE_FAMILIES={'sage':'cas_sage','wolfram':'cas_wolfram','python':'python_runtime','python_exact':'python_runtime','precise':'precise_special_functions','arb':'flint_arb','lean':'lean_kernel','julia':'julia_runtime'}

def _hash(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def _map(xs): return {str(x.get('id','')):x for x in xs}
def _h(x): return isinstance(x,str) and HEX64.fullmatch(x) is not None

def build_verification_dag(route_report):
    out=[]
    for r in route_report.get('claims',[]):
        cid=str(r.get('id',''))
        if r.get('status')!='ROUTE_READY':
            out.append({'id':cid,'status':'HOLD_UPSTREAM_ROUTER','upstream_status':r.get('status'),'roles':[],'nodes':[],'edges':[]}); continue
        roles=list(r.get('required_roles',[])); nodes=[{'id':f'claim:{cid}','kind':'claim'}]; edges=[]
        for role in roles:
            rid=f'role:{cid}:{role}'; nodes.append({'id':rid,'kind':'proof_role','role':role}); edges.append({'source':f'claim:{cid}','target':rid})
            for eng in r.get('engine_candidates',{}).get(role,[]):
                eid=f'engine:{cid}:{role}:{eng}'; nodes.append({'id':eid,'kind':'engine_candidate','engine':eng,'family':ENGINE_FAMILIES.get(eng)}); edges.append({'source':rid,'target':eid})
        body={'id':cid,'roles':roles,'nodes':nodes,'edges':edges}; out.append({**body,'status':'DAG_READY','dag_sha256':_hash(body)})
    return {'schema':'proofpath.math_verification_dag.v1','claims':out,'claim_ceiling':'P4 defines obligations and candidate execution paths; it does not prove any claim.'}

def _quorum(claim,route,evidence):
    selected=[]; cid=str(claim['id']); roles=list(route.get('required_roles',[])); candidates=route.get('engine_candidates',{})
    for role in roles:
        xs=[e for e in evidence if e.get('claim_id')==cid and e.get('role')==role and e.get('status')=='PASS' and e.get('engine') in candidates.get(role,[])]
        if not xs:return {'status':'HOLD_INSUFFICIENT_EVIDENCE','missing_role':role}
        xs.sort(key=lambda e:(str(e.get('engine')),str(e.get('evidence_sha256')))); x=deepcopy(xs[0])
        if not _h(x.get('evidence_sha256')):return {'status':'HOLD_BAD_EVIDENCE_HASH','role':role}
        fam=ENGINE_FAMILIES.get(str(x.get('engine')))
        if fam is None:return {'status':'HOLD_UNKNOWN_ENGINE_FAMILY','role':role}
        x.pop('family',None); x['family']=fam; selected.append(x)
    fams=[x['family'] for x in selected]; engines=[str(x['engine']) for x in selected]
    if len(set(fams))!=len(roles) or len(set(engines))!=len(roles):return {'status':'HOLD_INSUFFICIENT_INDEPENDENCE','engines':engines,'families':fams}
    return {'status':'QUORUM_PASS','engines':engines,'families':fams,'selected_evidence':selected}

def _adversarial(claim,records):
    xs=[x for x in records if x.get('claim_id')==claim['id']]
    for x in xs:
        if not _h(x.get('evidence_sha256')):return {'status':'HOLD_BAD_ADVERSARIAL_HASH','category':x.get('category')}
    hit=next((x for x in xs if x.get('status')=='COUNTEREXAMPLE_FOUND'),None)
    if hit:return {'status':'HOLD_COUNTEREXAMPLE_FOUND','category':hit.get('category'),'evidence_sha256':hit.get('evidence_sha256')}
    need={'boundary'}|({'counterexample_search'} if claim.get('risk') in {'high','critical'} else set()); passed={str(x.get('category')) for x in xs if x.get('status')=='PASS'}; missing=sorted(need-passed)
    if missing:return {'status':'HOLD_ADVERSARIAL_INCOMPLETE','missing_categories':missing}
    return {'status':'ADVERSARIAL_PASS','categories':sorted(need),'evidence_sha256':sorted(x['evidence_sha256'] for x in xs if x.get('category') in need)}

def _escalation(c):
    return {'status':'HOLD_ESCALATION_REQUIRED','next_required_role':'rigorous_enclosure','target_claim_class':'rigorous_numerical'} if c.get('claim_class')=='numerical_approximation' and c.get('risk') in {'high','critical'} else {'status':'ESCALATION_RESOLVED'}

def _formal(c,q):
    if c.get('claim_class')!='theorem':return {'status':'NOT_REQUIRED'}
    target=str(c.get('formal_target','')).strip()
    if not target:return {'status':'HOLD_FORMALIZATION_TARGET'}
    if q.get('status')!='QUORUM_PASS':return {'status':'HOLD_FORMALIZATION_UPSTREAM'}
    xs=[e for e in q.get('selected_evidence',[]) if e.get('role')=='formal_kernel_proof' and e.get('engine')=='lean']
    if not xs:return {'status':'HOLD_FORMALIZATION_EVIDENCE'}
    if xs[0].get('formal_target')!=target:return {'status':'HOLD_FORMALIZATION_EVIDENCE_MISMATCH','expected_target':target,'evidence_target':xs[0].get('formal_target')}
    return {'status':'FORMALIZATION_BOUND','formal_target':target,'formal_evidence_sha256':xs[0]['evidence_sha256']}

def evaluate_assurance(claims,route_report,dag_report,evidence,adversarial):
    routes=_map(route_report.get('claims',[])); dags=_map(dag_report.get('claims',[])); out=[]
    for c in claims:
        cid=str(c['id']); r=routes.get(cid,{}); d=dags.get(cid,{})
        if r.get('status')!='ROUTE_READY' or d.get('status')!='DAG_READY':
            hold={'status':'HOLD_UPSTREAM_ROUTING'}; out.append({'id':cid,'quorum':hold,'adversarial':hold,'escalation':hold,'formalization':hold}); continue
        q=_quorum(c,r,evidence); out.append({'id':cid,'quorum':q,'adversarial':_adversarial(c,adversarial),'escalation':_escalation(c),'formalization':_formal(c,q)})
    return {'schema':'proofpath.math_assurance.report.v1','claims':out,'claim_ceiling':'P5-P8 evaluate evidence independence, falsification pressure, escalation, and formal binding only.'}

def _ready(r,d,a):
    return r.get('status')=='ROUTE_READY' and d.get('status')=='DAG_READY' and a.get('quorum',{}).get('status')=='QUORUM_PASS' and a.get('adversarial',{}).get('status')=='ADVERSARIAL_PASS' and a.get('escalation',{}).get('status')=='ESCALATION_RESOLVED' and a.get('formalization',{}).get('status') in {'FORMALIZATION_BOUND','NOT_REQUIRED'}

def build_proof_receipts(claims,route_report,dag_report,assurance_report,evidence,adversarial):
    routes=_map(route_report.get('claims',[])); dags=_map(dag_report.get('claims',[])); ass=_map(assurance_report.get('claims',[])); out=[]
    for c in claims:
        cid=str(c['id']); r=deepcopy(routes.get(cid,{})); d=deepcopy(dags.get(cid,{})); a=deepcopy(ass.get(cid,{}))
        body={'schema':'proofpath.math_proof_receipt.v1','id':cid,'status':'RECEIPT_READY' if _ready(r,d,a) else 'HOLD_UPSTREAM_ASSURANCE','claim':deepcopy(c),'route':r,'dag':{'status':d.get('status'),'roles':deepcopy(d.get('roles',[])),'dag_sha256':d.get('dag_sha256')},'assurance':a,'evidence':sorted((deepcopy(x) for x in evidence if x.get('claim_id')==cid),key=lambda x:(str(x.get('role')),str(x.get('engine')),str(x.get('evidence_sha256')))),'adversarial_evidence':sorted((deepcopy(x) for x in adversarial if x.get('claim_id')==cid),key=lambda x:(str(x.get('category')),str(x.get('status')),str(x.get('evidence_sha256')))),'claim_ceiling':'Receipt binds this exact claim, routing decision, evidence, and assurance state only.'}
        body['receipt_sha256']=_hash(body); out.append(body)
    return {'schema':'proofpath.math_proof_receipts.v1','receipts':out}

def verify_receipt(receipt):
    digest=receipt.get('receipt_sha256')
    if not _h(digest):return False
    body=deepcopy(receipt); body.pop('receipt_sha256',None); return _hash(body)==digest

def global_math_gate(claims,route_report,dag_report,assurance_report,receipt_report):
    routes=_map(route_report.get('claims',[])); dags=_map(dag_report.get('claims',[])); ass=_map(assurance_report.get('claims',[])); rec=_map(receipt_report.get('receipts',[])); out=[]
    for c in claims:
        cid=str(c['id']); r=routes.get(cid,{}); d=dags.get(cid,{}); a=ass.get(cid,{}); p=rec.get(cid,{})
        if r.get('status')!='ROUTE_READY':s=r.get('status','HOLD_ROUTER_MISSING')
        elif d.get('status')!='DAG_READY':s=d.get('status','HOLD_DAG_MISSING')
        elif a.get('quorum',{}).get('status')!='QUORUM_PASS':s=a.get('quorum',{}).get('status','HOLD_QUORUM_MISSING')
        elif a.get('adversarial',{}).get('status')!='ADVERSARIAL_PASS':s=a.get('adversarial',{}).get('status','HOLD_ADVERSARIAL_MISSING')
        elif a.get('escalation',{}).get('status')!='ESCALATION_RESOLVED':s=a.get('escalation',{}).get('status','HOLD_ESCALATION_MISSING')
        elif a.get('formalization',{}).get('status') not in {'FORMALIZATION_BOUND','NOT_REQUIRED'}:s=a.get('formalization',{}).get('status','HOLD_FORMALIZATION_MISSING')
        elif p.get('status')!='RECEIPT_READY' or not verify_receipt(p):s='HOLD_BAD_PROOF_RECEIPT'
        else:s='PASS'
        out.append({'id':cid,'status':s,'receipt_sha256':p.get('receipt_sha256') if s=='PASS' else None})
    return {'schema':'proofpath.global_math_gate.v1','claims':out,'claim_ceiling':'PASS applies only to the individual claim and evidence bound into its verified proof receipt; it does not generalize to other claims or future runs.'}

def build_bundle(payload):
    import claim_router
    claims=list(payload.get('claims',[])); route=claim_router.build_report({'schema':'proofpath.math_claims.v1','claims':claims}); dag=build_verification_dag(route); assurance=evaluate_assurance(claims,route,dag,list(payload.get('evidence',[])),list(payload.get('adversarial',[]))); receipts=build_proof_receipts(claims,route,dag,assurance,list(payload.get('evidence',[])),list(payload.get('adversarial',[]))); gate=global_math_gate(claims,route,dag,assurance,receipts)
    return {'schema':'proofpath.math_assurance_bundle.v1','route':route,'dag':dag,'assurance':assurance,'receipts':receipts,'gate':gate,'claim_ceiling':gate['claim_ceiling']}
