/** Lightweight structural test for the server-side project ZIP writer. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../lib/zip.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const { createStoredZip } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const archive = createStoredZip([
  { path: 'index.html', data: '<h1>Signal Lost</h1>' },
  { path: 'assets/state.json', data: '{"ready":true}' },
]);
const view = new DataView(archive.buffer, archive.byteOffset, archive.byteLength);
assert.equal(view.getUint32(0, true), 0x04034b50, 'archive starts with a local file header');
assert.equal(view.getUint32(archive.length - 22, true), 0x06054b50, 'archive ends with central-directory footer');
assert.equal(view.getUint16(archive.length - 12, true), 2, 'archive records both files');
assert.throws(() => createStoredZip([{ path: '../secrets.txt', data: 'nope' }]), /traversal/i);
console.log(JSON.stringify({ zipBytes: archive.length, entries: 2, traversalRejected: true }));
