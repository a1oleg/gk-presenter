import fs from 'node:fs/promises';import path from 'node:path';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from './obs_control.mjs';
import {materialDir} from '../src/material-paths.mjs';
const out=path.resolve(process.argv[2]),read=async f=>JSON.parse(await fs.readFile(f,'utf8'));
const request=await read(path.join(out,'request.json')),alignment=(await read(path.join(out,'alignment.json'))).alignment;
const text=alignment.characters.join(''),time=phrase=>{const i=text.indexOf(phrase);if(i<0)throw Error('Missing narration cue: '+phrase);return alignment.character_start_times_seconds[i];};
const file='graph/draw/generated/Fisher-Yates.drawio',idx=await diagramIndex({file}),owner=idx.cells.find(c=>c.cellId==='f0-n1').stableId.replace(/:flow-start$/,'');
const cues=[['Рассмотрим','f2-n1','39:0:42:1'],['Сначала по индексу','f2-n6','40:28:40:44'],['виртуальной переменной','f2-n4','40:28:40:44'],['будет записана','f2-n2','40:2:40:24'],['актуальный индекс','f2-n3','40:11:40:24'],['А то, что было','f2-n9','41:21:41:34'],['записывается на место','f2-n7','41:2:41:17'],['буквы поменялись','f2-n11','41:2:41:35']].map(([phrase,cellId,range])=>({time:time(phrase),cellId,stableId:idx.cells.find(c=>c.cellId===cellId).stableId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:'+range}));
const template=await read(path.join(materialDir(),'fisher-sequence-A1-N9-1790063462428402500/scenario.json'));
const values={alphabet:['А','Б','В','Г','Д','Е','Ё','Ж'],current:{index:7,value:'Ж'},random:6};
const changes=[];const add=phrase=>changes.push({time:time(phrase),values:structuredClone(values)});
values.alphabet[7]='Ё';add('то есть в самый конец');values.alphabet[6]='Ж';add('Таким образом');values.random=null;add('другое значение');values.current.index=6;add('сократится на один');changes.sort((a,b)=>a.time-b.time);
const duration=alignment.character_end_times_seconds.at(-1)+.7;
const scenario={kind:'captions',duration,voiceNote:'3.3',captions:{...template.captions,rect:{x:80,y:0,width:1240,height:96},values:{alphabet:['А','Б','В','Г','Д','Е','Ё','Ж'],current:{index:7,value:'Ж'},random:6}},captionEvents:changes};
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(scenario,null,2),{flag:'wx'});
const camera=()=>bridge({surface:'diagram',action:'presentRead',functionStableId:owner,cellId:'f2-n1',stableId:idx.cells.find(c=>c.cellId==='f2-n1').stableId});
const before=await camera(),events=[],obs=await connectObs();let owned=false,recording;
const move=async cue=>{const diagram=await bridge({surface:'diagram',action:'presentPointer',functionStableId:owner,...cue,pointerId:'narrator',durationMs:250});const code=await bridge({surface:'editor',action:'sourcePointer',functionStableId:owner,stableId:cue.sourceStableId});return {diagram,code};};
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('OBS already recording');
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});if(!settings.inputSettings.window.includes('coldKode PRESENTATION'))throw Error('Wrong capture window');
 await move(cues[0]);await obs.request('StartRecord');owned=true;const started=performance.now();
 for(const cue of cues){const delay=cue.time*1000-(performance.now()-started);if(delay>0)await new Promise(r=>setTimeout(r,delay));events.push({...cue,result:await move(cue)});console.log('Cue: '+cue.cellId);}
 const remaining=duration*1000-(performance.now()-started);if(remaining>0)await new Promise(r=>setTimeout(r,remaining));
}finally{if(owned)recording=await obs.request('StopRecord');obs.close();}
if(!recording)throw Error('No recording');
await new Promise(r=>setTimeout(r,1200));const target=path.join(out,'recording'+path.extname(recording.outputPath));await fs.copyFile(recording.outputPath,target);
const after=await camera();if(JSON.stringify(before.camera)!==JSON.stringify(after.camera))throw Error('Camera changed during recording');
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({recording:target,events,cameraBefore:before,cameraAfter:after,source:file,sourceDigest:idx.digest},null,2));console.log(JSON.stringify({out,duration,events:events.length}));
