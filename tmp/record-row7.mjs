import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],fn='examples/fisher-yates/src/shuffle.ts:6:7:33:1';
const a=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment,text=a.characters.join('');
const cues=[
 {anchor:'Это будет алгоритм',cellId:'f0-n1',stableId:fn+':flow-start',sourceStableId:'examples/fisher-yates/src/shuffle.ts:5:16:5:23'},
 {anchor:'В начале корневой функции',cellId:'f0-n1',stableId:fn+':flow-start',sourceStableId:'examples/fisher-yates/src/shuffle.ts:5:16:5:23'},
 {anchor:'создадим массив',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'первых восьми букв',cellId:'f0-n2',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:19:10:57'},
 {anchor:'Массив отображается',cellId:'f0-n2-part-1',text:'alphabet',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'Открытый штабель',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:2:10:16'},
 {anchor:'первое появление переменной',cellId:'f0-n2-part-1',text:'alphabet',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'тут она создаётся',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:2:10:16'}
].map(c=>{const i=text.indexOf(c.anchor);if(i<0)throw Error(c.anchor);return {...c,time:a.character_start_times_seconds[i]};});
const send=(c)=>bridge({surface:'diagram',action:'presentPointer',functionStableId:fn,stableId:c.stableId,cellId:c.cellId,...(c.text?{text:c.text}:{}),durationMs:650});
const code=(c)=>bridge({surface:'editor',action:'sourcePointer',functionStableId:fn,stableId:c.sourceStableId});
const obs=await connectObs();let active=false;
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Already recording');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const items=await obs.request('GetSceneItemList',{sceneName});const item=items.sceneItems.find(x=>x.sourceName==='VS Code OBS');
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});
 const windows=await obs.request('GetInputPropertiesListPropertyItems',{inputName:'VS Code OBS',propertyName:'window'});
 if(!windows.propertyItems.some(x=>x.itemEnabled&&x.itemValue===settings.inputSettings.window&&x.itemName.includes('coldKode PRESENTATION')))throw Error('Presentation window unavailable');
 const {sourceWidth:w,sourceHeight:h}=item.sceneItemTransform;if(w!==1920||h!==1032)throw Error('Unexpected source size');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify(items,null,2));
 const s=item.sceneItemTransform.scaleX;
 const cameraBefore=await bridge({surface:'diagram',action:'presentRead',functionStableId:fn,stableId:cues[0].stableId,cellId:cues[0].cellId});
 for(const x of items.sceneItems)await obs.request('SetSceneItemEnabled',{sceneName,sceneItemId:x.sceneItemId,sceneItemEnabled:x.sceneItemId===item.sceneItemId});
 // Validate all source ranges before recording; do not incur a failed take halfway through.
 for(const c of cues)await code(c);
 await code(cues[0]);await send(cues[0]);
 await obs.request('StartRecord');active=true;const start=performance.now(),events=[];
 for(const c of cues){await new Promise(r=>setTimeout(r,Math.max(0,c.time*1000-(performance.now()-start))));events.push({...c,diagram:await send(c),code:await code(c)});}
 const duration=a.character_end_times_seconds.at(-1)+.8;
 await new Promise(r=>setTimeout(r,Math.max(0,duration*1000-(performance.now()-start))));
 const result=await obs.request('StopRecord');active=false;await new Promise(r=>setTimeout(r,1500));
 const recording=path.join(out,'recording'+path.extname(result.outputPath));await fs.copyFile(result.outputPath,recording);
 const cameraAfter=await bridge({surface:'diagram',action:'presentRead',functionStableId:fn,stableId:cues[0].stableId,cellId:cues[0].cellId});
 if(JSON.stringify(cameraAfter.camera)!==JSON.stringify(cameraBefore.camera))throw Error('Camera changed');
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({recording,events,cameraBefore,cameraAfter,framingPreserved:true,layout:'RIGHT 50/50',diagram:'graph/draw/generated/Fisher-Yates.drawio',effectiveDiagramScale:cameraBefore.camera.scale*s,scroll:false},null,2));
 console.log('RECORDING_READY');
}finally{if(active)await obs.request('StopRecord');obs.close();}
