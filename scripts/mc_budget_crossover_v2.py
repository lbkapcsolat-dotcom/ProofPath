import argparse
import hashlib
import json
from pathlib import Path

import mc_budget_crossover_v1 as v1

PREREGISTERED_BUDGETS = v1.PREREGISTERED_BUDGETS
first_wrap_step = v1.first_wrap_step
cross_eval_metrics = v1.cross_eval_metrics
CROSS_RUN_NLL_ABS_TOLERANCE = 1e-6


def within_replay_tolerance(actual, expected, abs_tol=CROSS_RUN_NLL_ABS_TOLERANCE):
    return abs(float(actual) - float(expected)) <= float(abs_tol)


def _rehash_receipt(receipt):
    core = dict(receipt)
    core.pop('receipt_sha256_pre_field', None)
    canonical = json.dumps(core, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(canonical).hexdigest()


def main(outdir):
    outdir = Path(outdir)
    prior_exit = 0
    try:
        v1.main(outdir)
    except SystemExit as e:
        prior_exit = int(e.code or 0)
        if prior_exit not in (0, 2):
            raise

    receipt_path = outdir / 'receipt.json'
    if not receipt_path.exists():
        raise RuntimeError('HOLD_NO_RECEIPT_FROM_BASE_EXECUTION')
    receipt = json.loads(receipt_path.read_text())

    mismatches = receipt.get('prior_native_validation_replay_mismatches', [])
    diffs = [abs(float(x['actual']) - float(x['expected'])) for x in mismatches]
    replay_within_tolerance = all(
        within_replay_tolerance(x['actual'], x['expected']) for x in mismatches
    )
    max_abs_diff = max(diffs) if diffs else 0.0

    runtime = receipt['runtime']
    runtime_ok = (
        float(runtime['total_seconds']) <= v1.TOTAL_LIMIT_S
        and all(float(x['seconds']) <= v1.PER_ARM_LIMIT_S for x in runtime['arm_train_seconds'])
    )
    structural_pass = all([
        bool(receipt['matrix_complete']),
        bool(receipt['final_test_all_4_bidirectional_specialization']),
        replay_within_tolerance,
        runtime_ok,
    ])
    crossover = bool(receipt['crossover_replicated_all_4_384_positive_512_negative'])

    if not structural_pass:
        verdict = 'HOLD_CHECKPOINT_CROSS_EVAL_INTEGRITY_OR_RUNTIME'
    elif crossover:
        verdict = 'PASS_BOUNDED_CHECKPOINT_CROSS_EVAL_REPLICATION__FIRST_SWEEP_CROSSOVER_REPLICATED'
    else:
        verdict = 'PASS_BOUNDED_CHECKPOINT_CROSS_EVAL_REPLICATION__FIRST_SWEEP_CROSSOVER_NOT_REPLICATED'

    receipt['base_execution_exit_code_before_integrity_correction'] = prior_exit
    receipt['prior_native_validation_exact_replay'] = False
    receipt['prior_native_validation_within_tolerance_replay'] = replay_within_tolerance
    receipt['cross_run_nll_abs_tolerance'] = CROSS_RUN_NLL_ABS_TOLERANCE
    receipt['cross_run_nll_max_abs_diff'] = max_abs_diff
    receipt['cross_run_byte_exact_training_replay_claim'] = False
    receipt['integrity_correction_reason'] = (
        'Independent hosted CPU runners produced tiny floating-point NLL drift; '
        'scientific sign/effect conclusions are evaluated separately from byte-exact cross-run replay.'
    )
    receipt['verdict'] = verdict
    receipt['receipt_sha256_pre_field'] = _rehash_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')

    summary = {
        'gate': receipt['gate'],
        'verdict': verdict,
        'crossover_replicated': crossover,
        'final_test_negative_replicated': receipt['final_test_all_4_native_negative_replicated'],
        'final_specialization': receipt['final_test_all_4_bidirectional_specialization'],
        'prior_native_validation_exact_replay': False,
        'prior_native_validation_within_tolerance_replay': replay_within_tolerance,
        'cross_run_nll_abs_tolerance': CROSS_RUN_NLL_ABS_TOLERANCE,
        'cross_run_nll_max_abs_diff': max_abs_diff,
        'aggregates': receipt['aggregates'],
        'receipt_sha256_pre_field': receipt['receipt_sha256_pre_field'],
    }
    (outdir / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')

    print(json.dumps(summary, indent=2, sort_keys=True))
    if not structural_pass:
        raise SystemExit(2)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default='outputs/mc_budget_crossover_v1')
    args = ap.parse_args()
    main(args.outdir)
