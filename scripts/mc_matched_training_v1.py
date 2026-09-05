import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
import os
import platform
import time
import urllib.request
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

GATE = 'MC_MATCHED_TRAINING_ABLATION_SMALL_MODEL_4_SEED_PAIRED_EXECUTION_AND_REPLAY_V1'
PASS_LABEL = 'PASS_BOUNDED_SMALL_MODEL_MATCHED_TRAINING_CAUSAL_EFFECT'
DATA_URL = 'https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt'
DATA_BYTES = 1115394
DATA_SHA256 = '86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed'
TRAIN_RANGE = (0, 1003854)
VAL_RANGE = (1003854, 1059624)
TEST_RANGE = (1059624, 1115394)
SEEDS = [3506515047, 2029779934, 2790631980, 3053553163]
REPLAY_SEED = 3506515047
EXPECTED_INIT = {
    3506515047: 'f00756ac9691e2d5611f7ae27994c96085241fd42da8ca8b61e991ed8dbe05fd',
    2029779934: '2ece1a244a525273d0faba97e9404af6d212664f1782711c462c363766ef6525',
    2790631980: '3af19d451f0a7bc2090e2e72ef4dd5645d0b2db3abaeaefb75a7cce4c68353dd',
    3053553163: 'e111e8f85f119aa2e5fee096d4b06c537ce9ac353624a4602b353c7e1cf39220',
}
VOCAB = 256
D = 128
SEQ = 128
SEG = 16
BATCH = 16
STEPS = 1024
CHECKPOINTS = [0,128,256,384,512,640,768,896,1024]
THREADS = 2
PER_ARM_TRAIN_LIMIT_S = 180.0
TOTAL_LIMIT_S = 1800.0


class SmallMCByteLM(nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, D)
        self.rnn = nn.GRU(D, D, batch_first=True)
        self.q = nn.Linear(D, D)
        self.k = nn.Linear(D, D)
        self.v = nn.Linear(D, D)
        self.o = nn.Linear(D, D)
        self.norm = nn.LayerNorm(D)
        self.head = nn.Linear(D, VOCAB)

    def forward(self, x, mc_scale: float):
        z = self.emb(x)
        h, _ = self.rnn(z)
        idx = torch.arange(SEG - 1, x.shape[1], SEG, device=x.device)
        cache = h.index_select(1, idx)
        q = self.q(h)
        k = self.k(cache)
        v = self.v(cache)
        scores = torch.einsum('btd,bnd->btn', q, k) / math.sqrt(D)
        tpos = torch.arange(x.shape[1], device=x.device).view(1, x.shape[1], 1)
        cpos = idx.view(1, 1, -1)
        mask = cpos < tpos
        scores = scores.masked_fill(~mask, -1e9)
        attn = torch.softmax(scores, dim=-1)
        attn = torch.where(mask.any(dim=-1, keepdim=True), attn, torch.zeros_like(attn))
        mem = torch.einsum('btn,bnd->btd', attn, v)
        y = self.norm(h + float(mc_scale) * self.o(mem))
        return self.head(y)


def param_signature(model):
    return [(n, tuple(p.shape), str(p.dtype), p.numel()) for n, p in model.named_parameters()]


def param_sha256(model):
    h = hashlib.sha256()
    for name, p in model.named_parameters():
        h.update(name.encode())
        h.update(p.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def percentile_linear(sorted_values, q):
    if not sorted_values:
        raise ValueError('empty values')
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values)-1) * q
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_values[lo])
    w = pos - lo
    return float(sorted_values[lo] * (1-w) + sorted_values[hi] * w)


def exhaustive_bootstrap_ci(values):
    vals = [float(x) for x in values]
    n = len(vals)
    means = []
    for inds in itertools.product(range(n), repeat=n):
        means.append(sum(vals[i] for i in inds)/n)
    means.sort()
    return percentile_linear(means, 0.025), percentile_linear(means, 0.975)


def loso_means(values):
    vals = [float(x) for x in values]
    return [sum(vals[:i] + vals[i+1:])/(len(vals)-1) for i in range(len(vals))]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def download_dataset(cache_path: Path):
    if cache_path.exists():
        raw = cache_path.read_bytes()
    else:
        with urllib.request.urlopen(DATA_URL, timeout=60) as r:
            raw = r.read()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(raw)
    if len(raw) != DATA_BYTES:
        raise RuntimeError(f'HOLD_DATASET_BYTES size={len(raw)} expected={DATA_BYTES}')
    got = sha_bytes(raw)
    if got != DATA_SHA256:
        raise RuntimeError(f'HOLD_DATASET_BYTES sha256={got} expected={DATA_SHA256}')
    return raw


