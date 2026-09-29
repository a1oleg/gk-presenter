import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {validateLesson} from './check-lesson.mjs';

const hash = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const color = value => typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value);
const number = value => Number.isFinite(value);
const unit = value => number(value) && value >= 0 && value <= 1;
const plain = value => value && typeof value === 'object' && !Array.isArray(value);
function fail(message) { throw Error(message); }

// Compile the existing editorial contract into a portable execution plan.
// No spreadsheet, topic, speech provider or renderer-specific widget is required.
export function compileProduction(lesson, baseDirectory) {
  const errors = validateLesson(lesson);
  if(errors.length) fail(errors.join('\n'));
  const p = lesson.production;
  if(!plain(p) || p.version !== 1) fail('production.version must be 1');
  const {width,height,fps} = p.canvas || {};
  if(![width,height].every(n => Number.isInteger(n) && n >= 64 && n <= 3840 && n % 2 === 0)) fail('canvas dimensions must be even integers, 64..3840');
  if(!Number.isInteger(fps) || fps < 1 || fps > 60) fail('canvas.fps must be 1..60');
  if(!color(p.background)) fail('production.background must be #RRGGBB');
  const assets = new Map();
  function asset(value,label) {
    if(typeof value !== 'string' || !value.trim()) fail(`${label}: local file required`);
    const file = fs.realpathSync(path.resolve(baseDirectory,value));
    if(!fs.statSync(file).isFile()) fail(`${label}: not a file`);
    const entry={path:file,sha256:hash(file)};
    assets.set(file,entry); return entry;
  }
  const font = asset(p.font,'production.font');
  const ids = new Set();
  const scenes = lesson.segments.map(segment => {
    if(!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(segment.id)) fail('segment id must be a safe filename, at most 64 characters');
    if(ids.has(segment.id)) fail('Duplicate scene id'); ids.add(segment.id);
    const r=segment.render;
    if(!plain(r)) fail(`${segment.id}: render is required`);
    if(!['silent','file'].includes(r.audio?.mode)) fail(`${segment.id}: explicit audio mode silent or file required`);
    const audio = r.audio.mode === 'file' ? {...asset(r.audio.file,'audio'),mode:'file'} : {mode:'silent'};
    if(audio.mode==='silent' && (!number(r.durationSeconds) || r.durationSeconds<=0 || r.durationSeconds>3600)) fail('Silent scenes need durationSeconds in (0,3600]');
    if(audio.mode==='file' && r.durationSeconds!==undefined) fail('Audio scenes derive duration from audio; omit durationSeconds');
    const tailSeconds = r.tailSeconds ?? 0.3;
    if(!number(tailSeconds) || tailSeconds<0 || tailSeconds>10) fail('tailSeconds must be 0..10');
    if(!plain(r.background) || !['solid','image'].includes(r.background.kind)) fail('background.kind must be solid or image');
    const background = r.background.kind==='image' ? {kind:'image',asset:asset(r.background.file,'background')} : {kind:'solid'};
    if(!Array.isArray(r.overlays)) fail('render.overlays must be an array');
    let alignment;
    function timing(value) {
      if(number(value) && value>=0) return value;
      if(!plain(value) || typeof value.anchor!=='string' || !value.anchor.length) fail('Timing requires nonnegative seconds or {anchor, occurrence?}');
      if(audio.mode!=='file' || !r.audio.alignment) fail('Anchor timing needs audio and alignment file');
      if(!alignment) {
        const input = asset(r.audio.alignment,'alignment');
        const data = JSON.parse(fs.readFileSync(input.path,'utf8').replace(/^\uFEFF/,''));
        alignment=data.alignment || data;
        if(!Array.isArray(alignment.characters) || !Array.isArray(alignment.character_start_times_seconds) || alignment.characters.length!==alignment.character_start_times_seconds.length) fail('Invalid character alignment');
        if(!alignment.characters.every(c=>typeof c==='string' && c.length===1)) fail('Alignment characters must be single UTF-16 characters');
        if(!alignment.character_start_times_seconds.every((t,i,a)=>number(t)&&t>=0&&(i===0||t>=a[i-1]))) fail('Alignment times must be nonnegative and ordered');
        if(alignment.characters.join('')!==segment.narration) fail('Alignment text differs from narration');
      }
      const text=alignment.characters.join(''); const matches=[];
      for(let i=text.indexOf(value.anchor);i>=0;i=text.indexOf(value.anchor,i+1)) matches.push(i);
      const occurrence=value.occurrence ?? 1;
      if(!Number.isInteger(occurrence)||occurrence<1||occurrence>matches.length) fail('Anchor occurrence not found');
      if(matches.length>1 && value.occurrence===undefined) fail('Repeated anchor needs explicit occurrence');
      return alignment.character_start_times_seconds[matches[occurrence-1]];
    }
    const overlays = r.overlays.map(o => {
      if(!plain(o) || !['text','pointer'].includes(o.kind)) fail('overlay.kind must be text or pointer');
      if(!unit(o.x)||!unit(o.y)) fail('Overlay coordinates must be 0..1');
      if(!color(o.color)) fail('Overlay color must be #RRGGBB');
      const start=timing(o.start ?? 0),end=o.end===undefined?null:timing(o.end);
      if(end!==null && end<=start) fail('Overlay end must follow start');
      if(o.kind==='text') {
        if(typeof o.text!=='string'||!o.text.trim()) fail('Overlay text is required');
        if(!Number.isInteger(o.size)||o.size<8||o.size>200) fail('Text size must be 8..200 pixels');
        return {kind:'text',text:o.text,size:o.size,x:o.x,y:o.y,color:o.color,start,end};
      }
      if(!Number.isInteger(o.size)||o.size<4||o.size>100) fail('Pointer size must be 4..100 pixels');
      return {kind:'pointer',size:o.size,x:o.x,y:o.y,color:o.color,start,end};
    });
    return {id:segment.id,narration:segment.narration,claimIds:segment.claimIds,background,audio,overlays,
      durationSeconds:r.durationSeconds ?? null,tailSeconds};
  });
  return {version:1,title:lesson.title,canvas:{width,height,fps},background:p.background,font,scenes,assets:[...assets.values()]};
}
