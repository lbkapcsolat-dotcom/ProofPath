from __future__ import annotations

import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

from hgraph_adapter.receipt import (
    build_shadow_receipt,
    verify_shadow_receipt,
    write_shadow_receipt,
)


REQUEST = {
    "source_namespace": "X_AIPRBG_6GATE_DIAGNOSTIC_V1",
    "target_namespace": "ESS_EQ64_6D_KERNEL",
    "permutation": [0, 1, 2, 3, 4, 5],
    "policy": "REFERENCE_ONLY",
}
VERDICT = {
    "structural_status": "PASS",
    "semantic_status": "HOLD",
    "claim_ceiling": "STRUCTURAL_ONLY",
    "reason_codes": ["NO_AXIS_LEVEL_EVIDENCE"],
    "runtime_bind": False,
}


def copy_dependency_tree(source_root: pathlib.Path, destination_root: pathlib.Path) -> None:
    files = (
        "hgraph_adapter/xb18.py",
        "hgraph_adapter/receipt.py",
        "hgraph_adapter/run_shadow_receipt.py",
        "hgraph_adapter/verify_shadow_receipt.py",
        "hgraph_adapter/requirements.txt",
        "hgraph_adapter/tests/test_xb18.py",
        "reference/namespace_safe_engine.py",
    )
    for relative in files:
        src = source_root / relative
        dst = destination_root / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


class XB18ShadowReceiptTests(unittest.TestCase):
    def test_receipt_roundtrip_and_fresh_dependency_rehash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td) / "formal"
            copy_dependency_tree(ROOT, root)
            receipt_path = pathlib.Path(td) / "receipt.json"
            receipt = build_shadow_receipt(root, REQUEST, VERDICT)
            write_shadow_receipt(receipt_path, receipt)
            verified = verify_shadow_receipt(root, REQUEST, VERDICT, receipt_path)
        self.assertEqual(verified, receipt)
        self.assertFalse(receipt["runtime_bind"])
        self.assertEqual(receipt["schema"], "HGRAPH_XB18_SHADOW_RECEIPT_V1")

    def test_fresh_dependency_rehash_rejects_adapter_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td) / "formal"
            copy_dependency_tree(ROOT, root)
            receipt_path = pathlib.Path(td) / "receipt.json"
            receipt = build_shadow_receipt(root, REQUEST, VERDICT)
            write_shadow_receipt(receipt_path, receipt)
            adapter = root / "hgraph_adapter" / "xb18.py"
            adapter.write_bytes(adapter.read_bytes() + b"\n")
            with self.assertRaisesRegex(
                ValueError,
                "DEPENDENCY_SHA256_MISMATCH:adapter_sha256",
            ):
                verify_shadow_receipt(root, REQUEST, VERDICT, receipt_path)

    def test_receipt_rejects_runtime_bind_true(self) -> None:
        bad_verdict = dict(VERDICT)
        bad_verdict["runtime_bind"] = True
        with self.assertRaisesRegex(ValueError, "RUNTIME_BIND_MUST_REMAIN_FALSE"):
            build_shadow_receipt(ROOT, REQUEST, bad_verdict)


if __name__ == "__main__":
    unittest.main()
