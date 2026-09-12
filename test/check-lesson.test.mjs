import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateLesson} from '../src/check-lesson.mjs';

const fixture = () => JSON.parse(fs.readFileSync(new URL('../examples/lesson.json', import.meta.url), 'utf8'));
test('example has linked evidence, speech and visuals', () => assert.deepEqual(validateLesson(fixture()), []));
test('rejects unsupported claims', () => {
  const lesson = fixture(); lesson.claims[0].evidenceIds = ['missing'];
  assert.ok(validateLesson(lesson).some(e => e.includes('unknown reference')));
});
test('rejects duplicate identity and missing revision', () => {
  const lesson = fixture(); lesson.evidence.push({...lesson.evidence[0], revision: ''});
  const errors = validateLesson(lesson);
  assert.ok(errors.some(e => e.includes('duplicate')));
  assert.ok(errors.some(e => e.includes('revision')));
});
test('rejects missing visual and invalid timing', () => {
  const lesson = fixture(); delete lesson.segments[0].visual; lesson.segments[0].targetSeconds = -1;
  assert.ok(validateLesson(lesson).length >= 3);
});
test('handles malformed input', () => {
  for (const value of [null, {}, {version:1, evidence:[null]}]) assert.ok(validateLesson(value).length > 0);
});
