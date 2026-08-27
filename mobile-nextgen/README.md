# ProofPath Mobile — RevenueCat Shipaton 2026 Next Gen

ProofPath Mobile is a bounded educational evidence-assessment prototype adapted for the RevenueCat Shipaton 2026 Next Gen track.

## What this branch adds

- Expo / React Native mobile shell for Android and iOS.
- Deterministic local claim-versus-evidence assessment.
- RevenueCat React Native SDK integration.
- RevenueCat offering readback in Expo Preview API Mode.
- Explicit zero-spend guardrail: this prototype contains no purchase action and does not initiate a transaction.

## RevenueCat public configuration

Only two public/non-secret values are needed for this prototype:

1. `EXPO_PUBLIC_REVENUECAT_PROJECT_ID`
   - RevenueCat dashboard -> Project Settings -> General -> Project ID.
2. `EXPO_PUBLIC_REVENUECAT_API_KEY`
   - RevenueCat dashboard -> Project Settings -> API keys -> App specific keys.
   - Use ONLY the public/SDK key. Never place a secret `sk_` key in this client repository.

Copy `.env.example` to `.env` and replace the placeholders with the real public values.

## Run

```bash
cd mobile-nextgen
npm install
npx expo start
```

RevenueCat documents that `react-native-purchases` automatically uses Preview API Mode in Expo Go. Preview mode can exercise subscription-related application logic without a real purchase. A development build is required for real in-app purchases.

## Runtime offering readback gate

The app configures the RevenueCat SDK with the public SDK key and calls `Purchases.getOfferings()`.

PASS condition:

- SDK config succeeds, and
- `offerings.current` is non-null, and
- the UI displays the current offering/package metadata.

HOLD conditions:

- missing public SDK key,
- SDK configuration error,
- no current offering configured,
- offering lookup error.

The project ID is retained for Devpost submission/readback evidence; it is not a secret and is not used by the client SDK for initialization.

## Submission claim ceiling

This build demonstrates a mobile evidence-assessment experience and RevenueCat SDK/offering integration in a non-transactional preview configuration. It does **not** prove that a real store purchase has been completed, does not claim production monetization readiness, and does not claim general-world evidence-classification accuracy.

`EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY`

## Remaining admission gates before Devpost submission

1. Read back the RevenueCat project ID and public SDK key from the authenticated dashboard.
2. Confirm a current offering can be read through the SDK in the demo environment.
3. Confirm student/academic email eligibility for the Next Gen category.
4. Add an open-source license acceptable for the public repository. No repository-wide license choice is made automatically by this branch.
5. Produce a <=2 minute public YouTube/Vimeo demonstration.
6. Provide the required 1024x1024 icon and 1179x2556 screenshot.
7. Hash the final repo/video/submission payload and perform Devpost remote readback after submission.
