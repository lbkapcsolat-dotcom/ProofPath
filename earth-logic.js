export function detectEarthCategory(claim,evidence){
  const t = `${claim} ${evidence}`.toLowerCase();
  if(/methane|carbon|emission|warming|climate/.test(t)) return "Climate";
  if(/solar|wind|electric|energy|efficien/.test(t)) return "Energy";
  if(/water|rain|drought|storm|flood/.test(t)) return "Water";
  if(/waste|recycl|landfill|compost|plastic/.test(t)) return "Waste";
  if(/wildlife|wetland|coral|ecosystem|biodiversity|marine/.test(t)) return "Biodiversity";
  if(/transit|traffic|bike|transport|vehicle/.test(t)) return "Transport";
  return "General";
}

export function nextEvidenceNeeded(label, category){
  const domain = category === "General" ? "environmental claim" : `${category.toLowerCase()} claim`;
  if(label === "SUPPORTED") return `Seek an independent source, measurement, or dataset that tests the same ${domain} across another place, time period, or sample.`;
  if(label === "CONTRADICTED") return `Identify the exact conflicting measurement or relationship, then verify its source, date, scale, and comparison baseline.`;
  return `Specify the missing baseline, comparison group, time window, scale, or measured outcome that would make this ${domain} testable.`;
}

export function evidenceContextCoverage(claim,evidence){
  const text = String(evidence ?? "").toLowerCase();
  const status = (field, pattern) => {
    const escaped = field.replace(/_/g,"[ _-]");
    const na = new RegExp(`\\b${escaped}\\b[^.]{0,24}\\b(?:not applicable|n\\/?a)\\b`,"i");
    if(na.test(text)) return "NOT_APPLICABLE";
    return pattern.test(text) ? "PRESENT" : "MISSING";
  };
  return {
    baseline: status("baseline",/\b(baseline|before|prior|historical|starting|initial)\b/),
    comparison: status("comparison",/\b(compared?|comparison|versus|vs\.?|control group|reference group|than)\b/),
    time_window: status("time_window",/\b(19|20)\d{2}\b|\b(day|week|month|year|hour|season|period|between|during|from)\b/),
    spatial_scale: status("spatial_scale",/\b(citywide|city|local|regional|national|global|site|district|county|state|country|watershed|km|kilometer|mile)\b/),
    measured_outcome: status("measured_outcome",/\b(measured|measurement|observed|recorded|lower|higher|increase|decrease|reduced|reduction|emission|pollution|temperature|concentration|runoff|water level|biodiversity|waste)\b|\b\d+(?:\.\d+)?\s*(?:%|ppm|ppb|mg|kg|g|mm|cm|km|m3|tons?|tonnes?)\b/),
    source_provenance: status("source_provenance",/\b(source|dataset|study|report|agency|doi|url|survey|monitoring station|satellite|publication)\b/)
  };
}
