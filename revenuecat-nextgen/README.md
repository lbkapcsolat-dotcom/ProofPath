# Evidence Coach Pocket — RevenueCat Next Gen

Android-first Expo/React Native prototype for the RevenueCat Shipaton 2026 Next Gen Award.

## Zero-spend purchase testing

The app uses RevenueCat **Test Store** only during development. No API key is committed. Set these environment variables outside source control before a real Test Store run:

- `EXPO_PUBLIC_REVENUECAT_TEST_API_KEY` → your Test Store public SDK key
- `EXPO_PUBLIC_REVENUECAT_ENTITLEMENT_ID` → `evidence_plus`

The app fails closed when the key is missing. For a real Test Store transaction, configure a Test Store product, attach it to the current Offering, and attach the product to the `evidence_plus` entitlement in RevenueCat.

## Verify

```bash
npm test
npm run verify:secrets
```

## Android build

```bash
npm install
npx expo prebuild --platform android
cd android
./gradlew assembleDebug
```

The debug APK is for development/testing only. Do not submit a Test Store API key to a production app store build.

## Claim boundary

`EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`

The classifier is a compact deterministic teaching aid, not a fact checker, scientific validator, calibrated confidence model, or decision authority.
