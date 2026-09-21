import {connectObs} from '../scripts/obs_control.mjs';
const obs=await connectObs();
try {
 const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
 await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:'C:/GitHub/coldKode-presenter/tmp/row2-preview.png',imageWidth:1600,imageHeight:900});
 console.log(await fetch('http://127.0.0.1:17844/health').then(r=>r.json()));
}finally{obs.close();}
