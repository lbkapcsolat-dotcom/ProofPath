import { trainSoftmax, predict } from "./model.js";
import { EARTH_TRAINING_SET, EARTH_HOLDOUT_SET } from "./earth-data.js";
import { detectEarthCategory, nextEvidenceNeeded } from "./earth-logic.js";

const CLAIM_CEILING = "EDUCATIONAL_ENVIRONMENTAL_EVIDENCE_ASSESSMENT_ONLY";
const model = trainSoftmax(EARTH_TRAINING_SET);

const claimEl = document.querySelector("#claim");
const evidenceEl = document.querySelector("#evidence");
const form = document.querySelector("#proofForm");
const resultEl = document.querySelector("#result");
const probsEl = document.querySelector("#probabilities");
const explanationEl = document.querySelector("#explanation");
const exampleSelect = document.querySelector("#exampleSelect");
const modelStatus = document.querySelector("#modelStatus");
const categoryEl = document.querySelector("#category");
const nextEvidenceEl = document.querySelector("#nextEvidence");

function pct(x){ return `${(x*100).toFixed(1)}%`; }

function explain(label){
  if(label === "SUPPORTED") return "The supplied evidence contains enough matching support signals for this compact educational classifier to place the pair in the SUPPORTED class.";
  if(label === "CONTRADICTED") return "The supplied evidence contains strong conflict signals such as negation, opposite terms, or incompatible relationships.";
  return "The evidence does not clearly justify or refute the claim. Earth Evidence keeps the conclusion conservative instead of converting partial evidence into certainty.";
}

export function analyze(claim,evidence){
  if(!claim.trim()) return {status:"BLOCK",message:"Add an environmental claim first."};
  if(!evidence.trim()) return {status:"BLOCK",message:"Add evidence first."};
  const category = detectEarthCategory(claim,evidence);
  const out = predict(model,claim,evidence);
  return {...out,status:"READY",category,claim_ceiling:CLAIM_CEILING,next_evidence:nextEvidenceNeeded(out.label,category)};
}

function render(out){
  if(out.status === "BLOCK"){
    resultEl.textContent = "BLOCK";
    probsEl.textContent = "";
    categoryEl.textContent = "Category: —";
    explanationEl.textContent = out.message;
    nextEvidenceEl.textContent = "";
    return;
  }
  resultEl.textContent = out.label;
  categoryEl.textContent = `Earth category: ${out.category}`;
  const p = out.probabilities;
  probsEl.textContent = `MODEL SCORE DISTRIBUTION · SUPPORTED ${pct(p.SUPPORTED)} · CONTRADICTED ${pct(p.CONTRADICTED)} · INSUFFICIENT ${pct(p.INSUFFICIENT)}`;
  explanationEl.innerHTML = `<p>${explain(out.label)}</p>`;
  nextEvidenceEl.innerHTML = `<strong>Next evidence needed:</strong> ${out.next_evidence}`;
}

form.addEventListener("submit",e=>{
  e.preventDefault();
  render(analyze(claimEl.value,evidenceEl.value));
});

EARTH_HOLDOUT_SET.forEach((demo,i)=>{
  const o = document.createElement("option");
  o.value = String(i);
  o.textContent = `${demo.category} · ${demo.label}: ${demo.claim}`;
  exampleSelect.appendChild(o);
});

exampleSelect.addEventListener("change",()=>{
  const demo = EARTH_HOLDOUT_SET[Number(exampleSelect.value)];
  if(!demo) return;
  claimEl.value = demo.claim;
  evidenceEl.value = demo.evidence;
  render(analyze(demo.claim,demo.evidence));
});

modelStatus.textContent = `Earth Evidence offline ML ready · ${EARTH_TRAINING_SET.length} Earth training pairs · ${EARTH_HOLDOUT_SET.length} untouched Earth holdout/demo pairs · no external AI API · no paid model · no CDN`;
