from __future__ import annotations

import json
import tempfile
from pathlib import Path

import live_evidence as live


def expect_failure(fn, needle: str) -> None:
    try:
        fn()
    except ValueError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {needle!r}")


def sage_raw() -> str:
    return "\n".join(
        [
            "SageMath version: 10.9",
            "PROOFPATH_EVIDENCE ALG-LIVE exact_computation factor_product=4294967295",
            "PROOFPATH_EVIDENCE THM-LIVE independent_countercheck rational_scan=true",
            "PROOFPATH_EVIDENCE RIG-LIVE independent_crosscheck sqrt2_residual_lt_1e-70=true",
            "PROOFPATH_EVIDENCE HPC-LIVE deterministic_independent_replay serial_sum=500000500000",
            "PROOFPATH_ADVERSARIAL ALG-LIVE boundary factor_product_exact=true",
            "PROOFPATH_ADVERSARIAL THM-LIVE boundary zero_and_sign_cases=true",
            "PROOFPATH_ADVERSARIAL THM-LIVE counterexample_search rational_scan_no_counterexample=true",
            "PROOFPATH_ADVERSARIAL HPC-LIVE boundary serial_formula_small_n=true",
            "",
        ]
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        canary = root / "research_math/sage/canary.py"
        canary.parent.mkdir(parents=True)
        canary.write_text("# exact source\n", encoding="utf-8")
        evidence_dir = root / "out/sage"
        evidence_dir.mkdir(parents=True)
        raw = evidence_dir / "raw.log"
        raw.write_text(sage_raw(), encoding="utf-8")
        receipt = evidence_dir / "receipt.json"

        built = live.emit_receipt(
            "sage",
            source_sha="a" * 40,
            run_id="123",
            job="sagemath-independent-cas",
            raw_log=raw,
            repo_root=root,
            output_path=receipt,
        )
        assert built["engine"] == "sage"
        assert built["engine_family"] == "cas_sage"
        assert len(built["evidence"]) == 4
        assert len(built["adversarial"]) == 4
        assert live.verify_receipt(receipt, root, "a" * 40)["status"] == "PASS"

        expect_failure(lambda: live.verify_receipt(receipt, root, "b" * 40), "source SHA mismatch")

        raw.write_text(sage_raw() + "tampered\n", encoding="utf-8")
        expect_failure(lambda: live.verify_receipt(receipt, root, "a" * 40), "raw output hash mismatch")
        raw.write_text(sage_raw(), encoding="utf-8")

        canary.write_text("# changed source\n", encoding="utf-8")
        expect_failure(lambda: live.verify_receipt(receipt, root, "a" * 40), "input hash mismatch")
        canary.write_text("# exact source\n", encoding="utf-8")

        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["receipt_sha256"] = "0" * 64
        receipt.write_text(json.dumps(payload), encoding="utf-8")
        expect_failure(lambda: live.verify_receipt(receipt, root, "a" * 40), "receipt hash mismatch")

    print("P11 LIVE ENGINE RECEIPT ROUNDTRIP = PASS")
    print("P11 SOURCE SHA GUARD = PASS")
    print("P11 RAW OUTPUT TAMPER GUARD = PASS")
    print("P11 INPUT HASH GUARD = PASS")
    print("P11 RECEIPT HASH GUARD = PASS")


if __name__ == "__main__":
    run()
