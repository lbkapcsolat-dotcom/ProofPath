import { normalizeDualLiveClaimRun, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';

export const GEMINI_LIVE_MODEL = 'gemini-3.7-flash';
export const GEMINI_PROVIDER = 'Google';
export const GEMINI_PROVIDER_SURFACE = 'Generative Language API';
export const GEMINI_EXECUTION_MODE = 'LIVE_GEMINI_API';
export const GEMINI_LIVE_PASS = 'PASS_GEMINI_DUAL_LIVE_STRUCTURED_CLAIM_VECTOR';

export function verifyGeminiLiveStructuredReceipt(receipt, bind) {
  if (!receipt || receipt.status !== GEMINI_LIVE_PASS) throw new Error('live Gemini PASS receipt required');
  if (receipt.provider !== GEMINI_PROVIDER) throw new Error('Google provider required');
  if (receipt.providerSurface !== GEMINI_PROVIDER_SURFACE) throw new Error('Generative Language API provider surface required');
  if (receipt.executionMode !== GEMINI_EXECUTION_MODE) throw new Error('LIVE_GEMINI_API execution mode required');
  if (receipt.model !== GEMINI_LIVE_MODEL) throw new Error('gemini-3.7-flash model required');
  if (receipt.packetSha256 !== bind.packetSha256) throw new Error('live Gemini receipt packet mismatch');
  if (receipt.claimSchema !== STRUCTURED_CLAIM_SCHEMA) throw new Error('live Gemini claim schema mismatch');
  if (receipt.claimOntology !== DUAL_LIVE_CLAIM_ONTOLOGY_ID) throw new Error('live Gemini claim ontology mismatch');
  if (receipt.liveInferenceExecuted !== true) throw new Error('live Gemini inference evidence required');
  if (receipt.zeroCorpusWrites !== true || receipt.authorityMutation !== false || receipt.pointerPromotion !== false || receipt.globalBind !== false || receipt.runtimeAdmission !== false || receipt.externalActuation !== false) {
    throw new Error('live Gemini receipt boundary violation');
  }
  return normalizeDualLiveClaimRun(receipt.run, bind);
}
