function isEntitlementActive(customerInfo, entitlementId) {
  return Boolean(customerInfo?.entitlements?.active?.[entitlementId]?.isActive ?? customerInfo?.entitlements?.active?.[entitlementId]);
}

export function createRevenueCatService({ purchases, config, logLevel }) {
  return {
    async bootstrap() {
      if (!config?.ready || !config?.apiKey) {
        return { state: 'NOT_CONFIGURED', isPremium: false, packageToBuy: null };
      }
      if (typeof purchases.setLogLevel === 'function') purchases.setLogLevel(logLevel);
      purchases.configure({ apiKey: config.apiKey });
      const [customerInfo, offerings] = await Promise.all([
        purchases.getCustomerInfo(),
        purchases.getOfferings(),
      ]);
      return {
        state: 'READY',
        isPremium: isEntitlementActive(customerInfo, config.entitlementId),
        packageToBuy: offerings?.current?.availablePackages?.[0] ?? null,
      };
    },

    async purchase(aPackage) {
      if (!config?.ready || !config?.apiKey) {
        return { state: 'NOT_CONFIGURED', isPremium: false };
      }
      if (!aPackage) {
        return { state: 'NO_PACKAGE', isPremium: false };
      }
      const { customerInfo } = await purchases.purchasePackage(aPackage);
      return {
        state: 'PURCHASED',
        isPremium: isEntitlementActive(customerInfo, config.entitlementId),
      };
    },
  };
}
