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
