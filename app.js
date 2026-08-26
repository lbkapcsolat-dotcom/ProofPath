import {summarize} from './analytics.js';
let dataset=null, metric='precip_mm';
const $=s=>document.querySelector(s);
function fmt(n,d=2){return Number(n).toFixed(d)}
function labelMetric(){return metric==='precip_mm'?'Annual precipitation (mm)':'SPI-12 (standardized)'}
function render(){
  const rows=dataset.rows, a=summarize(rows,metric), cp=rows[a.changePoint.index];
  $('#metricName').textContent=labelMetric();
  $('#trend').textContent=`${a.trend.slope>=0?'+':''}${fmt(a.trend.slope,metric==='spi'?3:1)} / year`;
  $('#trendMeta').textContent=`95% bootstrap CI ${fmt(a.ci.low,metric==='spi'?3:1)} to ${fmt(a.ci.high,metric==='spi'?3:1)} · R² ${fmt(a.trend.r2,2)}`;
  $('#cp').textContent=cp?String(cp.year):'—';
  $('#cpMeta').textContent=`CUSUM candidate · normalized score ${fmt(a.changePoint.score,2)}`;
  $('#anom').textContent=String(a.anomalies.length);
  $('#anomMeta').textContent=a.anomalies.length? a.anomalies.map(x=>`${rows[x.i].year} (${fmt(x.z,1)} MAD-z)`).join(', '):'No robust outliers at |z| ≥ 2.5';
  const uncertain=!(a.ci.low>0||a.ci.high<0);
  $('#uncertainty').textContent=uncertain?'Trend uncertain':'Directional signal';
  $('#uncertaintyMeta').textContent=uncertain?'Slope interval includes zero. Treat direction as unresolved.':'Slope interval excludes zero in this sample.';
  draw(rows,a);
  $('#tableBody').innerHTML=rows.map((r,i)=>`<tr><td>${r.year}</td><td>${fmt(r.precip_mm,2)}</td><td>${fmt(r.spi,3)}</td><td>${r.category}</td><td>${a.anomalies.some(x=>x.i===i)?'Outlier':''}${a.changePoint.index===i?' Change-point':''}</td></tr>`).join('');
}
function draw(rows,a){
  const c=$('#chart'), ctx=c.getContext('2d'); const dpr=window.devicePixelRatio||1; const rect=c.getBoundingClientRect();
  c.width=rect.width*dpr;c.height=380*dpr;ctx.scale(dpr,dpr); const W=rect.width,H=380,p={l:54,r:18,t:20,b:44};
  ctx.clearRect(0,0,W,H); const ys=a.values, ymin=Math.min(...ys), ymax=Math.max(...ys), pad=(ymax-ymin||1)*.12;
  const x=i=>p.l+i*(W-p.l-p.r)/(rows.length-1), y=v=>p.t+(ymax+pad-v)*(H-p.t-p.b)/(ymax-ymin+2*pad);
  ctx.font='12px system-ui';ctx.fillStyle='#64748b';ctx.strokeStyle='#e2e8f0';ctx.lineWidth=1;
  for(let k=0;k<5;k++){const v=ymin-pad+k*(ymax-ymin+2*pad)/4, yy=y(v);ctx.beginPath();ctx.moveTo(p.l,yy);ctx.lineTo(W-p.r,yy);ctx.stroke();ctx.fillText(fmt(v,metric==='spi'?2:0),6,yy+4)}
  ctx.strokeStyle='#0f766e';ctx.lineWidth=2.5;ctx.beginPath();rows.forEach((r,i)=>{const yy=y(a.values[i]);i?ctx.lineTo(x(i),yy):ctx.moveTo(x(i),yy)});ctx.stroke();
  const an=new Set(a.anomalies.map(z=>z.i)); rows.forEach((r,i)=>{ctx.beginPath();ctx.arc(x(i),y(a.values[i]),an.has(i)?5:3,0,Math.PI*2);ctx.fillStyle=an.has(i)?'#b91c1c':'#0f766e';ctx.fill()});
  const cp=a.changePoint.index;ctx.strokeStyle='#7c3aed';ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(x(cp),p.t);ctx.lineTo(x(cp),H-p.b);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#475569';[0,4,9,14,19,24].filter(i=>i<rows.length).forEach(i=>ctx.fillText(rows[i].year,x(i)-14,H-18));
}
async function loadDefault(){dataset=await (await fetch('./data/budapest_nasa_power_2000_2024.json')).json(); render()}
$('#metric').addEventListener('change',e=>{metric=e.target.value;render()});
$('#csv').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;const t=await f.text();const lines=t.trim().split(/\r?\n/), head=lines.shift().split(',').map(x=>x.trim());const yi=head.indexOf('year'), vi=head.indexOf('value');if(yi<0||vi<0){alert('CSV schema: year,value');return}const rows=lines.map(l=>l.split(',')).map(a=>({year:Number(a[yi]),precip_mm:Number(a[vi]),spi:Number(a[vi]),category:'Imported'})).filter(r=>Number.isFinite(r.year)&&Number.isFinite(r.precip_mm));if(rows.length<8){alert('Need at least 8 valid rows.');return}dataset={...dataset,dataset:'User CSV',rows};metric='precip_mm';$('#metric').value='precip_mm';render()});
window.addEventListener('resize',()=>dataset&&render());
loadDefault();
