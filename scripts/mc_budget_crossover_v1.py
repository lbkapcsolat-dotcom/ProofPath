import argparse
import copy
import csv
import hashlib
import json
import math
import os
import platform
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from mc_matched_training_v1 import (
    SmallMCByteLM,
    DATA_BYTES,
    DATA_SHA256,
    TRAIN_RANGE,
    VAL_RANGE,
    TEST_RANGE,
    SEEDS,
    EXPECTED_INIT,
    VOCAB,
    SEQ,
    SEG,
    BATCH,
    THREADS,
    download_dataset,
    bytes_to_long,
    window_starts,
    make_batch,
    evaluate,
    param_sha256,
    exhaustive_bootstrap_ci,
    loso_means,
    sha_bytes,
)

GATE = 'MC_MATCHED_TRAINING_BUDGET_CROSSOVER_PREREGISTRATION_AND_CHECKPOINT_CROSS_EVAL_REPLICATION_V1'
PREREGISTERED_BUDGETS = [384, 512, 768, 1024]
MAX_STEPS = 1024
PER_ARM_LIMIT_S = 180.0
TOTAL_LIMIT_S = 1800.0

# Frozen from the immediately preceding deterministic run before this gate.
PRIOR_NATIVE_VALIDATION_NLL = {
    3506515047: {
        'MC_ON': {384: 2.2027083144790827, 512: 2.087341580445739, 768: 2.028990121819507, 1024: 1.9702701996112693},
        'MC_OFF': {384: 2.2048617505479133, 512: 2.08681318239234, 768: 2.0291647231441803, 1024: 1.9709972874871613},
    },
    2029779934: {
        'MC_ON': {384: 2.202459512907883, 512: 2.086994643595027, 768: 2.0327609040271275, 1024: 1.9686770307606665},
        'MC_OFF': {384: 2.20275042851766, 512: 2.084998747946202, 768: 2.033586060315713, 1024: 1.968531348787505},
    },
    2790631980: {
        'MC_ON': {384: 2.195070371956661, 512: 2.084816610402074, 768: 2.026526799695245, 1024: 1.9728719842844995},
        'MC_OFF': {384: 2.1960924027980058, 512: 2.083514367026844, 768: 2.0261645909013417, 1024: 1.96985989603503},
    },
    3053553163: {
        'MC_ON': {384: 2.2047496466801086, 512: 2.0911637262366285, 768: 2.034565425741261, 1024: 1.9794983458244937},
        'MC_OFF': {384: 2.206333054071185, 512: 2.0886048919853124, 768: 2.033054592965663, 1024: 1.9753919667211075},
    },
}


def first_wrap_step(train_bytes: int, seq: int, batch: int) -> int:
    starts = list(range(0, train_bytes - (seq + 1) + 1, seq))
    return math.floor((len(starts) - 1) / batch) + 1


def cross_eval_metrics(m):
    a = float(m['on_train_on_eval'])
    b = float(m['on_train_off_eval'])
    c = float(m['off_train_on_eval'])
    d = float(m['off_train_off_eval'])
    return {
        'native_delta_off_minus_on': d - a,
        'on_trained_knockout_penalty': b - a,
        'off_trained_activation_penalty': c - d,
        'common_on_eval_training_effect_offtrain_minus_ontrain': c - a,
        'common_off_eval_training_effect_offtrain_minus_ontrain': d - b,
        'interaction_contrast': (c - d) + (b - a),
    }


def train_with_checkpoint_cross_eval(seed, treatment, base_state, train_stream, val_stream, test_stream, total_t0):
    mc_native = 1.0 if treatment == 'MC_ON' else 0.0
    model = SmallMCByteLM()
    model.load_state_dict(copy.deepcopy(base_state))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.01)
    starts = window_starts(len(train_stream))
    cursor = 0
    checkpoints = {}
    t0 = time.perf_counter()

    for step in range(1, MAX_STEPS + 1):
        if time.perf_counter() - t0 > PER_ARM_LIMIT_S:
            raise RuntimeError('HOLD_ZERO_SPEND_EXECUTION_SURFACE per-arm runtime')
        if time.perf_counter() - total_t0 > TOTAL_LIMIT_S:
            raise RuntimeError('HOLD_ZERO_SPEND_EXECUTION_SURFACE total runtime')
        ss = []
        for _ in range(BATCH):
            ss.append(starts[cursor])
            cursor = (cursor + 1) % len(starts)
        x, y = make_batch(train_stream, ss)
        model.train()
        opt.zero_grad(set_to_none=True)
        logits = model(x, mc_native)
        loss = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step in PREREGISTERED_BUDGETS:
            checkpoints[step] = {
                'parameter_sha256': param_sha256(model),
                'validation': {
                    'MC_ON': evaluate(model, val_stream, 1.0),
                    'MC_OFF': evaluate(model, val_stream, 0.0),
                },
                'test': {
                    'MC_ON': evaluate(model, test_stream, 1.0),
                    'MC_OFF': evaluate(model, test_stream, 0.0),
                },
            }

    return {
        'seed': seed,
        'treatment': treatment,
        'initial_parameter_sha256': param_sha256_from_state(base_state),
        'train_seconds': time.perf_counter() - t0,
        'checkpoints': checkpoints,
    }


