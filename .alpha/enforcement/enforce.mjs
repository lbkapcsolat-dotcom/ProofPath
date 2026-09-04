export function evaluateAdmission({ grant, policy, expected, now, usedNonces }) {
  if (!grant || !policy || !expected) return { ok: false, reason: 'DENY' };
  const nowMs = Date.parse(now);
  const checks = [
    policy.enabled === true,
    policy.policy_version === expected.policy_version,
    policy.source_main_sha === expected.source_main_sha,
    policy.source_reference_engine_tree === expected.source_reference_engine_tree,
    policy.scope === expected.scope,
    policy.mantyl_version === expected.mantyl_version,
    Date.parse(policy.not_before) <= nowMs,
    nowMs <= Date.parse(policy.not_after),
    grant.gate === 'MANTYL_REAL_ALPHA_ENFORCED_SCOPED_GRANT_V1',
    grant.policy_version === expected.policy_version,
    grant.source_receipt_sha256 === expected.receipt_sha256,
    grant.source_main_sha === expected.source_main_sha,
    grant.source_reference_engine_tree === expected.source_reference_engine_tree,
    grant.scope === expected.scope,
    grant.mantyl_version === expected.mantyl_version,
    grant.authority === 'NONE',
    grant.github_permissions === 'CONTENTS_READ_ONLY',
    grant.external_publish === false,
    grant.paid_layer_used === false,
    grant.verdict === 'ADMIT_BOUNDED',
    Date.parse(grant.issued_at) <= nowMs,
    nowMs <= Date.parse(grant.expires_at),
    typeof grant.nonce === 'string' && grant.nonce.length > 0,
    !(usedNonces ?? new Set()).has(grant.nonce)
  ];
  return checks.every(Boolean)
    ? { ok: true, reason: 'ADMIT_BOUNDED' }
    : { ok: false, reason: 'DENY' };
}
