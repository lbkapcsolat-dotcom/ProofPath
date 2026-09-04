export function evaluateAdmission({ grant, policy, expected, now, usedNonces }) {
  if (!policy) return { ok: false, reason: 'MISSING_POLICY' };
  if (!expected) return { ok: false, reason: 'MISSING_EXPECTED_CONTRACT' };
  if (!grant) return { ok: false, reason: 'MISSING_GRANT' };

  const nowMs = Date.parse(now);
  const policyStart = Date.parse(policy.not_before);
  const policyEnd = Date.parse(policy.not_after);
  const grantStart = Date.parse(grant.issued_at);
  const grantEnd = Date.parse(grant.expires_at);

  if (policy.enabled !== true) return { ok: false, reason: 'POLICY_DISABLED' };
  if (![nowMs, policyStart, policyEnd, grantStart, grantEnd].every(Number.isFinite)) {
    return { ok: false, reason: 'INVALID_TIME_BOUNDARY' };
  }
  if (nowMs < policyStart) return { ok: false, reason: 'POLICY_NOT_ACTIVE' };
  if (nowMs > policyEnd) return { ok: false, reason: 'POLICY_STALE' };

  if (policy.policy_version !== expected.policy_version || grant.policy_version !== expected.policy_version) {
    return { ok: false, reason: 'WRONG_POLICY_VERSION' };
  }
  if (policy.source_main_sha !== expected.source_main_sha || grant.source_main_sha !== expected.source_main_sha) {
    return { ok: false, reason: 'WRONG_SOURCE_MAIN' };
  }
  if (policy.source_reference_engine_tree !== expected.source_reference_engine_tree || grant.source_reference_engine_tree !== expected.source_reference_engine_tree) {
    return { ok: false, reason: 'WRONG_SOURCE_TREE' };
  }
  if (policy.scope !== expected.scope || grant.scope !== expected.scope) {
    return { ok: false, reason: 'WRONG_SCOPE' };
  }
  if (policy.mantyl_version !== expected.mantyl_version || grant.mantyl_version !== expected.mantyl_version) {
    return { ok: false, reason: 'WRONG_MANTYL_VERSION' };
  }
  if (grant.source_receipt_sha256 !== expected.receipt_sha256) {
    return { ok: false, reason: 'WRONG_RECEIPT' };
  }
  if (grant.gate !== 'MANTYL_REAL_ALPHA_ENFORCED_SCOPED_GRANT_V1' || grant.verdict !== 'ADMIT_BOUNDED') {
    return { ok: false, reason: 'INVALID_GRANT_CONTRACT' };
  }
  if (grant.authority !== 'NONE' || grant.github_permissions !== 'CONTENTS_READ_ONLY' || grant.external_publish !== false || grant.paid_layer_used !== false) {
    return { ok: false, reason: 'LEAST_AUTHORITY_VIOLATION' };
  }
  if (nowMs < grantStart) return { ok: false, reason: 'GRANT_NOT_ACTIVE' };
  if (nowMs > grantEnd) return { ok: false, reason: 'GRANT_STALE' };
  if (typeof grant.nonce !== 'string' || grant.nonce.length === 0) {
    return { ok: false, reason: 'MISSING_NONCE' };
  }
  if ((usedNonces ?? new Set()).has(grant.nonce)) {
    return { ok: false, reason: 'REPLAYED_NONCE' };
  }

  return { ok: true, reason: 'ADMIT_BOUNDED' };
}
