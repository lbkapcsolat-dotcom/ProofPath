export function mean(a){return a.reduce((s,x)=>s+x,0)/a.length}
export function median(a){const b=[...a].sort((x,y)=>x-y); const m=Math.floor(b.length/2); return b.length%2?b[m]:(b[m-1]+b[m])/2}
export function ols(xs, ys){
  const mx=mean(xs), my=mean(ys); let num=0, den=0, ssTot=0, ssRes=0;
  for(let i=0;i<xs.length;i++){num+=(xs[i]-mx)*(ys[i]-my); den+=(xs[i]-mx)**2}
  const slope=den?num/den:0, intercept=my-slope*mx;
  for(let i=0;i<xs.length;i++){const yhat=intercept+slope*xs[i]; ssTot+=(ys[i]-my)**2; ssRes+=(ys[i]-yhat)**2}
  return {slope,intercept,r2:ssTot?1-ssRes/ssTot:1};
}
export function madScores(values){
  const m=median(values), mad=median(values.map(v=>Math.abs(v-m))) || 1e-12;
  return values.map(v=>0.67448975*(v-m)/mad);
}
export function anomalies(values, threshold=2.5){return madScores(values).map((z,i)=>({i,z,flag:Math.abs(z)>=threshold})).filter(x=>x.flag)}
export function changePointCUSUM(values){
  const m=mean(values); let c=0, best=0, idx=0; const path=[];
  for(let i=0;i<values.length;i++){c+=values[i]-m; path.push(c); if(i>1&&i<values.length-2&&Math.abs(c)>Math.abs(best)){best=c;idx=i}}
  const scale=Math.sqrt(values.reduce((s,v)=>s+(v-m)**2,0)/values.length)||1;
  return {index:idx,score:Math.abs(best)/(scale*Math.sqrt(values.length)),path};
}
function mulberry32(seed){return function(){let t=seed+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
export function bootstrapSlopeCI(xs, ys, iterations=1200, seed=1337){
  const r=mulberry32(seed), slopes=[]; const n=xs.length;
  for(let k=0;k<iterations;k++){const bx=[],by=[];for(let i=0;i<n;i++){const j=Math.floor(r()*n);bx.push(xs[j]);by.push(ys[j])}slopes.push(ols(bx,by).slope)}
  slopes.sort((a,b)=>a-b); const q=p=>slopes[Math.min(slopes.length-1,Math.floor(p*(slopes.length-1)))];
  return {low:q(.025),high:q(.975),iterations};
}
export function summarize(rows, key='precip_mm'){
  const xs=rows.map(r=>r.year), ys=rows.map(r=>Number(r[key]));
  const trend=ols(xs,ys), ci=bootstrapSlopeCI(xs,ys), cps=changePointCUSUM(ys), outliers=anomalies(ys);
  return {trend,ci,changePoint:cps,anomalies:outliers,values:ys,years:xs};
}
