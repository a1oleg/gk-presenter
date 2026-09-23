import {bridge} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const base={functionStableId:'services/api/claude.ts:1022:0:2911:1'};
console.log(await bridge({...base,surface:'editor',action:'openDiagram',filePath:'graph/draw/generated/queryModel.drawio'}));
const obs=await connectObs();
try{
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 const item=sceneItems.find(i=>i.sourceName==='VS Code OBS'),t=item.sceneItemTransform;
 const scale=.75/t.scaleX;
 console.log(await bridge({...base,surface:'diagram',action:'presentFocus',stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9',includeAnnotations:true,scale}));
 console.log({diagramScale:scale,obsScale:t.scaleX,outputScale:scale*t.scaleX});
}finally{obs.close();}
