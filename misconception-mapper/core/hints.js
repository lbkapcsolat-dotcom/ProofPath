import { getMisconception } from './taxonomy.js';
export function buildHint(diagnosis) {
  const item = getMisconception(diagnosis?.id) ?? getMisconception('unknown');
  return item.hintTemplate.replace(/\s+/g, ' ').trim();
}
