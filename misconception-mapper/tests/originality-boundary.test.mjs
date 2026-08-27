import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

async function walk(dir) {
  const out=[];
  for (const e of await readdir(dir,{withFileTypes:true})) {
    const p=new URL(`../${dir}/${e.name}`, import.meta.url);
    if (e.isDirectory()) out.push(...await walk(`${dir}/${e.name}`));
    else out.push(p);
  }
  return out;
}

test('runtime source does not import existing ProofPath root modules', async () => {
  const files = [new URL('../app.js', import.meta.url), ...(await walk('core'))];
  for (const file of files) {
    const text=(await readFile(file,'utf8')).toLowerCase();
    assert.equal(text.includes("../model.js"), false);
    assert.equal(text.includes("../app.js"), false);
    assert.equal(text.includes("../tests.mjs"), false);
    assert.equal(text.includes('proofpath'), false);
  }
});

test('package declares no runtime or development dependencies', async () => {
  const pkg=JSON.parse(await readFile(new URL('../package.json', import.meta.url),'utf8'));
  assert.equal(pkg.dependencies, undefined);
  assert.equal(pkg.devDependencies, undefined);
});
