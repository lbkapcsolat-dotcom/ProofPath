import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateAdmission } from './enforce.mjs';

const MAIN = '5952ba59762bc9cb800e3fa82ab61748b25728c3';
const TREE = 'efd70b2eccea206e9a7a51f1d115cfeb29180b89';
const RECEIPT_SHA = 'cd38e3e4ab7950ca7bc2536958d0cc6d51a6df52c0e2214b832fb51f60aa4d77';
const POLICY_VERSION = 'MANTYL_ENFORCED_SCOPED_V1';
const SCOPE = 'REFERENCE_ENGINE_EXISTING_VERIFICATION_COMMANDS_ONLY';

function validFixture() {
  return {
    now: '2026-09-04T21:20:00.000Z',
    policy: {
      enabled: true,
      policy_version: POLICY_VERSION,
      not_before: '2026-09-01T00:00:00.000Z',
      not_after: '2026-12-31T23:59:59.000Z',
      source_main_sha: MAIN,
      source_reference_engine_tree: TREE,
      scope: SCOPE,
      mantyl_version: '0.5.0'
    },
    grant: {
      gate: 'MANTYL_REAL_ALPHA_ENFORCED_SCOPED_GRANT_V1',
      policy_version: POLICY_VERSION,
      source_receipt_sha256: RECEIPT_SHA,
      source_main_sha: MAIN,
      source_reference_engine_tree: TREE,
      scope: SCOPE,
      mantyl_version: '0.5.0',
      nonce: 'nonce-A',
      issued_at: '2026-09-04T21:19:00.000Z',
      expires_at: '2026-09-04T21:25:00.000Z',
      authority: 'NONE',
      github_permissions: 'CONTENTS_READ_ONLY',
      external_publish: false,
      paid_layer_used: false,
      verdict: 'ADMIT_BOUNDED'
    },
    expected: {
      receipt_sha256: RECEIPT_SHA,
      source_main_sha: MAIN,
      source_reference_engine_tree: TREE,
      policy_version: POLICY_VERSION,
      scope: SCOPE,
      mantyl_version: '0.5.0'
    },
    usedNonces: new Set()
  };
}

test('exact valid grant admits the exact governed reference_engine scope', () => {
  const result = evaluateAdmission(validFixture());
  assert.deepEqual(result, { ok: true, reason: 'ADMIT_BOUNDED' });
});
