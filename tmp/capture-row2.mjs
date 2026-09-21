import fs from 'node:fs/promises';
import path from 'node:path';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],obs=await connectObs();
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Recording active');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const items=await obs.request('GetSceneItemList',{sceneName});
 const names=items.sceneItems.filter(x=>x.sceneItemEnabled).map(x=>x.sourceName).sort();
 if(JSON.stringify(names)!==JSON.stringify(['Google Slides OBS','VS Code OBS']))throw Error('Scene changed');
 const video=await obs.request('GetVideoSettings');
 if(video.baseWidth!==1600||video.baseHeight!==900)throw Error('Unexpected canvas');
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:path.join(out,'scene.png'),imageWidth:1600,imageHeight:900});
 await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({sceneName,...items,video,mode:'static-composite',transformsPreserved:true,stableId:'services/api/claude.ts:1051:5:1051:27',focus:'existing-user-prepared-scene',requestedScale:75},null,2));
}finally{obs.close();}
