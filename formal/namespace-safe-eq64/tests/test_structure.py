import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from namespace_safe_engine import (
    all_states, check_structural_mapping, decode_state, encode_state,
    hamming_distance, load_namespace, normalize_polarity, validate_namespace,
)

class StructureTests(unittest.TestCase):
    def setUp(self):
        self.ess = load_namespace(ROOT / "fixtures" / "ess_eq64_6d_kernel.json")
        self.aip = load_namespace(ROOT / "fixtures" / "x_aiprbg_6gate.json")

    def test_fixture_validation(self):
        validate_namespace(self.ess)
        validate_namespace(self.aip)

    def test_64_states_and_roundtrip(self):
        states = all_states()
        self.assertEqual(len(states), 64)
        self.assertEqual(len(set(states)), 64)
        for state in states:
            self.assertEqual(decode_state(encode_state(state)), state)

    def test_normalization_is_involution_for_ess(self):
        for state in all_states():
            self.assertEqual(normalize_polarity(self.ess, normalize_polarity(self.ess, state)), state)

    def test_identity_structural_mapping(self):
        result = check_structural_mapping(tuple(range(6)))
        self.assertEqual(result, {"meet_preserved": True, "join_preserved": True, "hamming_preserved": True})

    def test_hamming_examples(self):
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,0,0,0,0,0)), 1)
        self.assertEqual(hamming_distance((0,0,0,0,0,0), (1,1,0,0,0,0)), 2)

if __name__ == "__main__":
    unittest.main()
