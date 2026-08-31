import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('./api/corpus-callosum-gemini-reason.js', import.meta.url), 'utf8');

assert.match(source, /const MODEL = 'gemini-3\.7-flash'/, 'runtime must target the same Gemini 3.7 Flash model as the preflight');
assert.doesNotMatch(source, /\btemperature\s*:/, 'Gemini 3.7 runtime must not send deprecated temperature sampling');
assert.match(source, /'x-goog-api-key'\s*:\s*process\.env\.GEMINI_API_KEY/, 'API key must be sent server-side in the auth header');
assert.doesNotMatch(source, /\?key=/, 'API key must not be placed in the request URL');
assert.match(source, /responseMimeType\s*:\s*'application\/json'/, 'runtime must request JSON output');
assert.match(source, /responseSchema\s*:/, 'runtime must constrain structured output');

console.log('PASS Gemini 3.7 runtime contract');
