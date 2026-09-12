# RevenueCat Next Gen Evidence Coach Pocket Design

## Goal
Build a zero-spend Android-first Expo/React Native app that demonstrates a bounded evidence-assessment flow and a real RevenueCat Test Store purchase/entitlement path without committing secrets or requiring Google Play publication.

## Architecture
The app is isolated under `revenuecat-nextgen/` in the existing public ProofPath repository. Pure evidence and RevenueCat orchestration logic are dependency-free modules tested with Node's built-in test runner. A thin native adapter injects `react-native-purchases` into the tested service. The UI remains one screen: claim, evidence, verdict, next-evidence guidance, and an optional Test Store unlock for a deeper checklist.

## RevenueCat boundary
Development uses only `EXPO_PUBLIC_REVENUECAT_TEST_API_KEY` and defaults to entitlement `evidence_plus`. Missing configuration produces `NOT_CONFIGURED`; no key is stored in source. The app selects the first package from the current RevenueCat Offering and unlocks only when the configured entitlement is active in returned CustomerInfo.

## Verification
TDD covers evidence classification, fail-closed configuration, RevenueCat bootstrap, and successful entitlement unlock. CI runs tests, secret scanning, Expo prebuild, and Android `assembleDebug`. A real Test Store transaction remains a separate runtime gate requiring a RevenueCat Project ID, Test Store SDK key, product/offering, and entitlement configuration.

## Claim ceiling
A successful build proves only that the Android debug artifact compiles with the RevenueCat native SDK. A successful Test Store transaction proves only that the sandbox purchase flow updates the configured RevenueCat entitlement. Neither proves production billing, store readiness, business viability, scientific correctness, or competition eligibility beyond the verified rules.
