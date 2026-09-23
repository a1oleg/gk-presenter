import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bridge} from '../../graphKoda/graph/presentation/presentation.mjs';
import {applyPreparedScene,checkPreparedScene,loadPreparedScene} from '../src/scene-staging.mjs';
import {connectObs} from './obs_control.mjs';

const out=path.resolve(process.argv[2]);
const {plan}=await loadPreparedScene(out);
assert.equal(plan.sheet.row,14);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const sheet=await read('scene-sheet-source.json'),voice=await read('request.json');
assert.equal(voice.text.trim(),sheet.values[0][0].trim());
const run=await read('runtime-session.json');
const alignment=(await read('alignment.json')).alignment;
const text=alignment.characters.join('');
const anchor=s=>{const i=text.indexOf(s);assert(i>=0,'Missing narration anchor: '+s);return alignment.character_start_times_seconds[i];};
const duration=alignment.character_end_times_seconds.at(-1)+0.8;
const base={functionStableId:run.root};
const step=input=>bridge({...base,...input});
const sleep=ms=>new Promise(r=>setTimeout(r,Math.max(0,ms)));
const events=[],cameras=[];
const obs=await connectObs();let owned=false,started=0,completed=false;
try {
  assert(!(await obs.request('GetRecordStatus')).outputActive,'OBS already recording');
  await applyPreparedScene(out);
  await step({surface:'diagram',action:'contextMenu',cellId:'f0-n4'});
  await step({surface:'diagram',action:'menuClick',label:'показать статистику Цикла'});
  await step({surface:'runtime',action:'waitForAnalysis',sessionId:run.sessionId});
  await step({surface:'runtime',action:'selectAll',sessionId:run.sessionId});
  await step({surface:'diagram',action:'presentPointer',stableId:run.loop,cellId:'f0-n4',pointerId:'narrator',visible:false});
  await step({surface:'runtime',action:'selectCase',sessionId:run.sessionId,index:0,durationMs:500});
  await sleep(500);
  await checkPreparedScene(out);
  const readFrame=()=>step({surface:'diagram',action:'presentRead',stableId:run.loop,cellId:'f0-n4'});
  const initial=await readFrame();assert(initial.visible);
  const schedule=[['repeat','segment-1'],['false','segment-2']].map(([word,id])=>[Math.max(0,anchor(word)-0.65),{surface:'runtime',action:'selectSegment',id,sessionId:run.sessionId,durationMs:650}]);
  assert(schedule[1][0]>schedule[0][0]+0.65,'Segment cues overlap');
  const video=await obs.request('GetVideoSettings');
  assert.equal(video.outputWidth,plan.canvas.width);assert.equal(video.outputHeight,plan.canvas.height);assert.equal(video.fpsNumerator/video.fpsDenominator,plan.canvas.fps);
  await obs.request('SetCurrentProgramScene',{sceneName:'graphKoda A12'});
  const {sceneItems}=await obs.request('GetSceneItemList',{sceneName:'graphKoda A12'});
  const capture=sceneItems.find(i=>i.sourceName==='graphKoda presentation capture');assert(capture?.sceneItemTransform.sourceWidth>0);
  await obs.request('SetSceneItemTransform',{sceneName:'graphKoda A12',sceneItemId:capture.sceneItemId,sceneItemTransform:{boundsType:'OBS_BOUNDS_SCALE_INNER',boundsWidth:1920,boundsHeight:1080,boundsAlignment:0,alignment:5,positionX:0,positionY:0}});
  await obs.request('SetRecordDirectory',{recordDirectory:out});
  await fs.writeFile(path.join(out,'capture-plan.json'),JSON.stringify({row:14,initialCase:0,duration,schedule},null,2));
  await obs.request('StartRecord');owned=true;started=performance.now();
  for(const [at,input] of schedule){
    await sleep(at*1000-(performance.now()-started));
    const time=(performance.now()-started)/1000;
    const result=await step(input);
    events.push({time,input,result});assert(result.pointerSamples.length>=3);
    await sleep(250);
    const frame=await readFrame();assert(frame.visible);
    for(const key of ['x','y','width','height'])assert(Math.abs(frame.screenBounds[key]-initial.screenBounds[key])<1,'Diagram moved: '+key);
    cameras.push({segment:input.id,before:initial.screenBounds,after:frame.screenBounds});
    await checkPreparedScene(out);
  }
  await sleep(duration*1000-(performance.now()-started));completed=true;
} finally {
  if(owned){
    const stopped=await obs.request('StopRecord');
    await fs.writeFile(path.join(out,'recording.json'),JSON.stringify({...stopped,completed,duration,sessionId:run.sessionId,initialCase:0,events},null,2));
    await fs.writeFile(path.join(out,'camera-checks.json'),JSON.stringify(cameras,null,2));
    console.log(JSON.stringify({completed,...stopped}));
  }
  obs.close();
}
