import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bridge} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';

const out=path.resolve(process.argv[2]);
const run=JSON.parse(await fs.readFile(path.join(out,'runtime-session.json'),'utf8'));
const alignment=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment;
const text=alignment.characters.join('');
function anchor(s){const i=text.indexOf(s);if(i<0)throw Error('Missing spoken anchor: '+s);return alignment.character_start_times_seconds[i];}
const base={functionStableId:run.root};
const events=[];
let started=0;
async function step(input){const before=performance.now();const result=await bridge({...base,...input});events.push({time:(before-started)/1000,completed:(performance.now()-started)/1000,input,result});return result;}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const obs=await connectObs();let owned=false;
try {
  if((await obs.request('GetRecordStatus')).outputActive)throw Error('OBS already recording');
  await step({surface:'runtime',action:'selectAll',sessionId:run.sessionId});
  await step({surface:'editor',action:'openDiagram',filePath:'graph/draw/generated/Fisher-Yates.drawio'});
  await step({surface:'diagram',action:'dismissMenu'});
  await step({surface:'diagram',action:'presentFocus',stableId:run.loop,cellId:'f0-n4',scale:0.6});
  const readFrame=async()=>bridge({...base,surface:'diagram',action:'presentRead',stableId:run.loop,cellId:'f0-n4'});
  const initialFrame=await readFrame();
  assert(initialFrame.visible,'Loop is outside the initial viewport');
  await step({surface:'diagram',action:'presentPointer',stableId:run.loop,cellId:'f0-n4',pointerId:'narrator',text:'for'});
  const {sceneItems}=await obs.request('GetSceneItemList',{sceneName:'coldKode A12'});
  const capture=sceneItems.find(i=>i.sourceName==='coldKode presentation capture');
  if(!capture||capture.sceneItemTransform.sourceWidth<=0)throw Error('Empty capture');
  await obs.request('SetSceneItemTransform',{sceneName:'coldKode A12',sceneItemId:capture.sceneItemId,sceneItemTransform:{boundsType:'OBS_BOUNDS_SCALE_INNER',boundsWidth:1920,boundsHeight:1080,boundsAlignment:0,alignment:5,positionX:0,positionY:0}});
  await obs.request('SetRecordDirectory',{recordDirectory:out});
  const schedule=[
    [anchor('откроем'),{surface:'diagram',action:'contextMenu',cellId:'f0-n4'}],
    [anchor('Здесь')-0.25,{surface:'diagram',action:'menuClick',label:'показать статистику Цикла'}],
    [anchor('вот первый'),{surface:'runtime',action:'selectCase',index:0,sessionId:run.sessionId}],
    [anchor('Нажимая'),{surface:'runtime',action:'selectCase',index:1,sessionId:run.sessionId}],
    [anchor('как именно'),{surface:'runtime',action:'selectCase',index:3,sessionId:run.sessionId}],
    [anchor('все ветки'),{surface:'runtime',action:'selectCase',index:6,sessionId:run.sessionId}],
    [anchor('до последнего'),{surface:'runtime',action:'selectCase',index:7,sessionId:run.sessionId}],
  ];
  await fs.writeFile(path.join(out,'capture-plan.json'),JSON.stringify({sessionId:run.sessionId,schedule},null,2));
  events.length=0;
  await obs.request('StartRecord');owned=true;started=performance.now();
  const cameras=[];
  const readCamera=async()=> {
    const frame=await readFrame();
    assert(frame.visible,'Loop left the visible viewport');
    for(const key of ['x','y','width','height']) assert(Math.abs(frame.screenBounds[key]-initialFrame.screenBounds[key])<1,'Loop moved on screen: '+key);
    return frame.screenBounds;
  };
  for(const [at,input] of schedule){
    await sleep(Math.max(0,at*1000-(performance.now()-started)));
    const before=input.action==='selectCase'?await readCamera():null;
    await step(input);
    if(input.action==='menuClick'){
      await sleep(300);
      await readCamera();
    }
    if(before){
      await bridge({...base,surface:'diagram',action:'presentPointer',stableId:run.loop,cellId:'f0-n4',pointerId:'narrator',visible:false});
      await sleep(200);
      const after=await readCamera();
      cameras.push({index:input.index,before,after});
      await fs.writeFile(path.join(out,'camera-checks.json'),JSON.stringify(cameras,null,2));
      assert.deepEqual(after,before,'Case selection moved the diagram');
      assert.deepEqual(after,cameras[0].before,'Camera drifted between cases');
    }
  }
  await sleep(Math.max(0,(alignment.character_end_times_seconds.at(-1)+0.5)*1000-(performance.now()-started)));
} finally {
  if(owned){const stopped=await obs.request('StopRecord');await fs.writeFile(path.join(out,'recording.json'),JSON.stringify({...stopped,sessionId:run.sessionId,events},null,2));console.log(JSON.stringify(stopped));}
  obs.close();
}