def param_sha256_from_state(state):
    h = hashlib.sha256()
    for name, tensor in state.items():
        h.update(name.encode())
        h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def aggregate_budget(rows, budget, split):
    sub = [r for r in rows if r['budget'] == budget and r['split'] == split]
    native = [r['native_delta_off_minus_on'] for r in sub]
    interaction = [r['interaction_contrast'] for r in sub]
    knock = [r['on_trained_knockout_penalty'] for r in sub]
    activation = [r['off_trained_activation_penalty'] for r in sub]
    ci = exhaustive_bootstrap_ci(native)
    return {
        'budget': budget,
        'split': split,
        'n_seeds': len(sub),
        'native_delta_mean': sum(native) / len(native),
        'native_delta_range': [min(native), max(native)],
        'native_delta_bootstrap_95_ci': list(ci),
        'native_delta_loso_means': loso_means(native),
        'native_positive_count': sum(x > 0 for x in native),
        'native_negative_count': sum(x < 0 for x in native),
        'interaction_mean': sum(interaction) / len(interaction),
        'on_trained_knockout_penalty_mean': sum(knock) / len(knock),
        'off_trained_activation_penalty_mean': sum(activation) / len(activation),
    }


def main(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(THREADS)
    torch.use_deterministic_algorithms(True)
    total_t0 = time.perf_counter()

    raw = download_dataset(outdir / 'tinyshakespeare_input.txt')
    train_b = raw[slice(*TRAIN_RANGE)]
    val_b = raw[slice(*VAL_RANGE)]
    test_b = raw[slice(*TEST_RANGE)]
    train_stream = bytes_to_long(train_b)
    val_stream = bytes_to_long(val_b)
    test_stream = bytes_to_long(test_b)

    wrap = first_wrap_step(len(train_b), SEQ, BATCH)
    if PREREGISTERED_BUDGETS != [384, 512, 768, 1024] or not (384 < wrap < 512):
        raise RuntimeError('HOLD_PREREGISTRATION_FENCE')

    arms = []
    parity = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        base = SmallMCByteLM()
        init_hash = param_sha256(base)
        if init_hash != EXPECTED_INIT[seed]:
            raise RuntimeError(f'HOLD_INIT_PARITY seed={seed}')
        base_state = copy.deepcopy(base.state_dict())
        parity.append({'seed': seed, 'initial_parameter_sha256': init_hash, 'expected': EXPECTED_INIT[seed], 'equal': True})
        arms.append(train_with_checkpoint_cross_eval(seed, 'MC_ON', base_state, train_stream, val_stream, test_stream, total_t0))
        arms.append(train_with_checkpoint_cross_eval(seed, 'MC_OFF', base_state, train_stream, val_stream, test_stream, total_t0))

    replay_native_exact = True
    replay_mismatches = []
    for arm in arms:
        seed = arm['seed']
        treatment = arm['treatment']
        for budget in PREREGISTERED_BUDGETS:
            got = arm['checkpoints'][budget]['validation'][treatment]['nll']
            exp = PRIOR_NATIVE_VALIDATION_NLL[seed][treatment][budget]
            if got != exp:
                replay_native_exact = False
                replay_mismatches.append({'seed': seed, 'treatment': treatment, 'budget': budget, 'expected': exp, 'actual': got})

    rows = []
    for seed in SEEDS:
        on = next(a for a in arms if a['seed'] == seed and a['treatment'] == 'MC_ON')
        off = next(a for a in arms if a['seed'] == seed and a['treatment'] == 'MC_OFF')
        for budget in PREREGISTERED_BUDGETS:
            for split in ['validation', 'test']:
                matrix = {
                    'on_train_on_eval': on['checkpoints'][budget][split]['MC_ON']['nll'],
                    'on_train_off_eval': on['checkpoints'][budget][split]['MC_OFF']['nll'],
                    'off_train_on_eval': off['checkpoints'][budget][split]['MC_ON']['nll'],
                    'off_train_off_eval': off['checkpoints'][budget][split]['MC_OFF']['nll'],
                }
                metrics = cross_eval_metrics(matrix)
                rows.append({'seed': seed, 'budget': budget, 'split': split, **matrix, **metrics})

    aggregates = [aggregate_budget(rows, b, split) for b in PREREGISTERED_BUDGETS for split in ['validation', 'test']]
    val384 = [r for r in rows if r['budget'] == 384 and r['split'] == 'validation']
    val512 = [r for r in rows if r['budget'] == 512 and r['split'] == 'validation']
    test1024 = [r for r in rows if r['budget'] == 1024 and r['split'] == 'test']

    crossover_replicated = (
        all(r['native_delta_off_minus_on'] > 0 for r in val384)
        and all(r['native_delta_off_minus_on'] < 0 for r in val512)
    )
    final_test_negative_replicated = all(r['native_delta_off_minus_on'] < 0 for r in test1024)
    final_specialization = all(
        r['on_trained_knockout_penalty'] > 0 and r['off_trained_activation_penalty'] > 0
        for r in test1024
    )
    matrix_complete = len(rows) == len(SEEDS) * len(PREREGISTERED_BUDGETS) * 2
    runtime_ok = all(a['train_seconds'] <= PER_ARM_LIMIT_S for a in arms) and (time.perf_counter() - total_t0 <= TOTAL_LIMIT_S)
    structural_pass = all([matrix_complete, replay_native_exact, final_specialization, runtime_ok])

    if not structural_pass:
        verdict = 'HOLD_CHECKPOINT_CROSS_EVAL_INTEGRITY_OR_RUNTIME'
    elif crossover_replicated:
        verdict = 'PASS_BOUNDED_CHECKPOINT_CROSS_EVAL_REPLICATION__FIRST_SWEEP_CROSSOVER_REPLICATED'
    else:
        verdict = 'PASS_BOUNDED_CHECKPOINT_CROSS_EVAL_REPLICATION__FIRST_SWEEP_CROSSOVER_NOT_REPLICATED'

    summary = {
        'gate': GATE,
        'verdict': verdict,
        'zero_spend': True,
        'global_bind': False,
        'production_promotion': False,
        'no_outcome_driven_seed_selection': True,
        'preregistration': {
            'budgets': PREREGISTERED_BUDGETS,
            'seeds': SEEDS,
            'first_wrap_step': wrap,
            'budget_384_pre_wrap': 384 < wrap,
            'budget_512_post_wrap': 512 > wrap,
            'matrix_cells_per_seed_budget_split': 4,
        },
        'dataset': {
            'raw_bytes': len(raw), 'raw_sha256': sha_bytes(raw),
            'train_bytes': len(train_b), 'train_sha256': sha_bytes(train_b),
            'validation_bytes': len(val_b), 'validation_sha256': sha_bytes(val_b),
            'test_bytes': len(test_b), 'test_sha256': sha_bytes(test_b),
        },
        'model': {'family': 'SmallMCByteLM_V1', 'parameter_count': 231168, 'seq': SEQ, 'segment': SEG},
        'parity': parity,
        'prior_native_validation_exact_replay': replay_native_exact,
        'prior_native_validation_replay_mismatches': replay_mismatches,
        'crossover_replicated_all_4_384_positive_512_negative': crossover_replicated,
        'final_test_all_4_native_negative_replicated': final_test_negative_replicated,
        'final_test_all_4_bidirectional_specialization': final_specialization,
        'matrix_complete': matrix_complete,
        'aggregates': aggregates,
        'runtime': {
            'torch': torch.__version__, 'python': platform.python_version(), 'platform': platform.platform(),
            'threads': THREADS, 'total_seconds': time.perf_counter() - total_t0,
            'arm_train_seconds': [{'seed': a['seed'], 'treatment': a['treatment'], 'seconds': a['train_seconds']} for a in arms],
        },
        'claim_fence': {
            'OVERFITTING_CAUSE_IDENTIFIED': False,
            'GRADIENT_PATH_CAUSE_IDENTIFIED': False,
            'SCALE_GENERALIZATION': False,
            '113M_MATCHED_TRAINING_CAUSAL_EFFECT': False,
            'PAPER_PARITY': False,
            'UNIVERSAL_MC_GENERALIZATION': False,
            'PRODUCTION_SPEEDUP': False,
            'GLOBAL_BIND': False,
            'PRODUCTION_PROMOTION': False,
        },
    }
    canonical = json.dumps(summary, sort_keys=True, separators=(',', ':')).encode()
    summary['receipt_sha256_pre_field'] = hashlib.sha256(canonical).hexdigest()

    with (outdir / 'checkpoint_cross_eval.csv').open('w', newline='') as f:
        fields = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    with (outdir / 'checkpoint_parameter_hashes.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['seed','treatment','budget','parameter_sha256'])
        for a in arms:
            for b in PREREGISTERED_BUDGETS:
                w.writerow([a['seed'], a['treatment'], b, a['checkpoints'][b]['parameter_sha256']])
    (outdir / 'receipt.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    (outdir / 'summary.json').write_text(json.dumps({
        'gate': GATE, 'verdict': verdict,
        'crossover_replicated': crossover_replicated,
        'final_test_negative_replicated': final_test_negative_replicated,
        'final_specialization': final_specialization,
        'prior_native_validation_exact_replay': replay_native_exact,
        'aggregates': aggregates,
        'receipt_sha256_pre_field': summary['receipt_sha256_pre_field'],
    }, indent=2, sort_keys=True) + '\n')

    try:
        (outdir / 'tinyshakespeare_input.txt').unlink()
    except FileNotFoundError:
        pass

    print(json.dumps(summary, indent=2, sort_keys=True))
    if not structural_pass:
        raise SystemExit(2)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default='outputs/mc_budget_crossover_v1')
    args = ap.parse_args()
    main(args.outdir)
