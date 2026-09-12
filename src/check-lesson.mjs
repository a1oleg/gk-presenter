import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export function validateLesson(lesson) {
  const errors = [];
  if (!lesson || typeof lesson !== 'object') return ['Expected a lesson object'];
  if (lesson.version !== 1) errors.push('version must be 1');
  const text = value => typeof value === 'string' && value.trim().length > 0;
  if (!text(lesson.title)) errors.push('title is required');
  const index = (name) => {
    const rows = lesson[name];
    if (!Array.isArray(rows) || !rows.length) { errors.push(`${name} must be a nonempty array`); return new Map(); }
    const map = new Map();
    for (const row of rows) {
      if (!text(row?.id)) { errors.push(`${name}: missing id`); continue; }
      if (map.has(row.id)) errors.push(`${name}: duplicate id ${row.id}`);
      map.set(row.id, row);
    }
    return map;
  };
  const evidence = index('evidence');
  const claims = index('claims');
  const segments = index('segments');
  const references = (ids, target, label) => {
    if (!Array.isArray(ids) || !ids.length) { errors.push(`${label}: references required`); return; }
    for (const id of ids) if (!target.has(id)) errors.push(`${label}: unknown reference ${id}`);
  };
  for (const [id, item] of evidence) {
    if (!['code', 'graph', 'annotation', 'transcript', 'visual'].includes(item.kind)) errors.push(`${id}: invalid evidence kind`);
    if (!text(item.locator)) errors.push(`${id}: locator required`);
    if (!text(item.revision)) errors.push(`${id}: source revision required`);
  }
  for (const [id, claim] of claims) {
    if (!text(claim.text)) errors.push(`${id}: claim text required`);
    references(claim.evidenceIds, evidence, id);
  }
  for (const [id, segment] of segments) {
    if (!text(segment.narration)) errors.push(`${id}: narration required`);
    if (!(Number.isFinite(segment.targetSeconds) && segment.targetSeconds > 0)) errors.push(`${id}: positive targetSeconds required`);
    references(segment.claimIds, claims, id);
    if (!['code', 'diagram', 'screen', 'title'].includes(segment.visual?.kind)) errors.push(`${id}: invalid visual kind`);
    if (!text(segment.visual?.instruction)) errors.push(`${id}: visual instruction required`);
    references(segment.visual?.evidenceIds, evidence, `${id}.visual`);
  }
  return errors;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    if (!process.argv[2]) throw new Error('Usage: node src/check-lesson.mjs lesson.json');
    const errors = validateLesson(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')));
    console.log(JSON.stringify({ok: errors.length === 0, errors}, null, 2));
    process.exitCode = errors.length ? 1 : 0;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
