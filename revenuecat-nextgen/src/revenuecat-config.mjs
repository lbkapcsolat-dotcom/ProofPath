export function getRevenueCatConfig(env = {}) {
  const apiKey = String(env.EXPO_PUBLIC_REVENUECAT_TEST_API_KEY ?? '').trim();
  const entitlementId = String(env.EXPO_PUBLIC_REVENUECAT_ENTITLEMENT_ID ?? 'evidence_plus').trim() || 'evidence_plus';
  return { ready: apiKey.length > 0, apiKey: apiKey || null, entitlementId };
}
