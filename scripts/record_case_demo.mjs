import fs from 'node:fs/promises';
import {connectObs} from './obs_control.mjs';
import {execFileSync} from 'node:child_process';
const latest=JSON.parse(await fs.readFile('C:/GitHub/coldKode/tmp/fisher-yates/runtime/latest.json','utf8'));
const token=(await fs.readFile('C:/GitHub/coldKode/tmp/graph-demo-token.local','utf8')).trim();
const out=`C:/GitHub/coldKode-presenter/output/interactive-row014-${Date.now()}`;await fs.mkdir(out);
let started=performance.now();const events=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function demo(action,index){const input={surface:'runtime',action,index,functionStableId:latest.root,sessionId:latest.sessionId};const response=await fetch('http://127.0.0.1:17843/demo/step',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(input),signal:AbortSignal.timeout(20000)});const result=await response.json();if(!response.ok)throw new Error(JSON.stringify(result));events.push({time:(performance.now()-started)/1000,input,result});console.log(JSON.stringify({action,index,result}));}
const obs=await connectObs();let owned=false;
try{
 if((await obs.request('GetRecordStatus')).outputActive)throw new Error('OBS already recording');
 await demo('waitForAnalysis');await demo('selectAll');events.length=0;await sleep(600);
 await obs.request('StartRecord');owned=true;started=performance.now();console.log('RECORDING='+out);
 await sleep(3500);
 for(const index of [0,1,3,6,7]){
  // Positions are relative to the verified 1920x1032 VS Code window.
  execFileSync('powershell',['-NoProfile','-File','scripts/demo_pointer.ps1','-Action','move','-X','850','-Y',String(Math.round(119+(516+43.4*index-104)/.872093))],{windowsHide:true});
  await demo('selectCase',index);await sleep(index===7?14000:2800);
 }
}finally{if(owned){const stop=await obs.request('StopRecord');await fs.writeFile(out+'/recording.json',JSON.stringify({output:out,...stop,sessionId:latest.sessionId,events},null,2));console.log(JSON.stringify(stop));}obs.close();}
