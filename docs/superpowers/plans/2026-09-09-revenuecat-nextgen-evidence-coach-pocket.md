# RevenueCat Next Gen Evidence Coach Pocket Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a zero-spend Android debug APK containing a tested Evidence Coach flow and RevenueCat Test Store integration boundary.

**Architecture:** A standalone Expo 57 app lives under `revenuecat-nextgen/`. Pure logic is Node-testable; `src/revenuecat-native.js` is the only native SDK adapter. CI prebuilds Android and runs Gradle `assembleDebug`.

**Tech Stack:** Expo SDK 57, React 19.2.3, React Native 0.86, react-native-purchases 10.9.0, Node 22 tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-09-revenuecat-nextgen-evidence-coach-pocket-design.md`

## Global Constraints
- ZERO_SPEND.
- No RevenueCat API key or secret committed to GitHub.
- Test Store only for development evidence.
- No production/store readiness claim.
- Missing Project ID, key, product/offering, entitlement, student-email or guardian-consent evidence stays HOLD.

### Task 1: Pure evidence logic
- [x] Write failing tests for blank input, contradiction, and support.
- [x] Verify RED due to missing module.
- [x] Implement minimal deterministic classifier.
- [x] Verify tests GREEN.

### Task 2: RevenueCat fail-closed orchestration
- [x] Write failing tests for missing key, bootstrap, offering selection, and purchase entitlement.
- [x] Verify RED due to missing service module.
- [x] Implement dependency-injected service.
- [x] Verify all Node tests GREEN.

### Task 3: Android UI and native adapter
- [x] Wire the tested modules into one responsive screen.
- [x] Keep Test Store key environment-only.
- [x] Show explicit HOLD when RevenueCat is not configured.

### Task 4: Secret guard and CI APK build
- [x] Add repository secret scanner.
- [x] Push branch files.
- [ ] Require Node tests + secret guard PASS in CI.
- [ ] Require Expo Android prebuild + Gradle `assembleDebug` PASS.
- [ ] Record APK artifact identity/readback.

### Task 5: Real RevenueCat Test Store runtime evidence
- [ ] Configure external Test Store Project ID, product, current Offering, `evidence_plus` entitlement and public SDK key without spending money.
- [ ] Build/run with Test Store key injected outside source control.
- [ ] Complete simulated successful purchase.
- [ ] Verify CustomerInfo activates `evidence_plus` and dashboard shows sandbox transaction.

### Task 6: Next Gen submission assets and eligibility
- [ ] Verify student/academic email accepted by the competition.
- [ ] Verify guardian consent if entrant is a minor.
- [ ] Produce 1024×1024 icon and 1179×2556 screenshot.
- [ ] Produce <2 minute public YouTube/Vimeo demo from the working app.
- [ ] Fill RevenueCat Project ID and Next Gen repo fields.
- [ ] Submit only after all required fields and eligibility gates are PASS.
