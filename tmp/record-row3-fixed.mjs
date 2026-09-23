import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],fn='services/api/claude.ts:1022:0:2911:1';
const a=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment,text=a.characters.join('');
const index=await diagramIndex({file:'graph/draw/generated/queryModel.drawio'});
const ids=['f0-n9','f0-n12','f0-n22','f0-n23','f0-n30'],anchors=['Сначала вычисляется','Потом проверяется','В таком случае','И если да','а для пользователя'];
const cues=ids.map((id,i)=>{const c=index.cells.find(x=>x.cellId===id),at=text.indexOf(anchors[i]);if(!c||at<0)throw Error('Missing cue');return {...c,anchor:anchors[i],time:a.character_start_times_seconds[at]};});
const send=(action,c,extra={})=>bridge({surface:'diagram',action,functionStableId:fn,stableId:c.stableId,cellId:c.cellId,...extra});
const cameraBefore=await send('presentRead',cues[0]);
const obs=await connectObs();let recording=false;
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Recording already active');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const before=await obs.request('GetSceneItemList',{sceneName}),item=before.sceneItems.find(x=>x.sourceName==='VS Code OBS');
 if(!item?.sceneItemEnabled||item.sceneItemTransform.sourceWidth<=0||item.sceneItemTransform.sourceHeight<=0)throw Error('OBS window unavailable; refusing black recording');
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});
 if(!settings.inputSettings.window.includes('graphKoda PRESENTATION')||settings.inputSettings.priority!==0)throw Error('Wrong OBS target');
 if(before.sceneItems.some(x=>x.sceneItemEnabled&&x.sourceName!=='VS Code OBS'))throw Error('Unexpected visible source');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify({sceneName,...before},null,2));
 await send('presentPointer',cues[0],{durationMs:0});
 await obs.request('StartRecord');recording=true;const start=performance.now(),events=[];
 for(const cue of cues){
  await new Promise(r=>setTimeout(r,Math.max(0,cue.time*1000-(performance.now()-start))));
  events.push({...cue,pointer:await send('presentPointer',cue,{durationMs:550})});
 }
 const end=a.character_end_times_seconds.at(-1)+.8;
 await new Promise(r=>setTimeout(r,Math.max(0,end*1000-(performance.now()-start))));
 const stopped=await obs.request('StopRecord');recording=false;
 await new Promise(r=>setTimeout(r,1500));
 const file=path.join(out,'recording'+path.extname(stopped.outputPath));await fs.copyFile(stopped.outputPath,file);
 const cameraAfter=await send('presentRead',cues[0]);
 if(JSON.stringify(cameraBefore.camera)!==JSON.stringify(cameraAfter.camera))throw Error('Camera changed during fixed-frame recording');
 const after=await obs.request('GetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId});
 if(JSON.stringify(after.sceneItemTransform)!==JSON.stringify(item.sceneItemTransform))throw Error('OBS framing changed');
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({recording:file,source:index.file,sha256:index.digest,cameraBefore,cameraAfter,events,scroll:false,obsFramingPreserved:true},null,2));
 console.log('RECORDING_READY');
}finally{if(recording)await obs.request('StopRecord');obs.close();}
