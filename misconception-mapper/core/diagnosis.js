import { getMisconception } from './taxonomy.js';
export function selectDiagnosis(candidates) {
  const top = candidates?.[0];
  const second = candidates?.[1];
  if (!top || top.id === 'unknown' || top.score < 0.6) {
    return { status:'uncertain', id:'unknown', label:'Need more context', confidenceText:'Uncertain — need more context', why:'The current answer does not match a bounded pattern confidently.' };
  }
  if (second && top.score - second.score < 0.08) {
    return { status:'uncertain', id:'unknown', label:'Need more context', confidenceText:'Uncertain — two patterns are similarly plausible', why:'One additional intermediate step would help distinguish the patterns.' };
  }
  const item = getMisconception(top.id);
  return { status:'likely', id:top.id, label:item.label, confidenceText:`Likely pattern (${Math.round(top.score * 100)}% bounded score ceiling)`, why:top.evidence[0] ?? 'The submitted steps match this bounded pattern.' };
}
