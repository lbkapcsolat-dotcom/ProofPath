
export const LABELS = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"];

const STOP = new Set([
  "the","a","an","is","are","was","were","be","been","being","to","of","and","or",
  "in","on","at","for","with","by","from","that","this","it","as","into","than"
]);
const NEG = new Set(["not","no","never","none","without","cannot","can't","isn't","aren't","wasn't","weren't"]);
const ANTONYM_PAIRS = [
  ["increase","decrease"],["higher","lower"],["hot","cold"],["true","false"],
  ["supports","contradicts"],["alive","dead"],["open","closed"],["more","less"],
  ["before","after"],["always","never"],["possible","impossible"]
];

export function tokenize(text) {
  return String(text ?? "").toLowerCase().replace(/[^a-z0-9.%'-]+/g," ").trim().split(/\s+/).filter(Boolean);
}
function stemToken(t) {
  if (t.length > 4 && t.endsWith("ies")) return t.slice(0,-3)+"y";
  if (t.length > 4 && t.endsWith("es")) return t.slice(0,-2);
  if (t.length > 3 && t.endsWith("s") && !t.endsWith("ss")) return t.slice(0,-1);
  return t;
}
function contentTokens(text) { return tokenize(text).filter(t=>!STOP.has(t)).map(stemToken); }
function safeDiv(a,b){ return b ? a/b : 0; }
function hasNegation(tokens){ return tokens.some(t=>NEG.has(t)); }
function numericTokens(tokens){ return tokens.filter(t=>/^[0-9]+(?:\.[0-9]+)?%?$/.test(t)); }
function antonymConflict(c,e){
  const cs=new Set(c), es=new Set(e); let hits=0;
  for(const [x,y] of ANTONYM_PAIRS){
    if((cs.has(x)&&es.has(y))||(cs.has(y)&&es.has(x))) hits++;
  }
  return hits;
}

export function extractFeatures(claim,evidence){
  const c=contentTokens(claim), e=contentTokens(evidence);
  const cs=new Set(c), es=new Set(e);
  const inter=[...cs].filter(x=>es.has(x)).length;
  const union=new Set([...cs,...es]).size;
  const cNums=numericTokens(c), eNums=numericTokens(e);
  const numberMismatch=(cNums.length&&eNums.length&&cNums.join("|")!==eNums.join("|"))?1:0;
  const negMismatch=hasNegation(c)!==hasNegation(e)?1:0;
  const antonym=Math.min(1,antonymConflict(c,e));
  const exact=(evidence.toLowerCase().includes(claim.toLowerCase().trim())&&claim.trim())?1:0;
  const contradictionCue=/\b(not|never|false|incorrect|contradicts?|instead|whereas|however)\b/i.test(evidence)?1:0;
  const uncertaintyCue=/\b(may|might|could|uncertain|unknown|insufficient|suggests?|possible|possibly)\b/i.test(evidence)?1:0;
  const overclaimCue=/\b(always|guarantees?|guaranteed|definitely|perfect|completely|every|proves?|certain|expert)\b/i.test(claim)?1:0;
  return [
    1,
    safeDiv(inter,union),
    safeDiv(inter,cs.size),
    safeDiv(inter,es.size),
    negMismatch,
    numberMismatch,
    antonym,
    exact,
    contradictionCue,
    uncertaintyCue,
    overclaimCue,
    Math.min(1,safeDiv(e.length,Math.max(1,c.length))),
  ];
}
function zeros(r,c){ return Array.from({length:r},()=>Array(c).fill(0)); }
function softmax(logits){
  const m=Math.max(...logits), exps=logits.map(x=>Math.exp(x-m)), s=exps.reduce((a,b)=>a+b,0);
  return exps.map(x=>x/s);
}
function dot(a,b){ let s=0; for(let i=0;i<a.length;i++) s+=a[i]*b[i]; return s; }

export function trainSoftmax(examples,{epochs=1800,lr=0.08,l2=0.0005}={}){
  const f=extractFeatures(examples[0].claim,examples[0].evidence).length;
  const W=zeros(LABELS.length,f);
  for(let epoch=0;epoch<epochs;epoch++){
    const grad=zeros(LABELS.length,f);
    for(const ex of examples){
      const x=extractFeatures(ex.claim,ex.evidence);
      const y=LABELS.indexOf(ex.label);
      const probs=softmax(W.map(row=>dot(row,x)));
      for(let k=0;k<LABELS.length;k++){
        const err=probs[k]-(k===y?1:0);
        for(let j=0;j<f;j++) grad[k][j]+=err*x[j]+l2*W[k][j];
      }
    }
    for(let k=0;k<LABELS.length;k++) for(let j=0;j<f;j++) W[k][j]-=lr*grad[k][j]/examples.length;
  }
  return W;
}

export function predict(model,claim,evidence){
  if(!claim.trim()||!evidence.trim()){
    return {label:"INSUFFICIENT",probabilities:{SUPPORTED:0,CONTRADICTED:0,INSUFFICIENT:1},claim_ceiling:"EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY"};
  }
  const x=extractFeatures(claim,evidence);
  const probs=softmax(model.map(row=>dot(row,x)));
  const best=probs.indexOf(Math.max(...probs));
  return {
    label:LABELS[best],
    probabilities:Object.fromEntries(LABELS.map((l,i)=>[l,probs[i]])),
    features:x,
    claim_ceiling:"EDUCATIONAL_EVIDENCE_ASSESSMENT_ONLY",
  };
}

export const TRAINING_SET = [
  {claim:"Paris is the capital of France.",evidence:"Paris is the capital city of France.",label:"SUPPORTED"},
  {claim:"Water freezes at 0 C.",evidence:"At standard pressure, water freezes at 0 C.",label:"SUPPORTED"},
  {claim:"The Earth revolves around the Sun.",evidence:"Astronomical observations show the Earth revolves around the Sun.",label:"SUPPORTED"},
  {claim:"Vitamin C is found in oranges.",evidence:"Oranges contain vitamin C.",label:"SUPPORTED"},
  {claim:"A triangle has three sides.",evidence:"A triangle is a polygon with three sides.",label:"SUPPORTED"},
  {claim:"The Pacific is an ocean.",evidence:"The Pacific Ocean is the world's largest ocean.",label:"SUPPORTED"},
  {claim:"Plants need light for photosynthesis.",evidence:"Photosynthesis in plants uses light energy.",label:"SUPPORTED"},
  {claim:"Sound travels through air.",evidence:"Sound waves can travel through air.",label:"SUPPORTED"},
  {claim:"Iron is a metal.",evidence:"Iron is classified as a metal.",label:"SUPPORTED"},
  {claim:"The Moon orbits Earth.",evidence:"The Moon travels in an orbit around Earth.",label:"SUPPORTED"},
  {claim:"Boiling water is hot.",evidence:"Boiling water has a high temperature and is hot.",label:"SUPPORTED"},
  {claim:"Ten is more than five.",evidence:"10 is more than 5.",label:"SUPPORTED"},
  {claim:"Closed doors are not open.",evidence:"A closed door is not open.",label:"SUPPORTED"},
  {claim:"Ice is cold.",evidence:"Ice has a low temperature and is cold.",label:"SUPPORTED"},
  {claim:"Birds have feathers.",evidence:"Feathers cover the bodies of birds.",label:"SUPPORTED"},
  {claim:"Gravity pulls objects toward Earth.",evidence:"Objects are pulled toward Earth by gravity.",label:"SUPPORTED"},
  {claim:"Leaves can use sunlight.",evidence:"Sunlight provides energy used by leaves.",label:"SUPPORTED"},
  {claim:"Mammals breathe air.",evidence:"Air is breathed by mammals.",label:"SUPPORTED"},
  {claim:"A year contains months.",evidence:"Months are divisions of a year.",label:"SUPPORTED"},
  {claim:"Light is used by plants.",evidence:"Plants use energy from light.",label:"SUPPORTED"},
  {claim:"Seven is greater than three.",evidence:"3 is less than 7.",label:"SUPPORTED"},
  {claim:"Cold objects have low temperature.",evidence:"A low temperature means an object is cold.",label:"SUPPORTED"},

  {claim:"Paris is the capital of Germany.",evidence:"Paris is the capital of France, not Germany.",label:"CONTRADICTED"},
  {claim:"Water freezes at 20 C.",evidence:"Water freezes at 0 C, not 20 C.",label:"CONTRADICTED"},
  {claim:"The Earth is larger than the Sun.",evidence:"The Sun is much larger than Earth.",label:"CONTRADICTED"},
  {claim:"A triangle has four sides.",evidence:"A triangle has three sides, not four.",label:"CONTRADICTED"},
  {claim:"The Moon orbits Mars.",evidence:"The Moon orbits Earth, not Mars.",label:"CONTRADICTED"},
  {claim:"Ice is hot.",evidence:"Ice is cold, not hot.",label:"CONTRADICTED"},
  {claim:"Ten is less than five.",evidence:"10 is more than 5.",label:"CONTRADICTED"},
  {claim:"The door is open.",evidence:"The door is closed, not open.",label:"CONTRADICTED"},
  {claim:"Plants never use light.",evidence:"Plants use light energy for photosynthesis.",label:"CONTRADICTED"},
  {claim:"Iron is not a metal.",evidence:"Iron is a metal.",label:"CONTRADICTED"},
  {claim:"Boiling water is cold.",evidence:"Boiling water is hot.",label:"CONTRADICTED"},
  {claim:"The Pacific is not an ocean.",evidence:"The Pacific is an ocean.",label:"CONTRADICTED"},

  {claim:"Carrots give perfect night vision.",evidence:"Carrots contain vitamin A.",label:"INSUFFICIENT"},
  {claim:"This medicine cures every disease.",evidence:"The medicine reduced one symptom in a small study.",label:"INSUFFICIENT"},
  {claim:"Aliens visited Earth yesterday.",evidence:"A bright light was seen in the sky.",label:"INSUFFICIENT"},
  {claim:"The student will become a scientist.",evidence:"The student enjoys science class.",label:"INSUFFICIENT"},
  {claim:"The new app is the best in the world.",evidence:"Ten users said they liked the app.",label:"INSUFFICIENT"},
  {claim:"Exercise always guarantees happiness.",evidence:"Exercise may improve mood.",label:"INSUFFICIENT"},
  {claim:"This plant will live for 100 years.",evidence:"The plant is healthy today.",label:"INSUFFICIENT"},
  {claim:"The company will double revenue.",evidence:"Revenue increased last month.",label:"INSUFFICIENT"},
  {claim:"The storm will arrive at exactly noon.",evidence:"Forecasts suggest a storm may arrive tomorrow.",label:"INSUFFICIENT"},
  {claim:"The treatment is completely safe.",evidence:"No serious issue was observed in five people.",label:"INSUFFICIENT"},
  {claim:"The book proves the theory.",evidence:"The book discusses the theory.",label:"INSUFFICIENT"},
  {claim:"The team will definitely win.",evidence:"The team won its previous game.",label:"INSUFFICIENT"},
];

export const HOLDOUT_SET = [
  {claim:"Earth's natural satellite is the Moon.",evidence:"The Moon is Earth's natural satellite.",label:"SUPPORTED"},
  {claim:"A square has three sides.",evidence:"A square has four sides, not three.",label:"CONTRADICTED"},
  {claim:"Coffee guarantees perfect concentration.",evidence:"Coffee may improve alertness for some people.",label:"INSUFFICIENT"},
  {claim:"Five is less than ten.",evidence:"5 is less than 10.",label:"SUPPORTED"},
  {claim:"The Arctic is hot.",evidence:"The Arctic is cold, not hot.",label:"CONTRADICTED"},
  {claim:"Reading one article makes someone an expert.",evidence:"Reading can provide information about a topic.",label:"INSUFFICIENT"},
  {claim:"A closed shop is open.",evidence:"The shop is closed, not open.",label:"CONTRADICTED"},
  {claim:"Photosynthesis uses light.",evidence:"Plants use light energy during photosynthesis.",label:"SUPPORTED"},
  {claim:"Rain tomorrow is certain.",evidence:"Rain may occur tomorrow.",label:"INSUFFICIENT"},
  {claim:"Iron is a metal.",evidence:"Iron is classified as a metal.",label:"SUPPORTED"},
];
