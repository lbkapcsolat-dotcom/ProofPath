import test from 'node:test';
import assert from 'node:assert/strict';
import { getRevenueCatConfig } from '../src/revenuecat-config.mjs';

test('missing Test Store key fails closed', () => {
  assert.deepEqual(getRevenueCatConfig({}), { ready: false, apiKey: null, entitlementId: 'evidence_plus' });
});

test('configured key is returned without modification', () => {
  const result = getRevenueCatConfig({ EXPO_PUBLIC_REVENUECAT_TEST_API_KEY: 'test_key_value', EXPO_PUBLIC_REVENUECAT_ENTITLEMENT_ID: 'plus' });
  assert.deepEqual(result, { ready: true, apiKey: 'test_key_value', entitlementId: 'plus' });
});
