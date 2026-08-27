import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const forbidden = [
  'fetch(',
  'XMLHttpRequest',
  'axios',
  'openai',
  'anthropic',
  'gemini',
  'supabase',
  'firebase'
];

test('core runtime has no required network or paid-provider dependency', async () => {
  const files = [
    'core/taxonomy.js',
    'core/features.js',
    'core/rank.js',
    'core/diagnosis.js',
    'core/hints.js',
    'core/retry.js',
    'core/session.js',
    'core/modelAdapter.js',
    'core/analyze.js'
  ];

  for (const file of files) {
    const text = await readFile(new URL(`../${file}`, import.meta.url), 'utf8');
    for (const needle of forbidden) {
      assert.equal(text.toLowerCase().includes(needle.toLowerCase()), false, `${file} contains ${needle}`);
    }
  }
});
