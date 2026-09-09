import test from 'node:test';
import assert from 'node:assert/strict';
import { createRevenueCatService } from '../src/revenuecat-service.mjs';

test('bootstrap stays fail-closed when config is missing', async () => {
  let configureCalls = 0;
  const purchases = { configure() { configureCalls += 1; } };
  const service = createRevenueCatService({ purchases, config: { ready: false, apiKey: null, entitlementId: 'evidence_plus' }, logLevel: 'DEBUG' });
  const result = await service.bootstrap();
  assert.equal(result.state, 'NOT_CONFIGURED');
  assert.equal(configureCalls, 0);
});

test('bootstrap configures Test Store and returns current package and entitlement state', async () => {
  const calls = [];
  const pkg = { identifier: '$rc_monthly' };
  const purchases = {
    setLogLevel(level) { calls.push(['log', level]); },
    configure(opts) { calls.push(['configure', opts]); },
    async getCustomerInfo() { return { entitlements: { active: { evidence_plus: { isActive: true } } } }; },
    async getOfferings() { return { current: { availablePackages: [pkg] } }; },
  };
  const service = createRevenueCatService({ purchases, config: { ready: true, apiKey: 'test_key', entitlementId: 'evidence_plus' }, logLevel: 'DEBUG' });
  const result = await service.bootstrap();
  assert.equal(result.state, 'READY');
  assert.equal(result.isPremium, true);
  assert.equal(result.packageToBuy, pkg);
  assert.deepEqual(calls[1], ['configure', { apiKey: 'test_key' }]);
});

test('purchase reports entitlement unlocked after successful Test Store purchase', async () => {
  const pkg = { identifier: '$rc_monthly' };
  const purchases = {
    async purchasePackage(received) {
      assert.equal(received, pkg);
      return { customerInfo: { entitlements: { active: { evidence_plus: { isActive: true } } } } };
    },
  };
  const service = createRevenueCatService({ purchases, config: { ready: true, apiKey: 'test_key', entitlementId: 'evidence_plus' }, logLevel: 'DEBUG' });
  const result = await service.purchase(pkg);
  assert.deepEqual(result, { state: 'PURCHASED', isPremium: true });
});
