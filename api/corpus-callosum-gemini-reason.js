import {
  buildCorpusCallosumReadOnlyBind,
  buildIndependentReasoningPrompt,
  normalizeReasoningRun
} from '../corpus-callosum-contract.mjs';

const MODEL = 'gemini-2.5-flash';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ status: 'BLOCK', message: 'POST required.' });
  if (process.env.ENABLE_CORPUS_CALLOSUM_GEMINI_READ_ONLY !== '1') {
    return res.status(503).json({ status: 'BLOCK', message: 'Corpus Callosum Gemini read-only runtime is not explicitly enabled.' });
  }
  if (!process.env.GEMINI_API_KEY) return res.status(503).json({ status: 'BLOCK', message: 'Gemini is not configured.' });

  try {
    const bind = await buildCorpusCallosumReadOnlyBind(req.body || {});
    const prompt = buildIndependentReasoningPrompt('GEMINI', bind);
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${encodeURIComponent(process.env.GEMINI_API_KEY)}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.1,
          response_mime_type: 'application/json',
          response_schema: {
            type: 'OBJECT',
            properties: {
              conclusion: { type: 'STRING' },
              reasoning: { type: 'STRING' },
              provenanceIds: { type: 'ARRAY', items: { type: 'STRING' } },
              uncertainties: { type: 'ARRAY', items: { type: 'STRING' } }
            },
            required: ['conclusion', 'reasoning', 'provenanceIds', 'uncertainties']
          }
        }
      })
    });
    if (!response.ok) return res.status(502).json({ status: 'BLOCK', message: 'Gemini read-only reasoning unavailable.' });
    const data = await response.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!text) return res.status(502).json({ status: 'BLOCK', message: 'Gemini returned no reasoning payload.' });
    let candidate;
    try { candidate = JSON.parse(text); }
    catch { return res.status(502).json({ status: 'BLOCK', message: 'Gemini returned malformed JSON.' }); }

    const run = normalizeReasoningRun({
      consumer: 'GEMINI',
      packetSha256: bind.packetSha256,
      ...candidate
    }, bind);
    return res.status(200).json({ status: 'READY', gate: bind.gate, run });
  } catch (error) {
    return res.status(400).json({ status: 'BLOCK', message: error?.message || 'Read-only bind rejected.' });
  }
}
