from __future__ import annotations

import hashlib
import io
import json
import math
import random
import re
import statistics
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import torch
import torch.nn.functional as F
from huggingface_hub import hf_hub_download, model_info
from safetensors.torch import load_file

GATE = "MC_HELDOUT_CORPUS_HIERARCHICAL_GENERALIZATION_AND_EFFECT_ROBUSTNESS_V1"
OUT = Path("outputs/mc_heldout_hierarchical")
OUT.mkdir(parents=True, exist_ok=True)

REPO_ID = "Quazim0t0/Byrne-100M-Ultra-MC"
STAGE = "base_62k"
SEED = 20260905
WINDOW_LEN = 300
POSITIONS = [0.12, 0.38, 0.62, 0.88]
PRIOR_CORPORA = {"emma", "alice", "moby_dick", "hamlet"}

MODEL_FILES = [
    "config.py",
    "model_v2.py",
    "spike_tokenizer.py",
    "special_tokens.py",
    "fractal.py",
    f"safetensors/{STAGE}/config.json",
    f"safetensors/{STAGE}/model.safetensors",
    f"safetensors/{STAGE}/tokenizer.json",
]

CORPUS_SPECS = {
    "webtext": {"package": "webtext", "kind": "txt"},
    "inaugural": {"package": "inaugural", "kind": "txt"},
    "state_union": {"package": "state_union", "kind": "txt"},
    "movie_reviews": {"package": "movie_reviews", "kind": "txt"},
    "genesis_kjv": {"package": "genesis", "kind": "genesis_english"},
    "nps_chat": {"package": "nps_chat", "kind": "markup"},
    "reuters": {"package": "reuters", "kind": "markup_all"},
    "subjectivity": {"package": "subjectivity", "kind": "all"},
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def quantile(xs, q):
    ys = sorted(xs)
    x = (len(ys) - 1) * q
    lo = int(math.floor(x))
    hi = int(math.ceil(x))
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - x) + ys[hi] * (x - lo)


