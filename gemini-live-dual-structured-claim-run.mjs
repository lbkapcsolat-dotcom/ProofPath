import fs from 'node:fs';
import { buildCorpusCallosumReadOnlyBind } from './corpus-callosum-contract.mjs';
import { buildDualLiveStructuredClaimPrompt, normalizeDualLiveClaimRun, DUAL_LIVE_CLAIM_ONTOLOGY_ID } from './dual-live-structured-claim-contract.mjs';
import { STRUCTURED_CLAIM_SCHEMA } from './structured-claim-contract.mjs';

const MODEL='gemini-3.7-flash';
const GATE='ALPHA_NSH_DUAL_LIVE_STRUCTURED_CLAIM_EXECUTION_AND_ADJUDICATION_V1';
const fixture=JSON.parse(fs.readFileSync(new URL('./corpus-callosum-current-authority-fixture.json', import.meta.url),'utf8'));
const auth=JSON.parse(fs.readFileSync(new URL('./gemini-live-execution-authorization.json', import.meta.url),'utf8'));
const bind=await buildCorpusCallosumReadOnlyBind(fixture);
const receipt={gate:GATE,status:'HOLD',claimSchema:STRUCTURED_CLAIM_SCHEMA,claimOntology:DUAL_LIVE_CLAIM_ONTOLOGY_ID,packetSha256:bind.packetSha256,model:MODEL,freeTierAuthorized:auth.authorized===true,keyConfigured:Boolean(process.env.GEMINI_API_KEY),authenticatedModelSurface:false,liveInferenceExecuted:false,zeroCorpusWrites:true,authorityMutation:false,pointerPromotion:false,globalBind:false,runtimeAdmission:false,externalActuation:false};
if(bind.packetSha256!==auth.packetSha256||bind.packetSha256!==fixture.expectedPacketSha256){receipt.status='HOLD_SHARED_PACKET_IDENTITY_MISMATCH';console.log(JSON.stringify(receipt));process.exit(0);}
if(auth.modelTarget!==MODEL||auth.authorized!==true){receipt.status='HOLD_GEMINI_MODEL_AUTHORIZATION';console.log(JSON.stringify(receipt));process.exit(0);}
if(!process.env.GEMINI_API_KEY){receipt.status='HOLD_GEMINI_API_KEY_NOT_CONFIGURED';console.log(JSON.stringify(receipt));process.exit(0);}
const modelsResponse=await fetch('https://generativelanguage.googleapis.com/v1beta/models',{headers:{'x-goog-api-key':process.env.GEMINI_API_KEY}});
if(!modelsResponse.ok){receipt.status=`HOLD_GEMINI_MODEL_SURFACE_HTTP_${modelsResponse.status}`;console.log(JSON.stringify(receipt));process.exit(0);}
const models=await modelsResponse.json();
receipt.authenticatedModelSurface=(models.models||[]).map(m=>String(m.name||'').replace(/^models\//,'')).includes(MODEL);
if(!receipt.authenticatedModelSurface){receipt.status='HOLD_GEMINI_MODEL_NOT_AVAILABLE';console.log(JSON.stringify(receipt));process.exit(0);}
const prompt=buildDualLiveStructuredClaimPrompt('GEMINI',bind);
const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`,{method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':process.env.GEMINI_API_KEY},body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{responseMimeType:'application/json'}})});
receipt.liveInferenceExecuted=true;
if(!response.ok){receipt.status=`HOLD_GEMINI_DUAL_LIVE_HTTP_${response.status}`;console.log(JSON.stringify(receipt));process.exit(0);}
const payload=await response.json();
const text=payload?.candidates?.[0]?.content?.parts?.[0]?.text;
if(!text){receipt.status='HOLD_GEMINI_DUAL_LIVE_EMPTY';console.log(JSON.stringify(receipt));process.exit(0);}
let candidate; try{candidate=JSON.parse(text);}catch{receipt.status='HOLD_GEMINI_DUAL_LIVE_MALFORMED_JSON';console.log(JSON.stringify(receipt));process.exit(0);}
try{receipt.run=normalizeDualLiveClaimRun({consumer:'GEMINI',...candidate},bind);}catch(error){receipt.status=`HOLD_GEMINI_DUAL_LIVE_CONTRACT_REJECTED__${String(error?.message||'unknown').replace(/\s+/g,'_')}`;console.log(JSON.stringify(receipt));process.exit(0);}
receipt.status='PASS_GEMINI_DUAL_LIVE_STRUCTURED_CLAIM_VECTOR';
console.log(JSON.stringify(receipt));
