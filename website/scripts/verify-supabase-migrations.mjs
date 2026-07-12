import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(process.cwd(), 'supabase', 'migrations');
const files = (await readdir(root)).filter((file) => file.endsWith('.sql')).sort();
const seen = new Set();
for (const file of files) {
  if (!/^\d{12,14}_[a-z0-9_]+\.sql$/i.test(file)) throw new Error(`Invalid migration filename: ${file}`);
  const version = file.split('_', 1)[0];
  if (seen.has(version)) throw new Error(`Duplicate migration version: ${version}`);
  seen.add(version);
  const sql = await readFile(path.join(root, file), 'utf8');
  if (!sql.trim()) throw new Error(`Empty migration: ${file}`);
  if (/\bdrop\s+(database|schema)\b/i.test(sql)) throw new Error(`Destructive schema operation blocked: ${file}`);
  if (/\bcreate\s+table\b/i.test(sql) && !/enable\s+row\s+level\s+security/i.test(sql)) {
    throw new Error(`New tables must explicitly enable RLS: ${file}`);
  }
}
console.log(JSON.stringify({ migrations: files.length, verified: true }));
