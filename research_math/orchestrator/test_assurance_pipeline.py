from __future__ import annotations
import copy
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import claim_router
import assurance_pipeline as ap

def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()

CLAIMS = [
    {'id':'ALG-PASS','text':'2^32 - 1 = 3*5*17*257*65537','claim_class':'exact_algebraic','risk':'standard','domain':'integers','assumptions':[]},
    {'id':'THM-PASS','text':'For every real x, x^2 >= 0','claim_class':'theorem','risk':'high','domain':'real','assumptions':[],'formal_target':'ResearchMathP0.square_nonnegative'},
    {'id':'SAME-FAMILY','text':'Independent exact engines are required','claim_class':'exact_algebraic','risk':'standard','domain':'integers','assumptions':[]},
    {'id':'COUNTEREXAMPLE','text':'A deliberately false theorem canary','claim_class':'theorem','risk':'high','domain':'real','assumptions':[],'formal_target':'Canary.false_theorem'},
    {'id':'NUM-HIGH','text':'A high-risk floating-point approximation','claim_class':'numerical_approximation','risk':'high','domain':'real_numeric','assumptions':['finite inputs']},
]
EVIDENCE = [
    {'claim_id':'ALG-PASS','role':'exact_computation','engine':'sage','status':'PASS','evidence_sha256':h('alg-sage')},
    {'claim_id':'ALG-PASS','role':'independent_exact_crosscheck','engine':'python_exact','status':'PASS','evidence_sha256':h('alg-python')},
    {'claim_id':'THM-PASS','role':'formal_kernel_proof','engine':'lean','status':'PASS','evidence_sha256':h('thm-lean'),'formal_target':'ResearchMathP0.square_nonnegative'},
    {'claim_id':'THM-PASS','role':'independent_countercheck','engine':'sage','status':'PASS','evidence_sha256':h('thm-sage')},
    {'claim_id':'SAME-FAMILY','role':'exact_computation','engine':'wolfram','family':'forged_family_a','status':'PASS','evidence_sha256':h('same-1')},
    {'claim_id':'SAME-FAMILY','role':'independent_exact_crosscheck','engine':'wolfram','family':'forged_family_b','status':'PASS','evidence_sha256':h('same-2')},
    {'claim_id':'COUNTEREXAMPLE','role':'formal_kernel_proof','engine':'lean','status':'PASS','evidence_sha256':h('false-lean'),'formal_target':'Canary.false_theorem'},
    {'claim_id':'COUNTEREXAMPLE','role':'independent_countercheck','engine':'sage','status':'PASS','evidence_sha256':h('false-sage')},
    {'claim_id':'NUM-HIGH','role':'numerical_computation','engine':'python','status':'PASS','evidence_sha256':h('num-python')},
    {'claim_id':'NUM-HIGH','role':'independent_numeric_crosscheck','engine':'precise','status':'PASS','evidence_sha256':h('num-precise')},
]
ADVERSARIAL = [
    {'claim_id':'ALG-PASS','category':'boundary','status':'PASS','evidence_sha256':h('alg-boundary')},
    {'claim_id':'THM-PASS','category':'boundary','status':'PASS','evidence_sha256':h('thm-boundary')},
    {'claim_id':'THM-PASS','category':'counterexample_search','status':'PASS','evidence_sha256':h('thm-search')},
    {'claim_id':'SAME-FAMILY','category':'boundary','status':'PASS','evidence_sha256':h('same-boundary')},
    {'claim_id':'COUNTEREXAMPLE','category':'boundary','status':'PASS','evidence_sha256':h('false-boundary')},
    {'claim_id':'COUNTEREXAMPLE','category':'counterexample_search','status':'COUNTEREXAMPLE_FOUND','evidence_sha256':h('false-counterexample')},
    {'claim_id':'NUM-HIGH','category':'boundary','status':'PASS','evidence_sha256':h('num-boundary')},
    {'claim_id':'NUM-HIGH','category':'counterexample_search','status':'PASS','evidence_sha256':h('num-search')},
]

def by_id(items): return {x['id']:x for x in items}

def run():
    route=claim_router.build_report({'schema':'proofpath.math_claims.v1','claims':CLAIMS})
    dag=ap.build_verification_dag(route)
    assert dag['schema']=='proofpath.math_verification_dag.v1'
    assert by_id(dag['claims'])['ALG-PASS']['status']=='DAG_READY'
    assert by_id(dag['claims'])['THM-PASS']['roles']==['formal_kernel_proof','independent_countercheck']
    assurance=ap.evaluate_assurance(CLAIMS,route,dag,EVIDENCE,ADVERSARIAL); a=by_id(assurance['claims'])
    assert a['ALG-PASS']['quorum']['status']=='QUORUM_PASS'
    assert a['THM-PASS']['adversarial']['status']=='ADVERSARIAL_PASS'
    assert a['SAME-FAMILY']['quorum']['status']=='HOLD_INSUFFICIENT_INDEPENDENCE'
    assert a['COUNTEREXAMPLE']['adversarial']['status']=='HOLD_COUNTEREXAMPLE_FOUND'
    assert a['NUM-HIGH']['escalation']['status']=='HOLD_ESCALATION_REQUIRED'
    assert a['NUM-HIGH']['escalation']['next_required_role']=='rigorous_enclosure'
    assert a['THM-PASS']['formalization']['status']=='FORMALIZATION_BOUND'
    assert a['ALG-PASS']['formalization']['status']=='NOT_REQUIRED'
    receipts=ap.build_proof_receipts(CLAIMS,route,dag,assurance,EVIDENCE,ADVERSARIAL); r=by_id(receipts['receipts'])
    assert r['ALG-PASS']['status']=='RECEIPT_READY' and len(r['ALG-PASS']['receipt_sha256'])==64 and ap.verify_receipt(r['ALG-PASS'])
    tampered=copy.deepcopy(r['ALG-PASS']); tampered['claim']['text']='tampered'; assert not ap.verify_receipt(tampered)
    gate=ap.global_math_gate(CLAIMS,route,dag,assurance,receipts); g=by_id(gate['claims'])
    assert g['ALG-PASS']['status']=='PASS'
    assert g['THM-PASS']['status']=='PASS'
    assert g['SAME-FAMILY']['status']=='HOLD_INSUFFICIENT_INDEPENDENCE'
    assert g['COUNTEREXAMPLE']['status']=='HOLD_COUNTEREXAMPLE_FOUND'
    assert g['NUM-HIGH']['status']=='HOLD_ESCALATION_REQUIRED'
    assert gate['claim_ceiling'].startswith('PASS applies only')
    bundle=ap.build_bundle({'claims':CLAIMS,'evidence':EVIDENCE,'adversarial':ADVERSARIAL})
    assert bundle['schema']=='proofpath.math_assurance_bundle.v1'
    assert by_id(bundle['gate']['claims'])['SAME-FAMILY']['status']=='HOLD_INSUFFICIENT_INDEPENDENCE'
    print('P4 VERIFICATION DAG = PASS'); print('P5 INDEPENDENCE/QUORUM = PASS'); print('P6 ADVERSARIAL GATE = PASS'); print('P7 ESCALATION = PASS'); print('P8 FORMALIZATION BRIDGE = PASS'); print('P9 PROOF RECEIPTS = PASS'); print('P10 GLOBAL MATH GATE = PASS')

if __name__=='__main__': run()
