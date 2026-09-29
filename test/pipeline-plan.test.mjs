import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveCues} from '../src/pipeline-plan.mjs';
import {selectSourceLines} from '../src/semantic-snapshot.mjs';
test('source selection preserves CRLF offsets, blank lines and line numbers',()=>{
  const source='first\r\n\r\nthird\r\nfourth';
  const colors=Array.from(source,(_,i)=>String(i));
  const result=selectSourceLines(source,colors,[[2,3]]);
  assert.equal(result.code,'\nthird');assert.deepEqual(result.lineMap,[2,3]);
  assert.deepEqual(result.colors,['#D4D4D4','9','10','11','12','13']);
});
test('unordered and out-of-bounds source ranges are rejected',()=>{
  for(const ranges of [[[0,1]],[[1,3]],[[2,2],[1,1]],[[1,2],[2,2]]])assert.throws(()=>selectSourceLines('a\nb',['x','x','x'],ranges));
});
test('cue anchor resolves an explicit repeated occurrence',()=>{
  const a={characters:[...'go go'],character_start_times_seconds:[0,.1,.2,.3,.4]};
  const cue={anchor:'go',occurrence:2,diagramCell:'n1',codeLine:3};
  assert.equal(resolveCues([cue],a,1)[0].time,.3);
  delete cue.occurrence;assert.throws(()=>resolveCues([cue],a,1),/Repeated anchor/);
});
test('timeline rejects conflicting, reversed and out-of-range cues',()=>{
  const cue={diagramCell:'n1',codeLine:3};
  assert.throws(()=>resolveCues([{...cue,time:0,anchor:'go'}],null,1));
  assert.throws(()=>resolveCues([{...cue,time:1}],null,1));
  assert.throws(()=>resolveCues([{...cue,time:.5},{...cue,time:.2}],null,1));
});
