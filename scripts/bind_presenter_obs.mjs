// Bind only an exact, live presentation window. Never fall back to another Code window.
import fs from 'node:fs/promises';
import path from 'node:path';
import {connectObs} from './obs_control.mjs';
const obs=await connectObs();
try {
 if((await obs.request('GetRecordStatus')).outputActive)throw Error('Cannot rebind during recording');
 const health=await fetch('http://127.0.0.1:17844/health').then(r=>r.json());
 if(health.presentationWindow!==true)throw Error('Presentation bridge is not ready');
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
 const requestedName=process.argv[2];
 const enabled=sceneItems.filter(i=>i.inputKind==='window_capture'&&(requestedName?i.sourceName===requestedName:i.sceneItemEnabled));
 if(enabled.length!==1)throw Error('Expected exactly one enabled window capture; select it in OBS first');
 const inputName=enabled[0].sourceName;
 const {propertyItems}=await obs.request('GetInputPropertiesListPropertyItems',{inputName,propertyName:'window'});
 const windows=propertyItems.filter(i=>i.itemEnabled&&i.itemName.includes('coldKode PRESENTATION'));
 if(windows.length!==1)throw Error('Expected exactly one live coldKode PRESENTATION window');
 const original=await obs.request('GetInputSettings',{inputName});
 const out=path.resolve('output',`obs-presentation-${Date.now()}`);await fs.mkdir(out,{recursive:true});
 await fs.writeFile(path.join(out,'previous-settings.json'),JSON.stringify({sceneName,inputName,...original,sceneItem:enabled[0]},null,2));
 await obs.request('SetInputSettings',{inputName,inputSettings:{window:windows[0].itemValue,priority:0},overlay:true});
 const after=await obs.request('GetInputSettings',{inputName});
 if(after.inputSettings.window!==windows[0].itemValue||after.inputSettings.priority!==0)throw Error('OBS binding verification failed');
 console.log(JSON.stringify({sceneName,inputName,window:windows[0].itemName,exactTitle:true,backup:out}));
}finally{obs.close()}
