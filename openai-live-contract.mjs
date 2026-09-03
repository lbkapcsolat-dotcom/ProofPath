import { normalizeDualLiveClaimRun, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';

export const OPENAI_LIVE_MODEL = 'gpt-5.6-sol';
export const OPENAI_PROVIDER = 'OpenAI';
export const OPENAI_PROVIDER_SURFACE = 'Responses API';
export const OPENAI_EXECUTION_MODE = 'LIVE_OPENAI_API';
export const OPENAI_LIVE_PASS = 'PASS_GPT_LIVE_OPENAI_API_STRUCTURED_CLAIM_VECTOR';

export function verifyOpenAiLiveStructuredReceipt(receipt, bind) {
  if (!receipt || receipt.status !== OPENAI_LIVE_PASS) throw new Error('live OpenAI PASS receipt required');
  if (receipt.provider !== OPENAI_PROVIDER) throw new Error('OpenAI provider required');
  if (receipt.providerSurface !== OPENAI_PROVIDER_SURFACE) throw new Error('Responses API provider surface required');
  if (receipt.executionMode !== OPENAI_EXECUTION_MODE) throw new Error('LIVE_OPENAI_API execution mode required');
  if (receipt.model !== OPENAI_LIVE_MODEL) throw new Error('gpt-5.6-sol model required');
  if (receipt.packetSha256 !== bind.packetSha256) throw new Error('live OpenAI receipt packet mismatch');
  if (receipt.claimSchema !== STRUCTURED_CLAIM_SCHEMA) throw new Error('live OpenAI claim schema mismatch');
  if (receipt.claimOntology !== DUAL_LIVE_CLAIM_ONTOLOGY_ID) throw new Error('live OpenAI claim ontology mismatch');
  if (receipt.liveInferenceExecuted !== true) throw new Error('live inference evidence required');
  if (receipt.zeroCorpusWrites !== true || receipt.authorityMutation !== false || receipt.pointerPromotion !== false || receipt.globalBind !== false || receipt.runtimeAdmission !== false || receipt.externalActuation !== false) {
    throw new Error('live OpenAI receipt boundary violation');
  }
  return normalizeDualLiveClaimRun(receipt.run, bind);
}
