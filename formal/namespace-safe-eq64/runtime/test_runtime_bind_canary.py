import importlib
import json
import tempfile
import unittest
from pathlib import Path


EXPECTED_MATHLIB_REVISION = "0df444a360eaa60ab8c11dca51a86af692955474"
EXPECTED_MATRIX = [
    [True, False, True, False],
    [False, True, False, True],
    [True, False, True, False],
    [False, True, False, True],
]
EXPECTED_NEGATIVE_MATRIX = [
    [True, False, False, False],
    [False, True, False, False],
    [False, False, True, False],
    [False, False, False, True],
]


def load_canary():
    try:
        return importlib.import_module("runtime.runtime_bind_canary")
    except ImportError as exc:
        raise AssertionError(
            "runtime.runtime_bind_canary is required for the exact-SHA/replay gate"
        ) from exc


class EngineIdentityTests(unittest.TestCase):
    def _fixture_package(self, root: Path) -> Path:
        package = root / "formal" / "namespace-safe-eq64"
        package.mkdir(parents=True)
        (package / "RuntimeBindOracle.lean").write_text("oracle-v1\n", encoding="utf-8")
        (package / "MathlibHomologicalComplexBridge.lean").write_text(
            "bridge-v1\n", encoding="utf-8"
        )
        (package / "NatIndexedHomologyGate.lean").write_text(
            "nat-homology-v1\n", encoding="utf-8"
        )
        (package / "lean-toolchain").write_text(
            "leanprover/lean4:v4.33.1\n", encoding="utf-8"
        )
        (package / "lake-manifest.json").write_text(
            json.dumps(
                {
                    "version": "1.2.0",
                    "packages": [
                        {
                            "name": "mathlib",
                            "rev": EXPECTED_MATHLIB_REVISION,
                            "inputRev": EXPECTED_MATHLIB_REVISION,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        binary = package / ".lake" / "build" / "bin" / "runtimeBindOracle"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"oracle-binary-v1\n")
        return package

    def test_engine_sha_changes_after_one_byte_source_mutation(self):
        canary = load_canary()
        with tempfile.TemporaryDirectory() as td:
            package = self._fixture_package(Path(td))
            binary = package / ".lake" / "build" / "bin" / "runtimeBindOracle"
            manifest_a, engine_sha_a = canary.build_engine_identity(
                package, binary, "a" * 40
            )
            oracle = package / "RuntimeBindOracle.lean"
            oracle.write_bytes(oracle.read_bytes() + b"X")
            manifest_b, engine_sha_b = canary.build_engine_identity(
                package, binary, "a" * 40
            )

            self.assertEqual(
                manifest_a["mathlib_revision"], EXPECTED_MATHLIB_REVISION
            )
            self.assertNotEqual(
                manifest_a["oracle_source_sha256"],
                manifest_b["oracle_source_sha256"],
            )
            self.assertNotEqual(engine_sha_a, engine_sha_b)

    def test_mathlib_revision_mismatch_fails_closed(self):
        canary = load_canary()
        with tempfile.TemporaryDirectory() as td:
            package = self._fixture_package(Path(td))
            binary = package / ".lake" / "build" / "bin" / "runtimeBindOracle"
            manifest_path = package / "lake-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["packages"][0]["rev"] = "0" * 40
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "MATHLIB_REVISION_MISMATCH"):
                canary.build_engine_identity(package, binary, "b" * 40)


class OracleValidationTests(unittest.TestCase):
    def _oracle_bytes(self, *, negative: bool) -> bytes:
        payload = {
            "schema": "MATHLIB_RUNTIME_ORACLE_V1",
            "witness": "ZMOD4_H1_BOUNDARY_TIMES_2",
            "degree": 1,
            "representatives": [0, 1, 2, 3],
            "custom_class_equality": EXPECTED_MATRIX,
            "mathlib_class_equality": (
                EXPECTED_NEGATIVE_MATRIX if negative else EXPECTED_MATRIX
            ),
            "class_equal": not negative,
            "negative_control": negative,
        }
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        ) + b"\n"

    def test_positive_and_negative_outputs_are_strictly_validated(self):
        canary = load_canary()
        positive = canary.validate_oracle_output(
            self._oracle_bytes(negative=False), negative=False
        )
        negative = canary.validate_oracle_output(
            self._oracle_bytes(negative=True), negative=True
        )

        self.assertTrue(positive["class_equal"])
        self.assertFalse(negative["class_equal"])
        self.assertTrue(negative["negative_control"])

    def test_negative_control_that_reports_equality_is_rejected(self):
        canary = load_canary()
        payload = json.loads(self._oracle_bytes(negative=True))
        payload["mathlib_class_equality"] = EXPECTED_MATRIX
        payload["class_equal"] = True
        malformed = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"

        with self.assertRaisesRegex(ValueError, "NEGATIVE_CONTROL_NOT_DETECTED"):
            canary.validate_oracle_output(malformed, negative=True)


class ReceiptReplayTests(unittest.TestCase):
    def test_receipt_bytes_are_identical_for_identical_replay(self):
        canary = load_canary()
        fields = dict(
            git_head_sha="c" * 40,
            engine_sha256="1" * 64,
            oracle_binary_sha256="2" * 64,
            witness_sha256="3" * 64,
            positive_output_sha256="4" * 64,
            negative_output_sha256="5" * 64,
            negative_control_detected=True,
            replay_output_equal=True,
        )

        receipt_a = canary.build_receipt(**fields)
        receipt_b = canary.build_receipt(**fields)
        bytes_a = canary.canonical_json_bytes(receipt_a) + b"\n"
        bytes_b = canary.canonical_json_bytes(receipt_b) + b"\n"

        self.assertEqual(bytes_a, bytes_b)
        self.assertEqual(canary.sha256_bytes(bytes_a), canary.sha256_bytes(bytes_b))
        self.assertEqual(receipt_a["authority_scope"], "ISOLATED_CI_CANARY_ONLY")
        self.assertFalse(receipt_a["general_runtime_admission"])
        self.assertFalse(receipt_a["global_bind"])
        self.assertFalse(receipt_a["pointer_promotion"])
        self.assertFalse(receipt_a["production_readiness"])


if __name__ == "__main__":
    unittest.main()
