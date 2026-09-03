import assert from 'node:assert/strict';
import { semanticExitCode } from './gate-status.mjs';

assert.equal(semanticExitCode('PASS_AUTH_MODEL_READY'), 0);
assert.equal(semanticExitCode('PASS_GPT_LIVE_OPENAI_API_STRUCTURED_CLAIM_VECTOR'), 0);
assert.equal(semanticExitCode('HOLD_GEMINI_LIVE_HTTP_503'), 2);
assert.equal(semanticExitCode('HOLD_ZERO_SPEND_LIVE_INFERENCE_SURFACE_NOT_PROVEN'), 2);
assert.equal(semanticExitCode('FAIL_PACKET_IDENTITY'), 1);
assert.equal(semanticExitCode('UNKNOWN_STATUS'), 1);

console.log('PASS true dual-live fail-closed semantic exit codes');
