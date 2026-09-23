import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {materialDir} from '../src/material-paths.mjs';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';
const snapshot=JSON.parse(execFileSync('C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',['tmp/read_row2.py','!A41:P41'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
const row=snapshot.values[0];assert(!row[0]&&row[10]==='сохранить рамку от пред'&&row[4]==='снизу');
const previous=path.join(materialDir(),'scene-row040-below-1790163904528146500');
const metadata=JSON.parse(await fs.readFile(path.join(previous,'recording.json'),'utf8'));
const last=metadata.events.find(e=>e.type==='transition').final;
const out=path.join(materialDir(),'scene-row041-reverse-'+Date.now());await fs.mkdir(out);
const save=(n,v)=>fs.writeFile(path.join(out,n),JSON.stringify(v,null,2));
await save('sheet-source.json',snapshot);await save('request.json',{text:'',voice_id:null,model_id:null});
const index=await diagramIndex({file:'graph/draw/generated/queryModel.drawio'}),owner='services/api/claude.ts:1022:0:2911:1';
const id=x=>x.replace(/^stableId:\s*/,'');
const head=s=>{const a=index.cells.filter(c=>c.stableId===s),b=a.filter(c=>!a.some(p=>p.cellId===c.parent));assert(b.length===1,s);return b[0];};
const from=head(id(row[7])),to=head(id(row[12])),left=head(owner+':flow-start');
const call=x=>bridge({functionStableId:owner,...x});
const frame={surface:'diagram',action:'presentFocus',leftStableId:left.stableId,leftCellId:left.cellId,scale:last.camera.scale};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const obs=await connectObs();let owned=false,recording,completed=false,duration,events=[];
try{
 assert(!(await obs.request('GetRecordStatus')).outputActive);
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});assert(settings.inputSettings.window.includes('graphKoda PRESENTATION'));
 const codeStart=`services/api/claude.ts:${row[5]}:0:${row[5]}:1`,codeEnd=`services/api/claude.ts:${row[6]}:0:${row[6]}:1`;
 await call({surface:'editor',action:'openSource',filePath:'graph/draw/generated/queryModel.drawio',stableId:codeStart,endStableId:codeEnd,placement:'BELOW',editorAreaHeight:960});
 await call({...frame,stableId:from.stableId,cellId:from.cellId,topPadding:last.screenBounds.y,durationMs:0});
 await call({surface:'diagram',action:'presentPointer',stableId:from.stableId,cellId:from.cellId,pointerId:'narrator',visible:false});
 await call({surface:'editor',action:'sourcePointer',stableId:from.stableId,visible:false});
 const initial=await call({surface:'diagram',action:'presentRead',stableId:from.stableId,cellId:from.cellId});
 assert(Math.abs(initial.screenBounds.y-last.screenBounds.y)<3&&initial.camera.scale===last.camera.scale,'Previous framing not restored');
 const targetBefore=await call({surface:'diagram',action:'presentRead',stableId:to.stableId,cellId:to.cellId});
 const family=index.cells.filter(c=>c.parent===to.parent&&c.stableId),bounds=[];
 for(const c of family)bounds.push(await call({surface:'diagram',action:'presentRead',stableId:c.stableId,cellId:c.cellId}));
 const top=Math.min(...bounds.map(b=>b.screenBounds.y));
 const padding=32+targetBefore.screenBounds.y-top;
 await save('initial-scene.json',{initialCamera:initial,previousScene:previous,familyTopGap:32});
 await fs.copyFile(index.file,path.join(out,'source.drawio'));
 await obs.request('SetRecordDirectory',{recordDirectory:out});await obs.request('StartRecord');owned=true;
 const start=performance.now();await pause(500);
 const camera=await call({...frame,stableId:to.stableId,cellId:to.cellId,topPadding:padding,durationMs:1600});
 assert(camera.transition.samples.every(s=>Math.abs(s.left-initial.camera.scrollLeft)<1));
 // The installed source-scrolling API adds five context lines above its anchor.
 // Compensate for that presentation inset to place the requested line at top;
 // keep the semantic diagram target unchanged and verify the actual viewport.
 const requestedTopLine=Number(to.stableId.match(/:(\d+):\d+:\d+:\d+$/)[1]);
 const sourceAnchorLine=requestedTopLine+5;
 const sourceAnchor=`services/api/claude.ts:${sourceAnchorLine}:0:${sourceAnchorLine}:1`;
 const code=await call({surface:'editor',action:'openSource',filePath:'graph/draw/generated/queryModel.drawio',stableId:sourceAnchor,previousStableId:codeStart,placement:'BELOW'});
 assert(code.headroomLines===5,'Source scrolling inset changed');
 // openSource acknowledges starting the animation, not finishing it.
 // Keep recording through the full source scroll before the final hold.
 await pause((code.durationMs||0)+200);
 const sourceSettled=await call({surface:'editor',action:'sourcePointer',stableId:to.stableId,visible:false});
 const final=await call({surface:'diagram',action:'presentRead',stableId:to.stableId,cellId:to.cellId});assert(final.visible&&final.camera.scrollTop<initial.camera.scrollTop);
 events.push({type:'transition',camera,code,sourceSettled,sourceAnimationWaitMs:(code.durationMs||0)+200,final});await pause(1000);duration=(performance.now()-start)/1000;completed=true;
}finally{if(owned)recording=await obs.request('StopRecord');obs.close();await save('recording.json',{completed,recording,duration,events});}
assert(completed);
// The bridge exposes the visible line through pointer inspection only. Inspect
// after capture, then hide immediately so the silent clip has no pointer flash.
const sourceViewport=await call({surface:'editor',action:'sourcePointer',stableId:to.stableId});
await call({surface:'editor',action:'sourcePointer',stableId:to.stableId,visible:false});
assert(sourceViewport.visibleStartLine===Number(to.stableId.match(/:(\d+):\d+:\d+:\d+$/)[1]),'Code did not stop at requested top line');
await save('source-viewport-validation.json',sourceViewport);
await pause(1600);await save('scenario.json',{duration,row:41,voice:null,events});console.log(out);
