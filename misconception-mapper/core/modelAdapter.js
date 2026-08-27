export async function rerankWithOptionalModel(ranked, { enabled = false, adapter = null } = {}) {
  if (!enabled || typeof adapter !== 'function') return ranked;
  try {
    const result = await adapter(ranked);
    if (!Array.isArray(result) || result.length === 0) return ranked;
    return result;
  } catch {
    return ranked;
  }
}
