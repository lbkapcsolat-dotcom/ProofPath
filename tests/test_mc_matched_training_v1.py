import torch
from mc_matched_training_v1 import SmallMCByteLM, param_signature, param_sha256, exhaustive_bootstrap_ci, loso_means


def test_parameter_inventory_and_initial_bytes_match_between_treatments():
    seed = 3506515047
    torch.manual_seed(seed)
    a = SmallMCByteLM()
    torch.manual_seed(seed)
    b = SmallMCByteLM()
    assert param_signature(a) == param_signature(b)
    assert param_sha256(a) == param_sha256(b)
    assert sum(p.numel() for p in a.parameters()) == 231168


def test_mc_scale_zero_and_one_share_model_state_but_change_forward_path():
    seed = 123
    torch.manual_seed(seed)
    m = SmallMCByteLM().eval()
    x = torch.arange(128, dtype=torch.long).unsqueeze(0).repeat(2,1) % 256
    with torch.no_grad():
        y0 = m(x, mc_scale=0.0)
        y1 = m(x, mc_scale=1.0)
    assert y0.shape == y1.shape == (2,128,256)
    assert not torch.equal(y0, y1)


def test_exhaustive_bootstrap_ci_and_loso_are_deterministic():
    ds = [0.1, 0.2, 0.3, 0.4]
    lo, hi = exhaustive_bootstrap_ci(ds)
    assert 0.1 <= lo <= 0.25 <= hi <= 0.4
    got = loso_means(ds)
    exp = [0.3, 0.26666666666666666, 0.2333333333333333, 0.2]
    assert all(abs(a-b) < 1e-12 for a,b in zip(got, exp))
