import Purchases, { LOG_LEVEL, PurchasesOffering } from 'react-native-purchases';

export type RevenueCatState = {
  configured: boolean;
  offering: PurchasesOffering | null;
  message: string;
};

let configured = false;

export async function initializeRevenueCatPreview(): Promise<RevenueCatState> {
  const apiKey = process.env.EXPO_PUBLIC_REVENUECAT_API_KEY;

  if (!apiKey) {
    return {
      configured: false,
      offering: null,
      message: 'Add the public RevenueCat SDK key to enable the preview integration.',
    };
  }

  if (!configured) {
    Purchases.setLogLevel(LOG_LEVEL.INFO);
    Purchases.configure({ apiKey });
    configured = true;
  }

  try {
    const offerings = await Purchases.getOfferings();
    return {
      configured: true,
      offering: offerings.current ?? null,
      message: offerings.current
        ? 'RevenueCat preview offering loaded successfully.'
        : 'RevenueCat is configured, but no current offering is available yet.',
    };
  } catch (error) {
    return {
      configured: true,
      offering: null,
      message: error instanceof Error ? error.message : 'RevenueCat preview lookup failed.',
    };
  }
}
