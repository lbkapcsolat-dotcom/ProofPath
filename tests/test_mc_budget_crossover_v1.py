import math

from mc_budget_crossover_v1 import (
    PREREGISTERED_BUDGETS,
    first_wrap_step,
    cross_eval_metrics,
)


def test_preregistered_budget_ladder_brackets_first_sweep_and_is_frozen():
    assert PREREGISTERED_BUDGETS == [384, 512, 768, 1024]
    assert first_wrap_step(train_bytes=1003854, seq=128, batch=16) == 491
    assert 384 < 491 < 512


def test_cross_eval_metrics_recover_native_deltas_and_interaction():
    m = {
        'on_train_on_eval': 1.00,
        'on_train_off_eval': 1.02,
        'off_train_on_eval': 1.05,
        'off_train_off_eval': 0.99,
    }
    got = cross_eval_metrics(m)
    assert math.isclose(got['native_delta_off_minus_on'], -0.01, abs_tol=1e-12)
    assert math.isclose(got['on_trained_knockout_penalty'], 0.02, abs_tol=1e-12)
    assert math.isclose(got['off_trained_activation_penalty'], 0.06, abs_tol=1e-12)
    assert math.isclose(got['interaction_contrast'], 0.08, abs_tol=1e-12)
