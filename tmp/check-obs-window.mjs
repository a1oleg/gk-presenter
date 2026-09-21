import {connectObs} from '../scripts/obs_control.mjs';
const obs=await connectObs();
try{
 console.log(JSON.stringify(await obs.request('GetInputSettings',{inputName:'VS Code OBS'})));
 console.log(JSON.stringify(await obs.request('GetInputPropertiesListPropertyItems',{inputName:'VS Code OBS',propertyName:'window'})));
 console.log(JSON.stringify(await obs.request('GetSceneList')));
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 console.log(JSON.stringify(await obs.request('GetSceneItemList',{sceneName})));
}finally{obs.close();}
