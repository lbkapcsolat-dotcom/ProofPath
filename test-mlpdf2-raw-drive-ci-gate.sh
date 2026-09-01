#!/usr/bin/env bash
set -euo pipefail

SOURCE_ID="1B3NTUfOgOdupLO0CsfioiSz-CeUe3jVj"
EXPECTED_SOURCE_SHA="f186cadf85eb4a12cd553dd00140d985138ace2d14c3e46f764567afac9fd127"
EXPECTED_SOURCE_SIZE="29495805"
EXPECTED_PAGE_COUNT="692"
EXPECTED_EXTRACTION_SHA="d89d541ccfa6c68d0e7440f2e50403f7c04fe01c3e7e9c3d688195b7d052faf6"
EXPECTED_EXTRACTION_SIZE="1194587"
EXPECTED_CSTAR_TRACE="583dc16041894817b5f920d65cc1f3b1655334e82c715e306f807f07922f1d1e"

TMPDIR_ML="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ML"' EXIT
PDF="$TMPDIR_ML/source.pdf"
TXT_A="$TMPDIR_ML/extract-a.txt"
TXT_B="$TMPDIR_ML/extract-b.txt"
HEADERS="$TMPDIR_ML/headers.txt"

if ! command -v pdftotext >/dev/null 2>&1 || ! command -v pdfinfo >/dev/null 2>&1; then
  sudo apt-get update -y >/dev/null
  sudo apt-get install -y poppler-utils >/dev/null
fi

DOWNLOAD_URL="https://drive.usercontent.google.com/download?id=${SOURCE_ID}&export=download&confirm=t"
curl --fail --location --silent --show-error --retry 3 --retry-delay 2 --dump-header "$HEADERS" "$DOWNLOAD_URL" --output "$PDF"

SOURCE_SHA="$(sha256sum "$PDF" | awk '{print $1}')"
SOURCE_SIZE="$(stat -c%s "$PDF")"
SOURCE_MIME="$(file --brief --mime-type "$PDF")"
HTTP_CONTENT_TYPE="$(awk 'BEGIN{IGNORECASE=1} /^content-type:/ {gsub(/\r/,""); v=$0} END{sub(/^[^:]+:[[:space:]]*/,"",v); print v}' "$HEADERS")"

echo "OBSERVED_SOURCE_SHA256=${SOURCE_SHA}"
echo "OBSERVED_SOURCE_SIZE=${SOURCE_SIZE}"
echo "OBSERVED_FILE_MIME=${SOURCE_MIME}"
echo "OBSERVED_HTTP_CONTENT_TYPE=${HTTP_CONTENT_TYPE}"

[[ "$SOURCE_SHA" == "$EXPECTED_SOURCE_SHA" ]] || { echo "HOLD_SOURCE_SHA_REVERIFY_FAILED" >&2; exit 21; }
[[ "$SOURCE_SIZE" == "$EXPECTED_SOURCE_SIZE" ]] || { echo "HOLD_SOURCE_SIZE_REVERIFY_FAILED" >&2; exit 22; }
[[ "$SOURCE_MIME" == "application/pdf" ]] || { echo "HOLD_SOURCE_MIME_REVERIFY_FAILED" >&2; exit 29; }

PAGE_COUNT="$(pdfinfo "$PDF" | awk -F: '/^Pages:/ {gsub(/[[:space:]]/,"",$2); print $2}')"
[[ "$PAGE_COUNT" == "$EXPECTED_PAGE_COUNT" ]] || { echo "HOLD_PAGE_COUNT_REVERIFY_FAILED" >&2; exit 23; }

pdftotext -layout "$PDF" "$TXT_A"
pdftotext -layout "$PDF" "$TXT_B"
cmp -s "$TXT_A" "$TXT_B" || { echo "HOLD_EXTRACTION_BYTE_DETERMINISM_FAILED" >&2; exit 24; }

EXTRACTION_SHA_A="$(sha256sum "$TXT_A" | awk '{print $1}')"
EXTRACTION_SHA_B="$(sha256sum "$TXT_B" | awk '{print $1}')"
EXTRACTION_SIZE_A="$(stat -c%s "$TXT_A")"
EXTRACTION_SIZE_B="$(stat -c%s "$TXT_B")"

[[ "$EXTRACTION_SHA_A" == "$EXPECTED_EXTRACTION_SHA" ]] || { echo "HOLD_EXTRACTION_SHA_A_REVERIFY_FAILED" >&2; exit 25; }
[[ "$EXTRACTION_SHA_B" == "$EXPECTED_EXTRACTION_SHA" ]] || { echo "HOLD_EXTRACTION_SHA_B_REVERIFY_FAILED" >&2; exit 26; }
[[ "$EXTRACTION_SIZE_A" == "$EXPECTED_EXTRACTION_SIZE" ]] || { echo "HOLD_EXTRACTION_SIZE_A_REVERIFY_FAILED" >&2; exit 27; }
[[ "$EXTRACTION_SIZE_B" == "$EXPECTED_EXTRACTION_SIZE" ]] || { echo "HOLD_EXTRACTION_SIZE_B_REVERIFY_FAILED" >&2; exit 28; }

node <<'NODE'
const fs = require('fs');
const receipt = JSON.parse(fs.readFileSync('mlpdf2-extraction-candidate-receipt.json', 'utf8'));
const expectedTrace = '583dc16041894817b5f920d65cc1f3b1655334e82c715e306f807f07922f1d1e';
const sourceSha = 'f186cadf85eb4a12cd553dd00140d985138ace2d14c3e46f764567afac9fd127';
const extractionSha = 'd89d541ccfa6c68d0e7440f2e50403f7c04fe01c3e7e9c3d688195b7d052faf6';
if (receipt.status !== 'PASS_EXACT_SOURCE_EXTRACTION_DETERMINISM_8_LAYER_CSTAR_ROUNDTRIP') process.exit(31);
if (receipt.sourceIdentity?.sourceSha256 !== sourceSha) process.exit(32);
if (receipt.extractionDeterminism?.extractionSha256 !== extractionSha) process.exit(33);
if (receipt.candidateTraceSha256 !== expectedTrace) process.exit(34);
NODE

cat > mlpdf2-raw-drive-ci-receipt.json <<JSON
{"gate":"MLPDF2_RAW_DRIVE_DOWNLOAD_IN_CI_SOURCE_SHA_REVERIFY_PDFTOTEXT_RERUN_AB_EXTRACTION_SHA_REVERIFY_EXISTING_CSTAR_RECEIPT_MATCH_V1","status":"PASS_RAW_DRIVE_DOWNLOAD_SOURCE_AND_EXTRACTION_REVERIFIED_CSTAR_MATCH","driveFileId":"${SOURCE_ID}","sourceSha256":"${SOURCE_SHA}","sourceSizeBytes":${SOURCE_SIZE},"pageCount":${PAGE_COUNT},"extraction":{"tool":"pdftotext -layout","runs":2,"byteExact":true,"sha256A":"${EXTRACTION_SHA_A}","sha256B":"${EXTRACTION_SHA_B}","sizeBytesA":${EXTRACTION_SIZE_A},"sizeBytesB":${EXTRACTION_SIZE_B}},"existingCStarTraceSha256":"${EXPECTED_CSTAR_TRACE}","existingCStarReceiptMatch":true,"rawPdfPersisted":false,"extractedTextPersisted":false,"runtimeAdmission":false,"globalBind":false,"pointerPromotion":false,"productionReadinessClaimed":false}
JSON

cat mlpdf2-raw-drive-ci-receipt.json
