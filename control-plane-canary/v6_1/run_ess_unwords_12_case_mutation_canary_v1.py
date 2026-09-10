#!/usr/bin/env python3
import io
import json
import unittest

from test_ess_unwords_abstain_trigger_v1 import UnwordsSemanticGate12CaseCanary

suite = unittest.defaultTestLoader.loadTestsFromTestCase(UnwordsSemanticGate12CaseCanary)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
report = {
    "gate": "ESS_UNWORDS_ABSTAIN_TRIGGER_12_CASE_MUTATION_CANARY_V1",
    "cases_total": result.testsRun,
    "cases_passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "verdict": f"PASS_{result.testsRun}_OF_{result.testsRun}" if result.wasSuccessful() and result.testsRun == 12 else "HOLD_CANARY_NOT_12_OF_12",
    "test_log": stream.getvalue().splitlines(),
}
print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
raise SystemExit(0 if report["verdict"] == "PASS_12_OF_12" else 1)
