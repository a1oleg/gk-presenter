import fs from 'node:fs/promises';
import path from 'node:path';
import {bridge} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const out=process.argv[2],row=Number(process.argv[3]),base={functionStableId:'services/api/claude.ts:1022:0:2911:1'};
if(row===2){
 await bridge({...base,surface:'editor',action:'openDiagram',filePath:'graph/draw/generated/queryModel.drawio'});
 await bridge({...base,surface:'diagram',action:'presentFocus',stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9',scale:1.1,includeAnnotations:true});
}
const hide=await bridge({...base,surface:'diagram',action:'presentPointer',stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9',visible:false});
if(hide.stage!=='pointer-hidden')throw Error('Pointer hide unavailable');
const obs=await connectObs();
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Recording active');
 const v=await obs.request('GetVideoSettings');if(v.outputWidth!==1920||v.outputHeight!==1080)throw Error('Expected 1080p');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const items=await obs.request('GetSceneItemList',{sceneName});
 for(const item of items.sceneItems){
  const enabled=item.sourceName==='VS Code OBS'||row===2&&item.sourceName==='Google Slides OBS';
  if(enabled&&item.sceneItemTransform.sourceWidth<=0)throw Error('Source not available: '+item.sourceName);
  await obs.request('SetSceneItemEnabled',{sceneName,sceneItemId:item.sceneItemId,sceneItemEnabled:enabled});
 }
 await new Promise(r=>setTimeout(r,500));
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:path.join(out,'scene.png'),imageWidth:1920,imageHeight:1080});
 await fs.writeFile(path.join(out,'capture.json'),JSON.stringify({row,video:v,sceneName,items,hide},null,2));
}finally{obs.close();}
