# RevenueCat Next Gen Android Build Receipt V1

- Project: Evidence Coach Pocket
- Branch: `revenuecat-nextgen-evidence-coach-pocket-v1`
- Build input commit: `6a9e967ed3c931649dcd782ab0c515c274e90c45`
- GitHub Actions workflow: `RevenueCat Next Gen Android`
- Workflow run ID: `34410522599`
- Job ID: `102663612872`
- Workflow conclusion: `success`
- Unit tests: 8/8 PASS
- Secret guard: `PASS_NO_REVENUECAT_SECRET_COMMITTED`
- Expo Doctor: PASS
- Expo Android prebuild: PASS
- Gradle `assembleDebug`: PASS
- Artifact upload: PASS

## Artifact readback

- GitHub artifact ID: `10127286891`
- Artifact name: `evidence-coach-pocket-debug-apk`
- Artifact archive size reported by GitHub: `50,657,002` bytes
- Artifact archive SHA256: `c4655947d1ebc80800d1b0816f3bc8892fb1af9418745645daba91778ac77c9a`
- Independent downloaded archive SHA256: `c4655947d1ebc80800d1b0816f3bc8892fb1af9418745645daba91778ac77c9a`
- ZIP members: exactly 1
- APK member: `app-debug.apk`
- APK bytes: `139,363,063`
- APK SHA256: `d7d435eecfd41dbc98f3635346e036e1fd7ad09daf4e18c6cf871cf94d98a81f`

## Verdict

`PASS_ANDROID_DEBUG_APK_BUILD_AND_BYTE_READBACK`

## Remaining HOLD

This receipt does not prove a live RevenueCat Test Store transaction. The following remain required before that gate can pass:

- RevenueCat Project ID
- Test Store product
- current Offering containing the test package
- `evidence_plus` entitlement binding
- Test Store public SDK key injected outside source control
- real device/development-build Test Store purchase
- CustomerInfo readback showing the entitlement active
- RevenueCat dashboard sandbox transaction readback

Claim ceiling: development Android build and artifact byte identity only. No production billing, app-store readiness, competition eligibility, scientific validation, or Devpost submission PASS is claimed here.
