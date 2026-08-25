
import { TRAINING_SET, HOLDOUT_SET, trainSoftmax, predict } from "./model.js";
const model=trainSoftmax(TRAINING_SET);
const claimEl=document.querySelector("#claim");
const evidenceEl=document.querySelector("#evidence");
const form=document.querySelector("#proofForm");
const resultEl=document.querySelector("#result");
const probsEl=document.querySelector("#probabilities");
const explanationEl=document.querySelector("#explanation");
const exampleSelect=document.querySelector("#exampleSelect");
const modelStatus=document.querySelector("#modelStatus");
function pct(x){return `${(x*100).toFixed(1)}%`;}
function explain(label){
  if(label==="SUPPORTED") return "The supplied evidence has enough matching support signals for this compact classifier to place the pair in the SUPPORTED class.";
  if(label==="CONTRADICTED") return "The supplied evidence contains strong conflict signals, such as negation, opposite terms, or incompatible numeric information.";
  return "The evidence does not clearly support or contradict the claim. ProofPath keeps the conclusion conservative instead of forcing a yes/no answer.";
}
function learning(label){
  if(label==="SUPPORTED") return "Learning step: ask whether an independent source supports the same claim.";
  if(label==="CONTRADICTED") return "Learning step: identify the exact word, number, or relation that conflicts with the claim.";
  return "Learning step: name the missing evidence that would make the claim testable.";
}
export function analyze(claim,evidence){
  if(!claim.trim()) return {status:"BLOCK",message:"Add a claim first."};
  if(!evidence.trim()) return {status:"BLOCK",message:"Add evidence first."};
  return {status:"READY",...predict(model,claim,evidence)};
}
function render(out){
  if(out.status==="BLOCK"){resultEl.textContent="BLOCK";probsEl.textContent="";explanationEl.textContent=out.message;return;}
  resultEl.textContent=out.label;
  const p=out.probabilities;
  probsEl.textContent=`SUPPORTED ${pct(p.SUPPORTED)} · CONTRADICTED ${pct(p.CONTRADICTED)} · INSUFFICIENT ${pct(p.INSUFFICIENT)}`;
  explanationEl.innerHTML=`<p>${explain(out.label)}</p><p><strong>${learning(out.label)}</strong></p>`;
}
form.addEventListener("submit",e=>{e.preventDefault();render(analyze(claimEl.value,evidenceEl.value));});
HOLDOUT_SET.forEach((demo,i)=>{
  const o=document.createElement("option");o.value=String(i);o.textContent=`${demo.label}: ${demo.claim}`;exampleSelect.appendChild(o);
});
exampleSelect.addEventListener("change",()=>{
  const demo=HOLDOUT_SET[Number(exampleSelect.value)];
  if(!demo)return;claimEl.value=demo.claim;evidenceEl.value=demo.evidence;render(analyze(demo.claim,demo.evidence));
});
modelStatus.textContent=`Offline ML ready · ${TRAINING_SET.length} training pairs · ${HOLDOUT_SET.length} untouched holdout/demo pairs · no API · no CDN · no account`;
