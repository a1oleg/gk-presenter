import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],fn='examples/fisher-yates/src/shuffle.ts:6:7:33:1';
const a=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment,text=a.characters.join('');
const setId='examples/fisher-yates/src/shuffle.ts:11:8:11:16';
const idx=await diagramIndex({file:'graph/draw/generated/Fisher-Yates.drawio'});
const lines=(await fs.readFile('C:/GitHub/coldKode/examples/fisher-yates/src/shuffle.ts','utf8')).split(/\r?\n/);
function cue(anchor,cellId,line,token){const col=lines[line-1].indexOf(token);if(col<0)throw Error('Source token missing');const cell=idx.cells.find(c=>c.cellId===cellId);if(!cell)throw Error('Diagram target missing');return {anchor,cellId,stableId:cell.stableId,sourceStableId:`examples/fisher-yates/src/shuffle.ts:${line}:${col}:${line}:${col+token.length}`};}
const currentCues=[
 cue('Следующим шагом','f0-n3-part-1',16,'current'),
 cue('открытой коробкой','f0-n3-part-1',16,'let'),
 cue('Внутрь присваиваем объект','f0-n17',17,'{'),
 cue('В поле index','f0-n19-part-1',17,'index'),
 cue('вычитая 1','f0-n19-part-4',17,'- 1'),
 cue('А поле value','f0-n20',18,'undefined'),
 cue('length — это','f0-n19-part-2',17,'length'),
 cue('тему подсветки','f0-n19-part-2',17,'length')
];
const virtualCues=[
 {anchor:'Ниже по диагонали',cellId:'f0-n2-part-2',stableId:setId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:17:10:18'},
 {anchor:'Косая штриховка',cellId:'f0-n2-part-2',text:'set(',stableId:setId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:17:10:18'},
 {anchor:'будем называть',cellId:'f0-n2-part-2',stableId:setId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:17:10:18'},
 {anchor:'операцию присваивания',cellId:'f0-n2-part-2',text:'set(',stableId:setId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:17:10:18'},
 {anchor:'виртуальный метод set',cellId:'f0-n2-part-2',stableId:setId,sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:17:10:18'}
];
const loopMode=process.argv.includes('--loop');
const loopCues=[cue('Перейдём','f0-n4',25,'for'),cue('Условные ветвления','f0-n5',25,'current.index > 0'),{...cue('тру','f0-n5',25,'current.index > 0'),cellId:'f0-e9',text:'true'},{...cue('фолс','f0-n5',25,'current.index > 0'),cellId:'f0-e10',text:'false'},cue('на каждой итерации','f0-n5-part-2',25,'current.index'),cue('не достигнут','f0-n5-part-4',25,'0'),{...cue('уйдёт влево','f0-n5',25,'current.index > 0'),cellId:'f0-e10',text:'false'}];
const cues=(loopMode?loopCues:process.argv.includes('--current')?currentCues:process.argv.includes('--virtual-set')?virtualCues:[
 {anchor:'Это будет алгоритм',cellId:'f0-n1',stableId:fn+':flow-start',sourceStableId:'examples/fisher-yates/src/shuffle.ts:5:16:5:23'},
 {anchor:'В начале корневой функции',cellId:'f0-n1',stableId:fn+':flow-start',sourceStableId:'examples/fisher-yates/src/shuffle.ts:5:16:5:23'},
 {anchor:'создадим массив',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'первых восьми букв',cellId:'f0-n2',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:19:10:57'},
 {anchor:'Массив отображается',cellId:'f0-n2-part-1',text:'alphabet',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'Открытый штабель',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:2:10:16'},
 {anchor:'первое появление переменной',cellId:'f0-n2-part-1',text:'alphabet',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:8:10:16'},
 {anchor:'тут она создаётся',cellId:'f0-n2-part-1',stableId:'examples/fisher-yates/src/shuffle.ts:11:8:11:16',sourceStableId:'examples/fisher-yates/src/shuffle.ts:10:2:10:16'}
]).map(c=>{let i=text.indexOf(c.anchor);while(i>=0&&((i>0&&/[\p{L}\p{N}]/u.test(text[i-1]))||/[\p{L}\p{N}]/u.test(text[i+c.anchor.length]||'')))i=text.indexOf(c.anchor,i+1);if(i<0)throw Error(c.anchor);return {...c,time:a.character_start_times_seconds[i]};});
for(let i=1;i<cues.length;i++)if(cues[i].time<cues[i-1].time)throw Error('Narration cues are out of order');
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
 await code(cues[0]);if(!loopMode)await send(cues[0]);
 await obs.request('StartRecord');active=true;const start=performance.now(),events=[];
 let synchronizedFocus;
 if(loopMode){
   const source=await bridge({surface:'editor',action:'openSource',functionStableId:fn,filePath:'graph/draw/generated/Fisher-Yates.drawio',stableId:cues[0].sourceStableId,previousStableId:'examples/fisher-yates/src/shuffle.ts:5:0:32:1',placement:'RIGHT'});
   const diagram=await bridge({surface:'diagram',action:'presentFocus',functionStableId:fn,stableId:cues[0].stableId,cellId:'f0-n4',previousStableId:fn+':flow-start',durationMs:1200,scale:cameraBefore.camera.scale});
   synchronizedFocus={source,diagram};
 }
 for(const c of cues){await new Promise(r=>setTimeout(r,Math.max(0,c.time*1000-(performance.now()-start))));events.push({...c,diagram:await send(c),code:await code(c)});}
 const duration=a.character_end_times_seconds.at(-1)+.8;
 await new Promise(r=>setTimeout(r,Math.max(0,duration*1000-(performance.now()-start))));
 const result=await obs.request('StopRecord');active=false;await new Promise(r=>setTimeout(r,1500));
 const recording=path.join(out,'recording'+path.extname(result.outputPath));await fs.copyFile(result.outputPath,recording);
 const cameraAfter=await bridge({surface:'diagram',action:'presentRead',functionStableId:fn,stableId:cues[0].stableId,cellId:cues[0].cellId});
 if(!loopMode&&JSON.stringify(cameraAfter.camera)!==JSON.stringify(cameraBefore.camera))throw Error('Camera changed');
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({recording,events,cameraBefore,cameraAfter,synchronizedFocus,framingPreserved:true,layout:'RIGHT 50/50',diagram:'graph/draw/generated/Fisher-Yates.drawio',effectiveDiagramScale:cameraBefore.camera.scale*s,scroll:loopMode},null,2));
 console.log('RECORDING_READY');
}catch(error){console.error(error);throw error;}finally{if(active)await obs.request('StopRecord').catch(e=>console.error('Stop cleanup:',e.message));obs.close();}
