import {materialDir} from '../src/material-paths.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {connectObs} from '../scripts/obs_control.mjs';
const out=path.join(materialDir('output'),`scale-check-${Date.now()}`);
await fs.mkdir(out,{recursive:true});
const obs=await connectObs();
try {
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const file=path.join(out,'obs-frame.png');
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:file,imageWidth:1600,imageHeight:900});
 console.log(file);
}finally{obs.close();}
