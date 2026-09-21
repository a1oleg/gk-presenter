import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge} from '../../coldKode/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],base={functionStableId:'services/api/claude.ts:1022:0:2911:1',surface:'diagram',stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9'};
let hidden=await bridge({...base,action:'presentPointer',visible:false});
if(hidden.stage!=='pointer-hidden'){
 // Compatibility with the already-open plugin: park the pointer above the recorded viewport without moving the camera.
 hidden=await bridge({...base,action:'presentPointer',stableId:'services/api/claude.ts:1034:4:1034:62',cellId:'f0-n10',durationMs:0});
 hidden={...hidden,mode:'outside-recorded-viewport'};
}
const view=await bridge({...base,action:'presentRead'});
if(Math.abs(view.camera.scale-1.1)>.001)throw Error('Scene scale changed');
const obs=await connectObs();
try{
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const items=await obs.request('GetSceneItemList',{sceneName});
 const enabled=items.sceneItems.filter(x=>x.sceneItemEnabled);
 if(enabled.length!==1||enabled[0].sourceName!=='VS Code OBS'||enabled[0].sceneItemTransform.sourceWidth<=0)throw Error('OBS scene unavailable');
 const settings=await obs.request('GetInputSettings',{inputName:'VS Code OBS'});
 if(!settings.inputSettings.window.includes('coldKode PRESENTATION'))throw Error('Wrong capture window');
 await new Promise(r=>setTimeout(r,400));
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:path.join(out,'scene.png'),imageWidth:1600,imageHeight:900});
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({sceneName,view,items,hidden,framePreserved:true},null,2));
}finally{obs.close();}
