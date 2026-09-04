import { buildGeminiPrompt, lockAuthoritativeVerdict } from '../gemini-contract.js';

const MODEL = 'gemini-2.5-flash';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ status: 'BLOCK', message: 'POST required.' });
  if (!process.env.GEMINI_API_KEY) return res.status(503).json({ status: 'BLOCK', message: 'Gemini is not configured.' });

  const { claim = '', evidence = '', authoritative } = req.body || {};
  if (!claim.trim() || !evidence.trim() || !authoritative || authoritative.status !== 'READY') {
    return res.status(400).json({ status: 'BLOCK', message: 'Claim, evidence, and an authoritative classifier result are required.' });
  }

  const prompt = buildGeminiPrompt({ claim, evidence, authoritative });
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${encodeURIComponent(process.env.GEMINI_API_KEY)}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.2,
          response_mime_type: 'application/json',
          response_schema: {
            type: 'OBJECT',
            properties: {
              explanation: { type: 'STRING' },
              nextEvidenceStep: { type: 'STRING' }
            },
            required: ['explanation', 'nextEvidenceStep']
          }
        }
      })
    });

    if (!response.ok) return res.status(502).json({ status: 'BLOCK', message: 'Gemini explanation unavailable.' });
    const data = await response.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!text) return res.status(502).json({ status: 'BLOCK', message: 'Gemini returned no explanation.' });

    let candidate;
    try { candidate = JSON.parse(text); }
    catch { return res.status(502).json({ status: 'BLOCK', message: 'Gemini returned an invalid explanation format.' }); }

    return res.status(200).json(lockAuthoritativeVerdict(authoritative, candidate));
  } catch {
    return res.status(502).json({ status: 'BLOCK', message: 'Gemini explanation unavailable.' });
  }
}