def bytes_to_long(b):
    return torch.tensor(bytearray(b), dtype=torch.uint8).to(torch.long)


def window_starts(n_bytes):
    return list(range(0, n_bytes - (SEQ+1) + 1, SEQ))


def make_batch(stream, starts):
    rows = [stream[s:s+SEQ+1] for s in starts]
    z = torch.stack(rows)
    return z[:, :-1], z[:, 1:]


def evaluate(model, stream, mc_scale):
    starts = window_starts(len(stream))
    total_loss = 0.0
    total_tokens = 0
    model.eval()
    with torch.no_grad():
        for i in range(0, len(starts), BATCH):
            ss = starts[i:i+BATCH]
            x, y = make_batch(stream, ss)
            logits = model(x, mc_scale)
            loss_sum = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1), reduction='sum')
            total_loss += float(loss_sum)
            total_tokens += int(y.numel())
    nll = total_loss/total_tokens
    return {'nll': nll, 'ppl': math.exp(nll), 'tokens': total_tokens, 'windows': len(starts)}


def train_arm(seed, treatment, base_state, train_stream, val_stream, test_stream, total_t0):
    mc_scale = 1.0 if treatment == 'MC_ON' else 0.0
    model = SmallMCByteLM()
    model.load_state_dict(copy.deepcopy(base_state))
    init_hash = param_sha256(model)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9,0.95), eps=1e-8, weight_decay=0.01)
    starts = window_starts(len(train_stream))
    cursor = 0
    curve = []
    curve.append({'step': 0, **evaluate(model, val_stream, mc_scale)})
    train_t0 = time.perf_counter()
    last_loss = None
    for step in range(1, STEPS+1):
        if time.perf_counter() - train_t0 > PER_ARM_TRAIN_LIMIT_S:
            raise RuntimeError(f'HOLD_ZERO_SPEND_EXECUTION_SURFACE per-arm training > {PER_ARM_TRAIN_LIMIT_S}s')
        if time.perf_counter() - total_t0 > TOTAL_LIMIT_S:
            raise RuntimeError(f'HOLD_ZERO_SPEND_EXECUTION_SURFACE total > {TOTAL_LIMIT_S}s')
        ss=[]
        for _ in range(BATCH):
            ss.append(starts[cursor])
            cursor = (cursor + 1) % len(starts)
        x,y = make_batch(train_stream, ss)
        model.train()
        opt.zero_grad(set_to_none=True)
        logits = model(x, mc_scale)
        loss = F.cross_entropy(logits.reshape(-1,VOCAB), y.reshape(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        last_loss = float(loss.detach())
        if step in CHECKPOINTS:
            curve.append({'step': step, **evaluate(model, val_stream, mc_scale)})
    train_seconds = time.perf_counter() - train_t0
    test_native = evaluate(model, test_stream, mc_scale)
    test_cross = evaluate(model, test_stream, 1.0-mc_scale)
    return {
        'seed': seed,
        'treatment': treatment,
        'mc_scale': mc_scale,
        'initial_parameter_sha256': init_hash,
        'final_parameter_sha256': param_sha256(model),
        'train_seconds': train_seconds,
        'last_train_loss': last_loss,
        'validation_curve': curve,
        'test_native': test_native,
        'test_cross_scale': 1.0-mc_scale,
        'test_cross': test_cross,
    }


def trapz_auc(curve):
    pts = sorted((int(x['step']), float(x['nll'])) for x in curve)
    area = 0.0
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        area += (x1-x0)*(y0+y1)/2
    return area/(pts[-1][0]-pts[0][0])


def exact_sign_test_two_sided(values):
    n = sum(1 for x in values if x != 0)
    k = sum(1 for x in values if x > 0)
    if n == 0: return 1.0
    tail_k = max(k, n-k)
    tail = sum(math.comb(n,i) for i in range(tail_k,n+1))/(2**n)
    return min(1.0, 2*tail)


def main(outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(THREADS)
    torch.use_deterministic_algorithms(True)
    total_t0 = time.perf_counter()

    raw = download_dataset(outdir/'tinyshakespeare_input.txt')
    train_b = raw[slice(*TRAIN_RANGE)]; val_b = raw[slice(*VAL_RANGE)]; test_b = raw[slice(*TEST_RANGE)]
    data_receipt = {
        'raw_bytes': len(raw), 'raw_sha256': sha_bytes(raw),
        'train_bytes': len(train_b), 'train_sha256': sha_bytes(train_b),
        'validation_bytes': len(val_b), 'validation_sha256': sha_bytes(val_b),
        'test_bytes': len(test_b), 'test_sha256': sha_bytes(test_b),
    }
    train_stream = bytes_to_long(train_b); val_stream = bytes_to_long(val_b); test_stream = bytes_to_long(test_b)

    results = []
    parity = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        base = SmallMCByteLM()
        if sum(p.numel() for p in base.parameters()) != 231168:
            raise RuntimeError('HOLD_PARITY_BROKEN parameter_count')
        init_hash = param_sha256(base)
        expected = EXPECTED_INIT[seed]
        if init_hash != expected:
            raise RuntimeError(f'HOLD_PREOUTCOME_RUNTIME_INIT_HASH seed={seed} got={init_hash} expected={expected}')
        base_state = copy.deepcopy(base.state_dict())
        on_probe = SmallMCByteLM(); on_probe.load_state_dict(copy.deepcopy(base_state))
        off_probe = SmallMCByteLM(); off_probe.load_state_dict(copy.deepcopy(base_state))
        if param_signature(on_probe) != param_signature(off_probe) or param_sha256(on_probe) != param_sha256(off_probe):
            raise RuntimeError(f'HOLD_PARITY_BROKEN seed={seed}')
        parity.append({'seed':seed,'expected_init_sha256':expected,'actual_init_sha256':init_hash,'on_off_equal':True})
        results.append(train_arm(seed,'MC_ON',base_state,train_stream,val_stream,test_stream,total_t0))
        results.append(train_arm(seed,'MC_OFF',base_state,train_stream,val_stream,test_stream,total_t0))

    by_seed = {}
    for seed in SEEDS:
        on = next(r for r in results if r['seed']==seed and r['treatment']=='MC_ON')
        off = next(r for r in results if r['seed']==seed and r['treatment']=='MC_OFF')
        by_seed[seed] = {
            'delta_test_nll_off_minus_on': off['test_native']['nll'] - on['test_native']['nll'],
            'delta_test_ppl_off_minus_on': off['test_native']['ppl'] - on['test_native']['ppl'],
            'delta_validation_auc_off_minus_on': trapz_auc(off['validation_curve']) - trapz_auc(on['validation_curve']),
            'inference_knockout_on_trained_delta_nll': on['test_cross']['nll'] - on['test_native']['nll'],
            'common_mc_off_training_effect_nll_offtrain_minus_ontrain': off['test_native']['nll'] - on['test_cross']['nll'],
            'common_mc_on_training_effect_nll_offtrain_minus_ontrain': off['test_cross']['nll'] - on['test_native']['nll'],
        }

    deltas = [by_seed[s]['delta_test_nll_off_minus_on'] for s in SEEDS]
    ppl_deltas = [by_seed[s]['delta_test_ppl_off_minus_on'] for s in SEEDS]
    auc_deltas = [by_seed[s]['delta_validation_auc_off_minus_on'] for s in SEEDS]
    ci = exhaustive_bootstrap_ci(deltas)
    loso = loso_means(deltas)
    positive_sum = sum(max(0.0,x) for x in deltas)
    max_contribution = max((max(0.0,x)/positive_sum if positive_sum else 1.0) for x in deltas)
    mean_delta = sum(deltas)/len(deltas)
    mean_ppl_delta = sum(ppl_deltas)/len(ppl_deltas)
    mean_auc_delta = sum(auc_deltas)/len(auc_deltas)

    criteria = {
        'mean_test_nll_delta_positive': mean_delta > 0,
        'bootstrap_95_ci_lower_positive': ci[0] > 0,
        'all_loso_mean_deltas_positive': all(x > 0 for x in loso),
        'mean_ppl_delta_positive': mean_ppl_delta > 0,
        'mean_validation_auc_delta_positive': mean_auc_delta > 0,
        'max_single_seed_positive_contribution_le_0_5': max_contribution <= 0.5,
    }

    torch.manual_seed(REPLAY_SEED)
    base = SmallMCByteLM(); base_state = copy.deepcopy(base.state_dict())
    replay = []
    for treatment in ['MC_ON','MC_OFF']:
        replay.append(train_arm(REPLAY_SEED,treatment,base_state,train_stream,val_stream,test_stream,total_t0))
    replay_checks = []
    for rr in replay:
        orig = next(r for r in results if r['seed']==REPLAY_SEED and r['treatment']==rr['treatment'])
        equal = (
            rr['final_parameter_sha256'] == orig['final_parameter_sha256'] and
            rr['test_native'] == orig['test_native'] and
            rr['validation_curve'] == orig['validation_curve']
        )
        replay_checks.append({'treatment':rr['treatment'],'exact_replay':equal,
                              'original_final_parameter_sha256':orig['final_parameter_sha256'],
                              'replay_final_parameter_sha256':rr['final_parameter_sha256']})
    criteria['predesignated_two_arm_exact_replay'] = all(x['exact_replay'] for x in replay_checks)
    criteria['total_wallclock_within_1800s'] = (time.perf_counter()-total_t0) <= TOTAL_LIMIT_S
    criteria['all_arm_training_within_180s'] = all(r['train_seconds'] <= PER_ARM_TRAIN_LIMIT_S for r in results+replay)

    causal_pass = all(criteria.values())
    verdict = PASS_LABEL if causal_pass else 'HOLD_CAUSAL_PASS_CRITERIA_NOT_MET'
    total_seconds = time.perf_counter()-total_t0
    summary = {
        'gate': GATE,
        'verdict': verdict,
        'causal_pass': causal_pass,
        'claim_ceiling': PASS_LABEL,
        'zero_spend': True,
        'global_bind': False,
        'production_promotion': False,
        'runtime': {'torch':torch.__version__,'python':platform.python_version(),'platform':platform.platform(),'threads':THREADS,'total_seconds':total_seconds},
        'dataset': data_receipt,
        'model': {'family':'SmallMCByteLM_V1','parameter_count':231168,'vocab':VOCAB,'d_model':D,'sequence_length':SEQ,'segment_size':SEG},
        'training': {'batch_size':BATCH,'steps_per_arm':STEPS,'tokens_per_step':BATCH*SEQ,'tokens_per_arm':BATCH*SEQ*STEPS,'seeds':SEEDS,'replay_seed':REPLAY_SEED},
        'parity': parity,
        'per_seed_effects': {str(k):v for k,v in by_seed.items()},
        'aggregate': {
            'mean_test_nll_delta_off_minus_on': mean_delta,
            'mean_test_ppl_delta_off_minus_on': mean_ppl_delta,
            'mean_validation_auc_delta_off_minus_on': mean_auc_delta,
            'exhaustive_bootstrap_95_ci_test_nll': list(ci),
            'loso_mean_test_nll_deltas': loso,
            'between_seed_sd_test_nll_delta': (sum((x-mean_delta)**2 for x in deltas)/(len(deltas)-1))**0.5,
            'effect_range_test_nll': [min(deltas), max(deltas)],
            'max_single_seed_positive_contribution': max_contribution,
            'exact_two_sided_sign_test_p': exact_sign_test_two_sided(deltas),
        },
        'criteria': criteria,
        'replay_checks': replay_checks,
        'claim_fence': {
            '113M_MATCHED_TRAINING_CAUSAL_EFFECT': False,
            'OFFICIAL_AUTHOR_CHECKPOINT': False,
            'PAPER_PARITY': False,
            'UNIVERSAL_MC_GENERALIZATION': False,
            'PRODUCTION_SPEEDUP': False,
            'GLOBAL_BIND': False,
            'PRODUCTION_PROMOTION': False,
        },
    }

    canonical = json.dumps(summary, sort_keys=True, separators=(',',':')).encode()
    summary['receipt_sha256_pre_field'] = hashlib.sha256(canonical).hexdigest()
    (outdir/'receipt.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    (outdir/'summary.json').write_text(json.dumps({
        'gate':GATE,'verdict':verdict,'aggregate':summary['aggregate'],'criteria':criteria,
        'receipt_sha256_pre_field':summary['receipt_sha256_pre_field'],'runtime':summary['runtime']
    },indent=2,sort_keys=True)+'\n')

    with (outdir/'paired_effects.csv').open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['seed','delta_test_nll_off_minus_on','delta_test_ppl_off_minus_on','delta_validation_auc_off_minus_on'])
        for s in SEEDS:
            v=by_seed[s]; w.writerow([s,v['delta_test_nll_off_minus_on'],v['delta_test_ppl_off_minus_on'],v['delta_validation_auc_off_minus_on']])
    with (outdir/'training_curves.csv').open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['seed','treatment','step','validation_nll','validation_ppl'])
        for r in results:
            for c in r['validation_curve']:
                w.writerow([r['seed'],r['treatment'],c['step'],c['nll'],c['ppl']])

    try: (outdir/'tinyshakespeare_input.txt').unlink()
    except FileNotFoundError: pass
    print(json.dumps(summary,indent=2,sort_keys=True))
    if not causal_pass:
        raise SystemExit(2)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--outdir',default='outputs/mc_matched_training_v1'); args=ap.parse_args(); main(args.outdir)
