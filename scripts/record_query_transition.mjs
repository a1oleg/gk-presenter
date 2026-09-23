import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';
const out=path.resolve(process.argv[2]);
const rowNumber=Number(process.argv[3]||37);
const read=async n=>JSON.parse(await fs.readFile(path.join(out,n),'utf8'));
const row=(await read('sheet-source.json')).values[0];
const diagramOnly=rowNumber===42&&!row[4];
assert(row[15]==='3.3'&&['','2'].includes(row[3]||'')&&['','снизу'].includes(row[4]));
const clean=v=>String(v||'').replace(/^stableId:\s*/,'').trim();
const idx=await diagramIndex({file:'graph/draw/generated/queryModel.drawio'});
const head=id=>{const a=idx.cells.filter(c=>c.stableId===id);const b=a.filter(c=>!a.some(p=>p.cellId===c.parent));assert(b.length===1,id);return b[0];};
const upper=head(clean(row[7])),target=['','нет'].includes(clean(row[12]))?null:head(clean(row[12]));
const lower=clean(row[10])?head(clean(row[10])):null;
const rawScale=String(row[11]||'').trim();
const explicitScale=rawScale?Number(rawScale.replace('%','').replace(',','.'))/(rawScale.endsWith('%')?100:1):null;
assert(lower||(Number.isFinite(explicitScale)&&explicitScale>=.1&&explicitScale<=4),'Specify upper + lower framing nodes, or an explicit scale; live window scale is not a scene instruction');
const owner='services/api/claude.ts:1022:0:2911:1';
const call=x=>bridge({functionStableId:owner,...x});
const base={surface:'diagram',stableId:upper.stableId,cellId:upper.cellId};
const a=(await read('alignment.json')).alignment,text=a.characters.join('');
const cue=target?a.character_start_times_seconds[text.indexOf(rowNumber===40?'залогировать':'посмотрим')]:null;if(target)assert(Number.isFinite(cue));
const duration=Math.max(a.character_end_times_seconds.at(-1)+1, target?cue+4:0);
const markers=rowNumber===39?[
 ['Если неподписочный','f0-n12','1052:4:1052:39'],
 ['На диаграмме','f0-n18-part-1','1053:4:1060:15'],
 ['через await','f0-n22-part-2','1054:6:1054:44'],
 ['два параметра','f0-n27','1055:8:1055:26'],
 ['дефолтное значение','f0-n28','1056:8:1058:9'],
 ['ожидаемый формат','f0-n22-awaited-type','1054:44:1054:66'],
 ['из его поля activated','f0-n29-part-2','1060:6:1060:15'],
 ['Что за аварийная','f0-n27','1055:8:1055:26'],
]:rowNumber===40?[
 ['залогировать','f0-n23','1062:4:1062:42'],
 ['сформировать стандартное','f0-n30-part-2','1063:10:1066:5'],
 ['выбрать другую модель','f0-n39-part-3','1064:6:1064:42'],
]:rowNumber===42?[
 ['Сначала проверка','f0-n8','1033:6:1033:26'],
 ['вызов внутри вызова','f1-n3-part-1','1033:6:1033:26'],
 ['нескольких функций','f1-n1','1033:6:1033:26'],
 ['фиксируем попытку','f0-n10','1034:4:1034:62'],
 ['откуда пришёл','f0-n14-part-2','1034:27:1034:46'],
 ['какая модель','f0-n15-part-2','1034:48:1034:61'],
 ['своё локальное','f2-n1','1034:4:1034:62'],
 ['в массив','f2-n2-part-2','1034:4:1034:62'],
 ['создаётся стоковое','f0-n20','1035:20:1040:6'],
 ['из нашей настройки','f0-n35-part-3','1037:8:1038:49'],
 ['стандартной фразы','f0-n35-part-5','1037:8:1038:49'],
 ['Причина остановки','f0-n19-part-5','1041:4:1041:44'],
 ['Через yield','f0-n34-part-1','1043:4:1043:17'],
 ['Следующий return','f0-n41','1044:4:1044:10'],
]:[];
const timedMarkers=markers.map(([phrase,cellId,range])=>{const pos=text.indexOf(phrase);assert(pos>=0,phrase);const c=idx.cells.find(c=>c.cellId===cellId);assert(c?.stableId,cellId);return{phrase,cellId,stableId:c.stableId,sourceStableId:'services/api/claude.ts:'+range,time:a.character_start_times_seconds[pos]};});
const obs=await connectObs();let recording,owned=false,completed=false;
const events=[];const wait=ms=>new Promise(r=>setTimeout(r,Math.max(0,ms)));
try{
 assert(!(await obs.request('GetRecordStatus')).outputActive);
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});assert(settings.inputSettings.window.includes('graphKoda PRESENTATION'));
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 const active=sceneItems.filter(i=>i.sceneItemEnabled);assert(active.length===1);
 const tr=active[0].sceneItemTransform;assert(tr.sourceWidth===1920&&tr.sourceHeight===1032&&tr.scaleX===1&&tr.scaleY===1);
 const left=head(owner+':flow-start');
 const horizontal={leftStableId:left.stableId,leftCellId:left.cellId};
 const sourceStart=rowNumber===37?owner:`services/api/claude.ts:${Number(row[5])}:0:${Number(row[5])}:1`;
 const sourceEnd=row[6]?`services/api/claude.ts:${Number(row[6])}:0:${Number(row[6])}:1`:undefined;
 const source=diagramOnly?await call({surface:'editor',action:'openDiagram',filePath:'graph/draw/generated/queryModel.drawio'}):await call({surface:'editor',action:'openSource',filePath:'graph/draw/generated/queryModel.drawio',stableId:sourceStart,endStableId:sourceEnd,editorAreaHeight:960,placement:'BELOW'});
 if(diagramOnly)await wait(1200);
 const framing=lower?{bottomStableId:lower.stableId,bottomCellId:lower.cellId}:{scale:explicitScale};
 if(clean(row[9])){const right=head(clean(row[9]));Object.assign(framing,{rightStableId:right.stableId,rightCellId:right.cellId});}
 await call({...base,action:'presentFocus',...horizontal,...framing,topPadding:16,durationMs:0});
 const fitted=await call({...base,action:'presentRead'});
 await call({...base,action:'presentFocus',...horizontal,scale:fitted.camera.scale,topPadding:16,durationMs:0});
 await call({...base,action:'presentPointer',pointerId:'narrator',visible:false});
 if(!diagramOnly)await call({surface:'editor',action:'sourcePointer',visible:false,stableId:owner});
 const initial=await call({...base,action:'presentRead'});assert(initial.visible);
 // Continued shots start at the family top plus a small fixed gap. Do not
 // retain the preceding step merely because a minimal reveal would allow it.
 let reveal=null;
 if(target&&timedMarkers.length){
  const roots=new Set([target,...timedMarkers.map(m=>idx.cells.find(c=>c.cellId===m.cellId))].map(c=>{
   while(c?.parent&&!/fold-row-/.test(c.parent)){const parent=idx.cells.find(p=>p.cellId===c.parent);if(!parent)break;c=parent;}
   return c.parent;
  }));
  const members=idx.cells.filter(c=>roots.has(c.parent)&&c.stableId);
  const frames=[];
  for(const c of members)frames.push(await call({surface:'diagram',action:'presentRead',stableId:c.stableId,cellId:c.cellId}));
  assert(frames.length,'No measurable call families');
  const top=Math.min(...frames.map(f=>f.screenBounds.y)),bottom=Math.max(...frames.map(f=>f.screenBounds.y+f.screenBounds.height));
  const inset=32;
  assert(bottom-top<=initial.viewport.height-2*inset,'Narrated families need separate chunks at this scale');
  const delta=top-inset;
  const annotationFrames=[];
  for(const f of frames)for(const annotation of f.annotations||[]){
   if(annotationFrames.some(x=>x.cellId===annotation.cellId))continue;
   const af=await call({surface:'diagram',action:'presentRead',stableId:f.stableId,cellId:annotation.cellId});
   assert(af.screenBounds.y-delta>=0&&af.screenBounds.y+af.screenBounds.height-delta<=initial.viewport.height,'Annotation does not fit family-aligned frame');
   annotationFrames.push(af);
  }
  const targetFrame=await call({surface:'diagram',action:'presentRead',stableId:target.stableId,cellId:target.cellId});
  reveal={frames,annotationFrames,inset,delta,topPadding:targetFrame.screenBounds.y-delta};
 }
 if(!target)for(const marker of timedMarkers){const frame=await call({surface:'diagram',action:'presentRead',stableId:marker.stableId,cellId:marker.cellId});assert(frame.visible,'Offscreen marker: '+marker.cellId);}
 const lowerFrame=lower?await call({surface:'diagram',action:'presentRead',stableId:lower.stableId,cellId:lower.cellId}):null;
 assert(!lowerFrame||lowerFrame.visible,'Lower framing target must fit before recording');
 if(row[3]==='2'){
  const diagramPointer=await call({...base,action:'presentPointer',pointerId:'narrator',durationMs:0});
  const codePointer=diagramOnly?null:await call({surface:'editor',action:'sourcePointer',stableId:upper.stableId});
  const pointerFrame=await call({...base,action:'presentRead'});
  assert(pointerFrame.visible&&JSON.stringify(pointerFrame.camera)===JSON.stringify(initial.camera),'Pointer must not scroll the scene');
  events.push({type:'dual-pointers',diagramPointer,codePointer,pointerFrame});
 }
 await fs.copyFile(idx.file,path.join(out,'source.drawio'));
 await fs.writeFile(path.join(out,'initial-scene.json'),JSON.stringify({initialCamera:initial,lowerFrame,framing,source,reveal},null,2));
 await obs.request('SetRecordDirectory',{recordDirectory:out});
 await obs.request('StartRecord');owned=true;const start=performance.now();
 if(target){
 await wait(Math.max(0,cue-(rowNumber===40?1.8:0))*1000-(performance.now()-start));
 const camera=reveal?.delta===0?null:await call({surface:'diagram',action:'presentFocus',...horizontal,stableId:target.stableId,cellId:target.cellId,scale:initial.camera.scale,topPadding:reveal?.topPadding??48,durationMs:1300});
 assert(!camera||camera.transition.samples.every(s=>Math.abs(s.left-initial.camera.scrollLeft)<1));
 const code=await call({surface:'editor',action:'openSource',filePath:'graph/draw/generated/queryModel.drawio',stableId:target.stableId,previousStableId:sourceStart,placement:'BELOW'});
 const final=await call({surface:'diagram',action:'presentRead',stableId:target.stableId,cellId:target.cellId});assert(final.visible);
 if(reveal){
  assert(Math.abs(final.camera.scrollTop-initial.camera.scrollTop-reveal.delta)<3,'Reveal scrolled farther than necessary');
  // Geometry is translated rigidly at a fixed scale; verify every measured
  // family member without delaying the narration with extra bridge round trips.
  const dy=final.camera.scrollTop-initial.camera.scrollTop;
  for(const f of reveal.frames)assert(f.screenBounds.y-dy>=reveal.inset-3&&f.screenBounds.y+f.screenBounds.height-dy<=final.viewport.height-reveal.inset+3,'Family clipped or too close to frame');
 }
 events.push({type:'transition',camera,code,final});
 }
 for(const marker of timedMarkers){
  await wait(Math.max(0,marker.time-1)*1000-(performance.now()-start));
  const diagramPointer=await call({surface:'diagram',action:'presentPointer',stableId:marker.stableId,cellId:marker.cellId,pointerId:'narrator',durationMs:200});
  const codePointer=diagramOnly?null:await call({surface:'editor',action:'sourcePointer',stableId:marker.sourceStableId});
  const frame=await call({surface:'diagram',action:'presentRead',stableId:marker.stableId,cellId:marker.cellId});assert(frame.visible,'Narrated target outside frame');
  events.push({type:'narration-pointer',...marker,readyTime:(performance.now()-start)/1000,diagramPointer,codePointer});
 }
 await wait(duration*1000-(performance.now()-start));
 if(!target){const final=await call({...base,action:'presentRead'});assert(JSON.stringify(final.camera)===JSON.stringify(initial.camera),'Static scene camera moved');events.push({type:'static-camera-verified',final});}
 completed=true;
}finally{
 if(owned)recording=await obs.request('StopRecord');obs.close();
 await fs.writeFile(path.join(out,'recording.json'),JSON.stringify({completed,recording,duration,events},null,2));
}
assert(completed);await wait(1600);
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify({duration,voice:'3.3',row:rowNumber,source:idx.file,events},null,2));
console.log(out);
