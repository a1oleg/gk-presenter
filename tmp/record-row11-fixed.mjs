import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],idx=await diagramIndex({file:'graph/draw/generated/Fisher-Yates.drawio'});
const fn=idx.cells.find(c=>c.cellId==='f0-n1').stableId.replace(/:flow-start$/,'');
const a=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment,text=a.characters.join('');
const source=await fs.readFile('C:/GitHub/graphKoda/examples/fisher-yates/src/shuffle.ts','utf8'),lines=source.split(/\r?\n/);
function sourceId(line,token){const col=lines[line-1].indexOf(token);if(col<0)throw Error('Missing source token');return `examples/fisher-yates/src/shuffle.ts:${line}:${col}:${line}:${col+token.length}`;}
const scenario=await fs.readFile(path.join(out,'scenario.json'),'utf8').then(JSON.parse).catch(()=>null);
const entries=scenario?scenario.events.map(e=>[e.atWord,e.diagramCell,e.codeLine,e.codeToken]):[['массив','f0-n2-part-1',26,'alphabet'],['объект','f0-n3-part-1',25,'current.index']];
const cues=entries.map(([anchor,id,line,token],n)=>{const i=text.indexOf(anchor),cell=idx.cells.find(c=>c.cellId===id);if((i<0&&!Number.isFinite(scenario?.events[n]?.time))||!cell)throw Error('Missing cue');return {...cell,anchor,time:scenario?.events[n]?.time??a.character_start_times_seconds[i],sourceStableId:sourceId(line,token)};});
const send=(action,c,extra={})=>bridge({surface:'diagram',action,functionStableId:fn,stableId:c.stableId,cellId:c.cellId,...extra});
const pointCode=c=>bridge({surface:'editor',action:'sourcePointer',functionStableId:fn,stableId:c.sourceStableId});
const before=await send('presentRead',cues[0]);
const motionCode=scenario?.kind==='dual-scene';
if(motionCode&&scenario.diagram.camera&&JSON.stringify(before.camera)!==JSON.stringify(scenario.diagram.camera.camera))throw Error('Diagram camera changed since layout validation');
const codeBefore=motionCode?{renderer:'Motion Canvas'}:await pointCode(cues[0]);
if(scenario&&!motionCode&&(!scenario.code.layout.safe||scenario.code.layout.calibration.visibleStartLine!==codeBefore.visibleStartLine))throw Error('Code viewport no longer matches validated caption layout');
await send('presentPointer',cues[0],{durationMs:0});
const obs=await connectObs();let active=false;
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Another recording active');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const scene=await obs.request('GetSceneItemList',{sceneName}),item=scene.sceneItems.find(c=>c.sourceName==='VS Code OBS');
 const setting=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});
 if(!item?.sceneItemEnabled||item.sceneItemTransform.sourceWidth!==1920||item.sceneItemTransform.sourceHeight!==1032||!setting.inputSettings.window.includes('graphKoda PRESENTATION'))throw Error('OBS capture target mismatch');
 if(scene.sceneItems.some(x=>x.sceneItemEnabled&&x!==item))throw Error('Unexpected source visible');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify(scene,null,2));
 await obs.request('StartRecord');active=true;const start=performance.now(),events=[];
 for(const cue of cues){await new Promise(r=>setTimeout(r,Math.max(0,cue.time*1000-(performance.now()-start))));events.push({...cue,diagram:await send('presentPointer',cue,{durationMs:500}),code:motionCode?{renderer:'Motion Canvas',time:cue.time}:await pointCode(cue)});}
 await new Promise(r=>setTimeout(r,Math.max(0,(a.character_end_times_seconds.at(-1)+1)*1000-(performance.now()-start))));
 const result=await obs.request('StopRecord');active=false;await new Promise(r=>setTimeout(r,1200));
 const recording=path.join(out,'recording'+path.extname(result.outputPath));await fs.copyFile(result.outputPath,recording);
 const after=await send('presentRead',cues[0]);
 if(JSON.stringify(before.camera)!==JSON.stringify(after.camera))throw Error('Camera changed');
 if(events.some(e=>e.code.visibleStartLine!==codeBefore.visibleStartLine))throw Error('Code scroll changed');
 const transform=await obs.request('GetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId});
 if(JSON.stringify(transform.sceneItemTransform)!==JSON.stringify(item.sceneItemTransform))throw Error('OBS framing changed');
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({recording,cameraBefore:before,cameraAfter:after,codeBefore,events,diagram:idx.file,diagramHash:idx.digest,framingPreserved:true,scroll:false,codeScrollPreserved:true},null,2));
 console.log('RECORDING_READY');
}finally{if(active)await obs.request('StopRecord');obs.close();}
