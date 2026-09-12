import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const allowed = new Set(['.env.example']);
const extensions = new Set(['.js', '.mjs', '.json', '.md', '.yml', '.yaml']);
const findings = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'android' || entry.name === 'dist') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (extensions.has(path.extname(entry.name)) || entry.name.startsWith('.env')) inspect(full);
  }
}

function inspect(file) {
  const rel = path.relative(root, file);
  if (allowed.has(rel)) return;
  const text = fs.readFileSync(file, 'utf8');
  if (/EXPO_PUBLIC_REVENUECAT_TEST_API_KEY\s*=\s*[^\s]+/.test(text)) findings.push(`${rel}: hard-coded RevenueCat Test Store key assignment`);
  if (/['\"](?:test|rcb|goog|appl)_[A-Za-z0-9_-]{20,}['\"]/.test(text)) findings.push(`${rel}: possible RevenueCat API key literal`);
}

walk(root);
if (findings.length) {
  console.error(findings.join('\n'));
  process.exit(1);
}
console.log('PASS_NO_REVENUECAT_SECRET_COMMITTED');
