import {materialDir} from '../src/material-paths.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=path.join(materialDir('output'),`reference-frame-${Date.now()}`);await fs.mkdir(out);
const obs=await connectObs();
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Recording active');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 const item=sceneItems.find(x=>x.sourceName==='VS Code OBS');
 if(item.sceneItemTransform.sourceWidth!==1920||item.sceneItemTransform.sourceHeight!==1032)throw Error('Unexpected source frame');
 await fs.writeFile(path.join(out,'obs-before.json'),JSON.stringify(item,null,2));
 const focus=await bridge({functionStableId:'services/api/claude.ts:1022:0:2911:1',surface:'diagram',action:'presentFocus',stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9',includeAnnotations:true,scale:1.1});
 await obs.request('SetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId,sceneItemTransform:{cropTop:132,cropBottom:0,cropLeft:5,cropRight:315,positionX:0,positionY:0,scaleX:1,scaleY:1,boundsType:'OBS_BOUNDS_NONE',alignment:5}});
 await new Promise(r=>setTimeout(r,700));
 const file=path.join(out,'obs-frame.png');
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:file,imageWidth:1600,imageHeight:900});
 await fs.writeFile(path.join(out,'framing.json'),JSON.stringify({focus,file,reference:'user screenshot',effectiveScale:1.1},null,2));
 console.log(JSON.stringify({file,focus}));
}finally{obs.close();}