def sign_test_two_sided(k, n):
    kk = max(k, n - k)
    tail = sum(math.comb(n, i) for i in range(kk, n + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def bootstrap_mean(values, seed, reps=20000):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return {
        "seed": seed,
        "reps": reps,
        "mean_observed": statistics.mean(values),
        "ci95_low": quantile(means, 0.025),
        "ci95_high": quantile(means, 0.975),
    }


def hierarchical_bootstrap(effect_map, seed, reps=20000):
    """Resample corpora, then windows within each sampled corpus."""
    rng = random.Random(seed)
    corpora = sorted(effect_map)
    c = len(corpora)
    means = []
    for _ in range(reps):
        sampled = [corpora[rng.randrange(c)] for _ in range(c)]
        vals = []
        for cname in sampled:
            v = effect_map[cname]
            vals.extend(v[rng.randrange(len(v))] for _ in range(len(v)))
        means.append(sum(vals) / len(vals))
    means.sort()
    observed_corpus_mean = statistics.mean(statistics.mean(effect_map[c]) for c in corpora)
    return {
        "seed": seed,
        "reps": reps,
        "corpus_count": c,
        "mean_of_corpus_means": observed_corpus_mean,
        "ci95_low": quantile(means, 0.025),
        "ci95_high": quantile(means, 0.975),
    }


def download_with_retry(repo_id, filename, revision, attempts=5):
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return Path(hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
                resume_download=True,
            ))
        except Exception as e:
            last = e
            print(f"HF_DOWNLOAD_RETRY file={filename} attempt={attempt} err={type(e).__name__}")
            time.sleep(min(15, attempt * 3))
    raise RuntimeError(f"HF download failed after retries: {filename}: {last}")


def corpus_member_selected(name: str, kind: str) -> bool:
    lname = name.lower()
    if name.endswith("/"):
        return False
    if kind == "txt":
        return lname.endswith(".txt")
    if kind == "genesis_english":
        return ("english-kjv" in lname) and lname.endswith(".txt")
    if kind == "markup":
        return lname.endswith(".xml") or lname.endswith(".txt")
    if kind == "markup_all":
        return not lname.endswith(("readme", ".readme"))
    if kind == "all":
        return True
    return False


def fetch_corpus(cname: str, spec: dict):
    pkg = spec["package"]
    kind = spec["kind"]
    url = f"https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/{pkg}.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "mc-heldout-audit/1.0"})
    raw_zip = urllib.request.urlopen(req, timeout=120).read()
    zf = zipfile.ZipFile(io.BytesIO(raw_zip))
    members = [n for n in zf.namelist() if corpus_member_selected(n, kind)]
    if not members:
        raise RuntimeError(f"No selected members for corpus {cname}")
    chunks = []
    member_meta = []
    for name in sorted(members):
        b = zf.read(name)
        text = b.decode("utf-8", errors="ignore")
        if kind in {"markup", "markup_all"}:
            text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        if text.strip():
            chunks.append(text)
            member_meta.append({"member": name, "raw_sha256": sha256_bytes(b), "raw_bytes": len(b)})
    joined = "\n".join(chunks)
    return {
        "url": url,
        "archive_sha256": sha256_bytes(raw_zip),
        "archive_bytes": len(raw_zip),
        "members": member_meta,
        "text": joined,
    }


def evaluate(model, windows):
    rows = []
    hashes = []
    with torch.no_grad():
        for wi, item in enumerate(windows):
            ids = item["tensor"]
            t0 = time.perf_counter()
            out = model(input_ids=ids, use_cache=False)
            dt = (time.perf_counter() - t0) * 1000.0
            logits = out.logits
            loss = F.cross_entropy(
                logits[:, :-1, :].reshape(-1, logits.shape[-1]),
                ids[:, 1:].reshape(-1),
            )
            h = sha256_bytes(logits.detach().cpu().numpy().tobytes())
            hashes.append(h)
            rows.append({
                "window_id": wi,
                "corpus": item["corpus"],
                "fraction": item["fraction"],
                "token_start": item["token_start"],
                "tokens": int(ids.numel()),
                "input_sha256": item["tensor_sha256"],
                "loss": float(loss.item()),
                "ppl": float(math.exp(min(20.0, loss.item()))),
                "latency_ms": dt,
                "logits_sha256": h,
            })
    return rows, hashes


def main():
    torch.manual_seed(SEED)
    torch.set_num_threads(1)

    info = model_info(REPO_ID)
    revision = info.sha
    downloaded = {f: download_with_retry(REPO_ID, f, revision) for f in MODEL_FILES}
    root = downloaded["config.py"].parent
    stage = root / "safetensors" / STAGE
    if not stage.exists():
        stage = downloaded[f"safetensors/{STAGE}/config.json"].parent

    sys.path.insert(0, str(root))
    from config import SpikeWhaleConfig
    from model_v2 import SpikeWhaleLM
    from spike_tokenizer import SpikeTokenizer

    cfg = SpikeWhaleConfig(**json.loads((stage / "config.json").read_text(encoding="utf-8")))
    model = SpikeWhaleLM(cfg)
    state = load_file(str(stage / "model.safetensors"), device="cpu")
    missing, unexpected = model.load_state_dict(state, strict=False)
    model.tie_weights()
    model.eval()
    tok = SpikeTokenizer(vocab_file=str(stage / "tokenizer.json"))

    gate_names = [n for n, _ in model.named_parameters() if "mc_gate" in n]
    if not gate_names:
        raise RuntimeError("No mc_gate parameters found; fail closed")
    gate_backup = {n: p.detach().clone() for n, p in model.named_parameters() if n in gate_names}
    gate_values = torch.cat([p.detach().flatten().float() for n, p in model.named_parameters() if n in gate_names])
    gate_mean_abs_tanh = float(torch.tanh(gate_values).abs().mean().item())

    corpus_meta = {}
    tokenized = {}
    for cname, spec in CORPUS_SPECS.items():
        c = fetch_corpus(cname, spec)
        ids = tok.encode(c.pop("text"), add_special_tokens=False)
        if len(ids) < 6000:
            raise RuntimeError(f"Heldout corpus too short after tokenization: {cname} {len(ids)}")
        c["token_count"] = len(ids)
        c["package"] = spec["package"]
        c["kind"] = spec["kind"]
        corpus_meta[cname] = c
        tokenized[cname] = ids

    heldout_vs_prior = set(tokenized).isdisjoint(PRIOR_CORPORA) and all(v["package"] != "gutenberg" for v in corpus_meta.values())
    if not heldout_vs_prior:
        raise RuntimeError("Heldout corpus fence failed")

    bos = tok.bos_token_id
    if bos is None:
        bos = int(getattr(cfg, "bos_token_id", 0))

    windows = []
    manifest = []
    for cname in sorted(tokenized):
        ids = tokenized[cname]
        max_start = len(ids) - WINDOW_LEN
        for pos in POSITIONS:
            s = max(0, min(max_start, int(round(pos * max_start))))
            body = ids[s:s + WINDOW_LEN]
            if len(body) != WINDOW_LEN:
                raise RuntimeError("Frozen heldout window length mismatch")
            tensor = torch.tensor([[bos] + body], dtype=torch.long)
            tsha = sha256_bytes(tensor.numpy().tobytes())
            item = {
                "corpus": cname,
                "fraction": pos,
                "token_start": s,
                "tensor": tensor,
                "tensor_sha256": tsha,
            }
            windows.append(item)
            manifest.append({k: v for k, v in item.items() if k != "tensor"})

    on_rows, on_hashes = evaluate(model, windows)

    with torch.no_grad():
        for n, p in model.named_parameters():
            if n in gate_names:
                p.zero_()
    off_rows, off_hashes = evaluate(model, windows)

    with torch.no_grad():
        for n, p in model.named_parameters():
            if n in gate_backup:
                p.copy_(gate_backup[n])
    replay_rows, replay_hashes = evaluate(model, windows)
    exact_replay = on_hashes == replay_hashes

    effects_by_corpus = {c: [] for c in sorted(tokenized)}
    window_effects = []
    latency_deltas = []
    for a, b in zip(on_rows, off_rows):
        if a["window_id"] != b["window_id"] or a["input_sha256"] != b["input_sha256"]:
            raise RuntimeError("Paired window mismatch")
        dloss = b["loss"] - a["loss"]
        dppl = b["ppl"] - a["ppl"]
        dlat = b["latency_ms"] - a["latency_ms"]
        effects_by_corpus[a["corpus"]].append(dloss)
        window_effects.append(dloss)
        latency_deltas.append(dlat)
        a["off_loss"] = b["loss"]
        a["off_ppl"] = b["ppl"]
        a["off_latency_ms"] = b["latency_ms"]
        a["delta_loss_off_minus_on"] = dloss
        a["delta_ppl_off_minus_on"] = dppl
        a["delta_latency_ms_off_minus_on"] = dlat

    corpus_effects = {}
    corpus_means = []
    for cname, vals in effects_by_corpus.items():
        m = statistics.mean(vals)
        corpus_means.append(m)
        corpus_effects[cname] = {
            "windows": len(vals),
            "mean_delta_loss_off_minus_on": m,
            "median_delta_loss_off_minus_on": statistics.median(vals),
            "positive_windows": sum(x > 0 for x in vals),
            "min_delta_loss": min(vals),
            "max_delta_loss": max(vals),
        }

    corpus_positive = sum(m > 0 for m in corpus_means)
    corpus_sign_p = sign_test_two_sided(corpus_positive, len(corpus_means))
    heterogeneity = {
        "corpus_mean": statistics.mean(corpus_means),
        "corpus_median": statistics.median(corpus_means),
        "between_corpus_sd": statistics.stdev(corpus_means) if len(corpus_means) > 1 else 0.0,
        "range_low": min(corpus_means),
        "range_high": max(corpus_means),
        "range_width": max(corpus_means) - min(corpus_means),
        "positive_corpora": corpus_positive,
        "total_corpora": len(corpus_means),
        "corpus_sign_test_two_sided_p": corpus_sign_p,
    }

    hierarchical_a = hierarchical_bootstrap(effects_by_corpus, 20260905, reps=20000)
    hierarchical_b = hierarchical_bootstrap(effects_by_corpus, 260224281, reps=20000)

    loco = {}
    for idx, omitted in enumerate(sorted(effects_by_corpus)):
        rem = {c: v for c, v in effects_by_corpus.items() if c != omitted}
        hb = hierarchical_bootstrap(rem, 910000 + idx, reps=8000)
        rem_means = [statistics.mean(v) for v in rem.values()]
        loco[omitted] = {
            "remaining_corpora": sorted(rem),
            "mean_of_remaining_corpus_means": statistics.mean(rem_means),
            "hierarchical_ci95_low": hb["ci95_low"],
            "hierarchical_ci95_high": hb["ci95_high"],
            "ci_above_zero": hb["ci95_low"] > 0,
        }

    window_boot = bootstrap_mean(window_effects, 777001, reps=20000)
    window_positive = sum(x > 0 for x in window_effects)
    window_sign_p = sign_test_two_sided(window_positive, len(window_effects))

    on_lat = [r["latency_ms"] for r in on_rows]
    off_lat = [r["latency_ms"] for r in off_rows]
    latency = {
        "mc_on": {
            "median_ms": statistics.median(on_lat),
            "p25_ms": quantile(on_lat, 0.25),
            "p75_ms": quantile(on_lat, 0.75),
            "p95_ms": quantile(on_lat, 0.95),
        },
        "mc_off": {
            "median_ms": statistics.median(off_lat),
            "p25_ms": quantile(off_lat, 0.25),
            "p75_ms": quantile(off_lat, 0.75),
            "p95_ms": quantile(off_lat, 0.95),
        },
        "paired_off_minus_on": {
            "mean_ms": statistics.mean(latency_deltas),
            "median_ms": statistics.median(latency_deltas),
        },
    }

    all_corpus_positive = all(m > 0 for m in corpus_means)
    hierarchical_stable = hierarchical_a["ci95_low"] > 0 and hierarchical_b["ci95_low"] > 0
    loco_stable = all(v["ci_above_zero"] for v in loco.values())
    real_task = len(on_rows) == len(CORPUS_SPECS) * len(POSITIONS) and all(r["tokens"] > int(getattr(cfg, "mc_segment_len", 0)) for r in on_rows)
    pass_gate = heldout_vs_prior and real_task and exact_replay and all_corpus_positive and hierarchical_stable and loco_stable
    verdict = "PASS_BOUNDED_HELDOUT_CORPUS_HIERARCHICAL_GENERALIZATION" if pass_gate else "HOLD_HELDOUT_GENERALIZATION_INCONSISTENT"

    weight_sha = sha256_bytes((stage / "model.safetensors").read_bytes())
    config_sha = sha256_bytes((stage / "config.json").read_bytes())
    tokenizer_sha = sha256_bytes((stage / "tokenizer.json").read_bytes())

    receipt = {
        "gate": GATE,
        "verdict": verdict,
        "zero_spend": True,
        "checkpoint": {
            "repo_id": REPO_ID,
            "hf_revision": revision,
            "stage": STAGE,
            "trained": True,
            "community_model": True,
            "official_paper_author_checkpoint": False,
            "weight_sha256": weight_sha,
            "config_sha256": config_sha,
            "tokenizer_sha256": tokenizer_sha,
            "tensors_loaded": len(state),
            "missing_keys": list(missing),
            "unexpected_keys": list(unexpected),
        },
        "model": {
            "class": "SpikeWhaleLM",
            "parameter_count": sum(p.numel() for p in model.parameters()),
            "mc_gate_parameter_count": len(gate_names),
            "mc_gate_mean_abs_tanh": gate_mean_abs_tanh,
            "mc_segment_len": int(getattr(cfg, "mc_segment_len", 0)),
        },
        "heldout_corpora": {
            "heldout_vs_prior_gutenberg_eval": heldout_vs_prior,
            "prior_corpora": sorted(PRIOR_CORPORA),
            "corpus_count": len(corpus_meta),
            "window_positions": POSITIONS,
            "window_body_tokens": WINDOW_LEN,
            "total_windows": len(windows),
            "corpora": corpus_meta,
            "window_manifest": manifest,
        },
        "paired_windows": on_rows,
        "effect": {
            "window_mean_delta_loss_off_minus_on": statistics.mean(window_effects),
            "window_median_delta_loss_off_minus_on": statistics.median(window_effects),
            "positive_windows": window_positive,
            "total_windows": len(window_effects),
            "window_sign_test_two_sided_p": window_sign_p,
            "window_bootstrap": window_boot,
            "per_corpus": corpus_effects,
            "heterogeneity": heterogeneity,
        },
        "hierarchical_bootstrap": {
            "seed_a": hierarchical_a,
            "seed_b": hierarchical_b,
            "both_ci95_above_zero": hierarchical_stable,
        },
        "leave_one_corpus_out": loco,
        "loco_all_ci95_above_zero": loco_stable,
        "latency": latency,
        "replay": {
            "exact_logit_hash_equality": exact_replay,
            "first_run_hashes": on_hashes,
            "replay_hashes": replay_hashes,
        },
        "claim_ceiling": {
            "trained_checkpoint_recovered": True,
            "real_heldout_multicorpus_lm_task": real_task,
            "corpus_is_resampling_unit": True,
            "hierarchical_bootstrap": True,
            "leave_one_corpus_out": True,
            "effect_heterogeneity_reported": True,
            "official_author_checkpoint": False,
            "paper_parity": False,
            "matched_training_ablation": False,
            "universal_domain_generalization": False,
            "production_latency_claim": False,
        },
    }

    pre = json.dumps(receipt, sort_keys=True, indent=2).encode()
    receipt["receipt_sha256_pre_field"] = sha256_bytes(pre)
    (OUT / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2), encoding="utf-8")
    (OUT / "paired_windows.json").write_text(json.dumps(on_rows, sort_keys=True, indent=2), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({
        "verdict": verdict,
        "corpus_count": len(corpus_meta),
        "total_windows": len(window_effects),
        "positive_corpora": corpus_positive,
        "total_corpora": len(corpus_means),
        "corpus_sign_test_p": corpus_sign_p,
        "window_mean_delta_loss": statistics.mean(window_effects),
        "window_positive": window_positive,
        "window_total": len(window_effects),
        "hierarchical_seed_a": hierarchical_a,
        "hierarchical_seed_b": hierarchical_b,
        "loco": loco,
        "heterogeneity": heterogeneity,
        "latency": latency,
        "exact_replay": exact_replay,
    }, sort_keys=True, indent=2), encoding="utf-8")

    print("VERDICT", verdict)
    print("HF_REVISION", revision)
    print("PARAMETER_COUNT", receipt["model"]["parameter_count"])
    print("HELDOUT_CORPORA", sorted(corpus_meta))
    print("TOTAL_WINDOWS", len(window_effects))
    print("POSITIVE_CORPORA", corpus_positive, "OF", len(corpus_means))
    print("CORPUS_SIGN_TEST_P", corpus_sign_p)
    print("WINDOW_MEAN_DELTA_LOSS", statistics.mean(window_effects))
    print("WINDOW_POSITIVE", window_positive, "OF", len(window_effects))
    print("HIER_A", json.dumps(hierarchical_a, sort_keys=True))
    print("HIER_B", json.dumps(hierarchical_b, sort_keys=True))
    print("HETEROGENEITY", json.dumps(heterogeneity, sort_keys=True))
    print("LOCO", json.dumps(loco, sort_keys=True))
    print("LATENCY", json.dumps(latency, sort_keys=True))
    print("EXACT_REPLAY", exact_replay)
    print("WEIGHT_SHA256", weight_sha)
    print("RECEIPT_SHA256_PRE_FIELD", receipt["receipt_sha256_pre_field"])


if __name__ == "__main__":
    main()
