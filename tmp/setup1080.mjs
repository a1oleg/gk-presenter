import fs from 'node:fs/promises';
import path from 'node:path';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],obs=await connectObs();
try{
 if((await obs.request('GetRecordStatus')).outputActive||(await obs.request('GetStreamStatus')).outputActive)throw Error('OBS output active');
 const video=await obs.request('GetVideoSettings');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const items=await obs.request('GetSceneItemList',{sceneName}),item=items.sceneItems.find(x=>x.sourceName==='VS Code OBS');
 if(item.sceneItemTransform.sourceWidth!==1920)throw Error('Unexpected source width');
 await fs.writeFile(path.join(out,'obs1080-before.json'),JSON.stringify({video,sceneName,items},null,2));
 await obs.request('SetVideoSettings',{baseWidth:1920,baseHeight:1080,outputWidth:1920,outputHeight:1080});
 const t=item.sceneItemTransform,visibleHeight=t.sourceHeight-t.cropTop-t.cropBottom;
 await obs.request('SetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId,sceneItemTransform:{scaleX:1,scaleY:1,positionX:0,positionY:(1080-visibleHeight)/2,boundsType:'OBS_BOUNDS_NONE',alignment:5}});
 const after=await obs.request('GetVideoSettings');if(after.outputWidth!==1920||after.outputHeight!==1080)throw Error('Video setting mismatch');
 console.log(JSON.stringify({video:after,sourceScale:1,paddingTop:(1080-visibleHeight)/2}));
}finally{obs.close();}
