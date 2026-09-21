import fs from 'node:fs/promises';
import {connectObs} from '../scripts/obs_control.mjs';
const obs=await connectObs();
try {
  if((await obs.request('GetRecordStatus')).outputActive || (await obs.request('GetStreamStatus')).outputActive)throw Error('Recording or stream active; transform not changed');
  const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
  const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
  const matches=sceneItems.filter(s=>s.sourceName==='VS Code OBS');
  if(matches.length!==1)throw Error('Ambiguous source');
  const item=matches[0];
  await fs.writeFile(new URL('./obs-vscode-transform-before.json',import.meta.url),JSON.stringify({sceneName,item},null,2));
  await obs.request('SetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId,sceneItemTransform:{
    positionX:0,positionY:0,rotation:0,alignment:5,
    boundsType:'OBS_BOUNDS_SCALE_OUTER',boundsAlignment:0,boundsWidth:1600,boundsHeight:900,cropToBounds:true,
    scaleX:1,scaleY:1,
  }});
  const result=await obs.request('GetSceneItemTransform',{sceneName,sceneItemId:item.sceneItemId});
  const t=result.sceneItemTransform;
  if(t.boundsWidth!==1600||t.boundsHeight!==900||!t.cropToBounds||t.boundsType!=='OBS_BOUNDS_SCALE_OUTER'||Math.abs(t.scaleX-t.scaleY)>0.0001)throw Error('Transform verification failed');
  console.log(JSON.stringify({sceneName,source:item.sourceName,transform:t}));
} finally {obs.close();}
