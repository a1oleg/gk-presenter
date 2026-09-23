import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';
import {frameSheetScene} from '../../coldKode/dev/frameSheetScene.mjs';
const out=path.resolve(process.argv[2]);
const read=async n=>JSON.parse(await fs.readFile(path.join(out,n),'utf8'));
const alignment=(await read('alignment.json')).alignment,text=alignment.characters.join('');
const snapshot=await read('sheet-source.json'),row=snapshot.values[0];
assert(row[3]==='2'&&['справа','снизу'].includes(row[4])&&row[15]==='3.3');
const placement=row[4]==='снизу'?'BELOW':'RIGHT';
const cleanId=value=>String(value||'').replace(/^stableId:\s*/,'').replace(/:flow-start$/,'').trim();
const file='graph/draw/generated/queryModel.drawio',idx=await diagramIndex({file}),owner='services/api/claude.ts:1022:0:2911:1';
const sourcePrefix='services/api/claude.ts:';
const cues=[
 ['Откроем','f0-n1','1022:16:1022:26'],
 ['принимает сообщения','f0-n2','1023:2:1023:21'],
 ['системный промпт','f0-n3','1024:2:1024:28'],
 ['настройки размышления','f0-n4','1025:2:1025:32'],
 ['доступные инструменты','f0-n5','1026:2:1026:14'],
 ['сигнал отмены','f0-n6','1027:2:1027:21'],
 ['объект дополнительных','f0-n7','1028:2:1028:18'],
 ['После параметров','f0-n1-return-signature-method','1029:3:1029:17'],
 ['события потока','f0-n1-return-signature-variant-0','1030:2:1030:13'],
 ['сообщения ассистента','f0-n1-return-signature-variant-1','1030:16:1030:32'],
 ['сообщения об ошибках','f0-n1-return-signature-variant-2','1030:35:1030:56'],
 ['А void','f0-n1-return-signature-variant-3','1031:2:1031:6'],
].map(([phrase,cellId,range])=>{const offset=text.indexOf(phrase);assert(offset>=0,phrase);return{phrase,time:alignment.character_start_times_seconds[offset],cellId,stableId:idx.cells.find(c=>c.cellId===cellId)?.stableId,sourceStableId:sourcePrefix+range};});
const duration=alignment.character_end_times_seconds.at(-1)+.8;
const base={functionStableId:owner},events=[],obs=await connectObs();let owned=false,recording,completed=false;
let initialCamera,opened,codeRangeFits=false;
const call=x=>bridge({...base,...x});
const pause=ms=>new Promise(r=>setTimeout(r,Math.max(0,ms)));
const move=async cue=>{
 const diagram=await call({surface:'diagram',action:'presentPointer',cellId:cue.cellId,stableId:cue.stableId,pointerId:'narrator',durationMs:280});
 const code=await call({surface:'editor',action:'sourcePointer',stableId:cue.sourceStableId});
 const frame=await call({surface:'diagram',action:'presentRead',cellId:cue.cellId,stableId:cue.stableId});
 assert(frame.visible,'Offscreen pointer target '+cue.cellId);
 return{diagram,code,frame};
};
try{
 assert(!(await obs.request('GetRecordStatus')).outputActive,'OBS already recording');
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});
 assert(settings.inputSettings.window.includes('coldKode PRESENTATION'),'Wrong capture window');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 assert(sceneItems.filter(i=>i.sceneItemEnabled).length===1);
 const item=sceneItems.find(i=>i.sourceName==='VS Code OBS'&&i.sceneItemEnabled);assert(item);
 const transform=item.sceneItemTransform,w=transform.sourceWidth-transform.cropLeft-transform.cropRight,h=transform.sourceHeight-transform.cropTop-transform.cropBottom;
 assert(w>0&&h>0);
 assert(transform.sourceWidth===1920&&transform.sourceHeight===1032,'Maximize the presentation window before recording; do not upscale a smaller capture');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify({sceneName,item},null,2));
 await obs.request('SetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId,sceneItemTransform:{boundsType:'OBS_BOUNDS_NONE',alignment:5,scaleX:1,scaleY:1,positionX:0,positionY:90,cropTop:132,cropBottom:0,cropLeft:0,cropRight:0}});
 const video=await obs.request('GetVideoSettings');assert(video.outputWidth===1920&&video.outputHeight===1080);
 await fs.copyFile(idx.file,path.join(out,'source.drawio'));
 // Establish both panes and the initial framing BEFORE OBS starts recording.
 const framing=await frameSheetScene({row:36,file:idx.file,functionStableId:owner,apply:false});
 assert(Array.from({length:12},(_,i)=>(framing.source.values[0][i]||'')===(row[i]||'')).every(Boolean),'Sheet framing changed since narration');
 const start=cleanId(row[5])||owner,end=cleanId(row[6]);
 // A numeric end line accompanies the user's already prepared manual pane.
 // Do not reopen it: that would replace the hand-set divider and scroll position.
 if(/^\d+$/.test(end)){
  const live=await call({surface:'editor',action:'sourcePointer',stableId:sourcePrefix+'1022:16:1022:26'});
  opened={stage:'manual-layout-preserved',visibleRanges:[{startLine:live.visibleStartLine,endLine:Number(end)}],endBoundarySource:'user-specified manual code range'};
 }else opened=await call({surface:'editor',action:'openSource',filePath:file,stableId:start,endStableId:end||undefined,editorAreaHeight:transform.sourceHeight-72,placement});
 const firstLine=Number(start.match(/:(\d+):\d+:\d+:\d+$/)?.[1]);
 const lastLine=/^\d+$/.test(end)?Number(end):end?Number(end.match(/:\d+:\d+:(\d+):\d+$/)?.[1]):Math.max(...cues.map(c=>Number(c.sourceStableId.match(/:\d+:\d+:(\d+):\d+$/)[1])));
 codeRangeFits=opened.visibleRanges.some(r=>r.startLine<=firstLine&&r.endLine>=lastLine);
 await call({...framing.command,durationMs:0});
 await pause(700);
 initialCamera=await call({surface:'diagram',action:'presentRead',stableId:framing.upper.stableId,cellId:framing.upper.cellId});
 assert(initialCamera.visible&&Math.abs(initialCamera.screenBounds.y-16)<3,'Initial head is not at the top');
 await fs.writeFile(path.join(out,'initial-scene.json'),JSON.stringify({framing,initialCamera,opened,codeRangeFits,captureScale:1},null,2));
 await move(cues[0]);
 await obs.request('SetRecordDirectory',{recordDirectory:out});
 await obs.request('StartRecord');owned=true;const started=performance.now();
 for(const cue of cues){
  await pause(cue.time*1000-(performance.now()-started));
  // Keep a chunk still throughout narration. Advance only when the NEXT
  // narrated step lies outside it, after finishing the previous visible step.
  const beforeCue=await call({surface:'diagram',action:'presentRead',cellId:cue.cellId,stableId:cue.stableId});
  if(/^f0-n[2-7]$/.test(cue.cellId)&&!beforeCue.visible){
   const camera=await call({surface:'diagram',action:'presentFocus',stableId:cue.stableId,cellId:cue.cellId,scale:initialCamera.camera.scale,topPadding:16,durationMs:650});
   const code=codeRangeFits?{stage:'source-scroll-skipped',reason:'Requested code range is already fully visible'}:await call({surface:'editor',action:'openSource',filePath:file,stableId:cue.sourceStableId,placement});
   events.push({type:'chunk-scroll',time:(performance.now()-started)/1000,firstCell:cue.cellId,before:beforeCue,camera,code});
  }
  if(cue.cellId==='f0-n1-return-signature-method'){
   const cellId='f0-n1-return-signature-variant-0',stableId=idx.cells.find(c=>c.cellId===cellId).stableId;
   const lastId='f0-n1-return-signature-variant-3';
   const before=await call({surface:'diagram',action:'presentRead',cellId,stableId});
   const last=await call({surface:'diagram',action:'presentRead',cellId:lastId,stableId:idx.cells.find(c=>c.cellId===lastId).stableId});
   const b=before.screenBounds,overflow=Math.max(0,last.screenBounds.y+last.screenBounds.height-(before.viewport.height-20));
   let camera=null;
   if(overflow>0)camera=await call({surface:'diagram',action:'presentFocus',cellId,stableId,scale:initialCamera.camera.scale,topPadding:Math.max(16,b.y-overflow),durationMs:650});
   const after=await call({surface:'diagram',action:'presentRead',cellId,stableId});
   const lastAfter=await call({surface:'diagram',action:'presentRead',cellId:lastId,stableId:idx.cells.find(c=>c.cellId===lastId).stableId});
   assert(after.visible&&lastAfter.visible,'Generator and its children must fit together');
   events.push({type:'generator-reveal',time:(performance.now()-started)/1000,before,after,camera,minimalScroll:overflow});
  }
  events.push({...cue,actualTime:(performance.now()-started)/1000,result:await move(cue)});console.log(cue.phrase);
 }
 await pause(duration*1000-(performance.now()-started));completed=true;
}finally{
 if(owned)recording=await obs.request('StopRecord');obs.close();
 await fs.writeFile(path.join(out,'recording.json'),JSON.stringify({completed,recording,duration,events,source:idx.file,digest:idx.digest},null,2));
}
assert(completed);await pause(1600);
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify({version:1,duration,canvas:{width:1920,height:1080,fps:30},voice:'3.3',cues,source:idx.file},null,2));
console.log(JSON.stringify({out,duration,recording}));
