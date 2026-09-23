// Reframe only the diagram; preserve the user's live code pane and divider.
import fs from 'node:fs/promises';
import path from 'node:path';
import {frameSheetScene} from '../../coldKode/dev/frameSheetScene.mjs';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
import {materialDir} from '../src/material-paths.mjs';
import {connectObs} from './obs_control.mjs';
const row=Number(process.argv[2]),file=process.argv[3];
const idx=await diagramIndex({file}),owner=idx.cells.find(c=>c.cellId==='f0-n1').stableId.replace(/:flow-start$/,'');
const plan=await frameSheetScene({row,file,functionStableId:owner,apply:false});
const base={functionStableId:owner};
const before=await bridge({...base,surface:'diagram',action:'presentRead',cellId:plan.upper.cellId,stableId:plan.upper.stableId});
const focused=await bridge({...plan.command,durationMs:0});
await bridge({...base,surface:'diagram',action:'presentPointer',cellId:plan.upper.cellId,stableId:plan.upper.stableId,pointerId:'narrator',visible:false});
await bridge({...base,surface:'editor',action:'sourcePointer',visible:false});
const checks=[];
for(const target of [plan.upper,plan.lower,plan.leftmost,plan.rightmost].filter(Boolean)){
 const state=await bridge({...base,surface:'diagram',action:'presentRead',cellId:target.cellId,stableId:target.stableId});
 if(!state.visible)throw Error('Boundary not visible: '+target.stableId);
 if(JSON.stringify(state.viewport)!==JSON.stringify(before.viewport))throw Error('User pane size changed');
 checks.push(state);
}
const out=path.join(materialDir(),`scene-row${row}-manual-preview-${Date.now()}`);await fs.mkdir(out);
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({plan,focused,checks,codeLayoutPreserved:true,lastCodeLine:plan.source.values[0][6]},null,2));
const obs=await connectObs();
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Recording active');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const item=(await obs.request('GetSceneItemList',{sceneName})).sceneItems.find(i=>i.sourceName==='VS Code OBS'&&i.sceneItemEnabled);
 if(!item||item.sceneItemTransform.scaleX!==1||item.sceneItemTransform.scaleY!==1||item.sceneItemTransform.sourceWidth!==1920)throw Error('Expected native 1920 capture at 1:1');
 const screenshot=path.join(out,'preview.png');
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:screenshot,imageWidth:1920,imageHeight:1080});
 console.log(JSON.stringify({screenshot,lastCodeLine:plan.source.values[0][6],checks}));
}finally{obs.close();}
