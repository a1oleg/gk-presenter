// Capture semantic two-pane states, not guessed desktop coordinates. No diagram edits.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';
const [directory,planFile,...flags]=process.argv.slice(2);
if(flags.some(f=>f!=='--standalone'))throw Error('Unknown capture option');
if(!directory||!planFile)throw Error('Usage: capture_source_scene.mjs AUDIO_DIRECTORY PLAN');
const out=path.resolve(directory),plan=JSON.parse(await fs.readFile(planFile,'utf8'));
const snapshot=JSON.parse(await fs.readFile(path.join(out,'sheet-source.json'),'utf8'));
const row=snapshot.values[1];
const sheetSceneId=String(row[1]).endsWith('.json')?JSON.parse(await fs.readFile(row[1],'utf8')).stableId:row[1];
if(sheetSceneId!==plan.stableId||row[2]!=='2'||row[3]!=='нет'||(row[4]==='снизу'?'BELOW':'RIGHT')!==plan.placement)throw Error('Plan differs from sheet instructions');
const index=await diagramIndex({file:plan.diagram});
// A mosaic's head has no parent with the same semantic identity.
const matches=index.cells.filter(c=>c.stableId===plan.stableId);
const heads=matches.filter(c=>!matches.some(p=>p.cellId===c.parent));
if(heads.length!==1)throw Error('Ambiguous semantic step head');
const base={functionStableId:plan.functionStableId},head=heads[0];
const previous=plan.previousFragment&&!flags.includes('--standalone')?JSON.parse(await fs.readFile(path.resolve(plan.previousFragment),'utf8')):null;
if(previous&&(previous.sha256!==index.digest||previous.placement!==plan.placement))throw Error('Previous fragment uses a different diagram or layout');
let opened=await bridge({...base,surface:'editor',action:'openSource',filePath:plan.diagram,stableId:previous?.stableId||plan.stableId,placement:plan.placement});
let focused=await bridge({...base,surface:'diagram',action:'presentFocus',stableId:previous?.stableId||plan.stableId,cellId:previous?.headCellId||head.cellId,includeAnnotations:true,includeStep:!previous&&plan.includeStep});
if(focused.formatPanelVisible!==false)throw Error('Format panel must be hidden before capture');
if(focused.viewport.height<250||focused.scale<.8)throw Error('Insufficient presentation space');
const hash=async f=>createHash('sha256').update(await fs.readFile(f)).digest('hex');
const sourceHash=await hash(opened.file);
const obs=await connectObs();
try {
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Do not alter a live recording');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 const captures=sceneItems.filter(x=>x.sceneItemEnabled);
 if(captures.length!==1||captures[0].inputKind!=='window_capture')throw Error('Expected only one window capture');
 const capture=captures[0],inputName=capture.sourceName;
 const settings=await obs.request('GetInputSettings',{inputName});
 if(!settings.inputSettings.window.includes('coldKode PRESENTATION')||settings.inputSettings.priority!==0)throw Error('OBS must use the exact separate presentation window');
 const {propertyItems}=await obs.request('GetInputPropertiesListPropertyItems',{inputName,propertyName:'window'});
 if(!propertyItems.some(x=>x.itemEnabled&&x.itemValue===settings.inputSettings.window))throw Error('Presentation window is not available');
 const video=await obs.request('GetVideoSettings');if(video.baseWidth!==1600||video.baseHeight!==900)throw Error('Expected 1600x900 canvas');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify({sceneName,...capture,settings},null,2));
 const {sourceWidth:w,sourceHeight:h}=capture.sceneItemTransform;
 if(!(w>0&&h>0))throw Error('Empty window capture');
 const scale=Math.min(1600/w,900/h);
 await obs.request('SetInputSettings',{inputName,inputSettings:{cursor:false},overlay:true});
 await obs.request('SetSceneItemTransform',{sceneName,sceneItemId:capture.sceneItemId,sceneItemTransform:{cropLeft:0,cropRight:0,cropTop:0,cropBottom:0,boundsType:'OBS_BOUNDS_NONE',alignment:5,rotation:0,scaleX:scale,scaleY:scale,positionX:(1600-w*scale)/2,positionY:(900-h*scale)/2}});
 let transition=null;
 if(previous){
  const last=previous.frames.at(-1);
  await bridge({...base,surface:'diagram',action:'presentPointer',stableId:previous.stableId,cellId:last.cellId,pointerId:'narrator',durationMs:0});
  await bridge({...base,surface:'editor',action:'sourcePointer',stableId:last.sourceStableId});
  await new Promise(r=>setTimeout(r,400));
  await obs.request('StartRecord');
  try {
   await new Promise(r=>setTimeout(r,200));
   opened=await bridge({...base,surface:'editor',action:'openSource',filePath:plan.diagram,stableId:plan.stableId,placement:plan.placement,previousStableId:previous.stableId});
   focused=await bridge({...base,surface:'diagram',action:'presentFocus',stableId:plan.stableId,cellId:head.cellId,includeAnnotations:true,includeStep:plan.includeStep,previousStableId:previous.stableId,durationMs:plan.transitionMs??1200});
   await new Promise(r=>setTimeout(r,200));
  }finally{transition=await obs.request('StopRecord');}
  // OBS acknowledges StopRecord before its muxer has necessarily flushed the file.
  let lastSize=-1,stable=0;const deadline=Date.now()+15000;
  while(stable<4&&Date.now()<deadline){await new Promise(r=>setTimeout(r,250));const size=(await fs.stat(transition.outputPath)).size;stable=size>0&&size===lastSize?stable+1:0;lastSize=size;}
  if(stable<4)throw Error('OBS recording did not finish flushing');
  await fs.copyFile(transition.outputPath,path.join(out,'transition-recording'+path.extname(transition.outputPath)));
  transition={...transition,originalOutputPath:transition.outputPath,outputPath:path.join(out,'transition-recording'+path.extname(transition.outputPath)),previousFragment:path.resolve(plan.previousFragment),previousStableId:previous.stableId,camera:focused.transition,source:opened};
  if(transition.camera.samples.length<5)throw Error('Too few samples for a smooth transition');
 }
 const frames=[];
 for(const [i,cue] of plan.markers.entries()){
  const diagram=await bridge({...base,surface:'diagram',action:'presentPointer',stableId:cue.diagramStableId||plan.stableId,cellId:cue.cellId,text:cue.text,pointerId:'narrator',durationMs:0});
  const code=await bridge({...base,surface:'editor',action:'sourcePointer',stableId:cue.sourceStableId});
  await new Promise(r=>setTimeout(r,600));
  const file=path.join(out,`dual-${String(i).padStart(2,'0')}.png`);
  await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:file,imageWidth:1600,imageHeight:900});
  frames.push({...cue,file,sha256:await hash(file),diagram,code});
 }
 if(sourceHash!==await hash(opened.file)||index.digest!==(await diagramIndex({file:plan.diagram})).digest)throw Error('Source/diagram changed during capture');
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({source:index.file,sha256:index.digest,sourceFile:opened.file,sourceSha256:sourceHash,stableId:plan.stableId,headCellId:head.cellId,placement:plan.placement,previousFragment:previous?path.resolve(plan.previousFragment):null,transition,opened,focused,frames,coordinateSource:'draw.io live view and VS Code semantic source ranges',obsWindow:settings.inputSettings.window},null,2));
 console.log(JSON.stringify({directory:out,frames:frames.length,headCellId:head.cellId,focused,code:frames.map(x=>x.code.text)}));
}finally{obs.close();}
