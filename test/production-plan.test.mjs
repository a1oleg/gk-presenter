import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {compileProduction} from '../src/production-plan.mjs';

function fixture(t) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'presenter-plan-test-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  fs.writeFileSync(path.join(dir,'asset'),'fixture');
  const lesson=JSON.parse(fs.readFileSync(new URL('../examples/production/fisher.json',import.meta.url),'utf8'));
  lesson.production.font='asset';
  return {dir,lesson};
}
test('compiler preserves evidence links, order, canvas and parameterized overlays',t=>{
  const {dir,lesson}=fixture(t); const plan=compileProduction(lesson,dir);
  assert.deepEqual(plan.scenes.map(s=>s.id),lesson.segments.map(s=>s.id));
  assert.deepEqual(plan.scenes[0].claimIds,lesson.segments[0].claimIds);
  assert.equal(plan.canvas.fps,24);
  assert.equal(plan.assets[0].sha256.length,64);
});
test('unsafe IDs, missing explicit audio mode and invalid dimensions are rejected',t=>{
  const {dir,lesson}=fixture(t);
  for(const edit of [l=>l.segments[0].id='../escape',l=>delete l.segments[0].render.audio,l=>l.production.canvas.width=321]) {
    const copy=structuredClone(lesson);edit(copy);assert.throws(()=>compileProduction(copy,dir));
  }
});
test('repeated speech anchors require an occurrence and stale alignment is rejected',t=>{
  const {dir,lesson}=fixture(t); const s=lesson.segments[0];
  s.narration='go go';s.render.audio={mode:'file',file:'asset',alignment:'alignment.json'};delete s.render.durationSeconds;
  fs.writeFileSync(path.join(dir,'alignment.json'),JSON.stringify({characters:[...'go go'],character_start_times_seconds:[0,.1,.2,.3,.4]}));
  s.render.overlays[0].start={anchor:'go'};
  assert.throws(()=>compileProduction(lesson,dir),/Repeated anchor/);
  s.render.overlays[0].start={anchor:'go',occurrence:2};
  assert.equal(compileProduction(lesson,dir).scenes[0].overlays[0].start,.3);
  s.narration='changed';assert.throws(()=>compileProduction(lesson,dir),/differs from narration/);
});
test('render cannot bypass editorial evidence validation',t=>{
  const {dir,lesson}=fixture(t);lesson.segments[0].claimIds=['missing'];
  assert.throws(()=>compileProduction(lesson,dir),/unknown reference/);
});
