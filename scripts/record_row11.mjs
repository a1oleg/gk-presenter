import {materialDir} from '../src/material-paths.mjs';
import fs from 'node:fs/promises';
import {connectObs} from './obs_control.mjs';
import {execFileSync} from 'node:child_process';
const currentRun=process.argv.includes('--current');
const latest=currentRun?JSON.parse(await fs.readFile('C:/GitHub/coldKode/tmp/fisher-yates/runtime/latest.json','utf8')):null;
const out = `${materialDir('output')}/interactive-row${currentRun?'012':'011'}-${Date.now()}`;
await fs.mkdir(out);
const token = (await fs.readFile('C:/GitHub/coldKode/tmp/graph-demo-token.local','utf8')).trim();
const functionStableId = currentRun?latest.root:'examples/fisher-yates/src/shuffle.ts:6:7:36:1';
const sleep = ms => new Promise(resolve=>setTimeout(resolve,ms));
const events=[];
let startedAt;
function pointer(...args) { execFileSync('powershell',['-NoProfile','-File','scripts/demo_pointer.ps1',...args],{windowsHide:true}); }
async function demo(input) {
  const response=await fetch('http://127.0.0.1:17843/demo/step',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({functionStableId,...input}),signal:AbortSignal.timeout(20000)});
  const result=await response.json();
  events.push({time:(performance.now()-startedAt)/1000,input,result});
  if (!response.ok) throw new Error(JSON.stringify(result));
  console.log(JSON.stringify({input,result}));
  return result;
}
const obs=await connectObs();let owned=false;
try {
  if ((await obs.request('GetRecordStatus')).outputActive) throw new Error('OBS already recording; leaving it untouched');
  await demo({surface:'diagram',action:'dismissMenu'});
  events.length=0;
  await obs.request('StartRecord');owned=true;startedAt=performance.now();
  console.log('RECORDING='+out);
  if(!process.argv.includes('--tail')) {
  await sleep(2500);
  const menu=await demo({surface:'diagram',action:'contextMenu',cellId:'f0-n4'});
  const label=menu.items.find(item=>item==='показать статистику Цикла');
  if(!label)throw new Error('Statistics item missing');
  await sleep(400);
  pointer('-Action','scroll','-X','500','-Y','690','-Ticks','8');
  events.push({time:(performance.now()-startedAt)/1000,input:{action:'menuScrolled'}});
  pointer('-Action','move','-X','470','-Y','904');
  await sleep(750);
  await demo({surface:'diagram',action:'menuClick',label});
  await demo({surface:'runtime',action:'waitForAnalysis',...(currentRun?{sessionId:latest.sessionId}:{})});
  }
  await sleep(800);
  pointer('-Action','drag','-X','1000','-Y','570','-TargetX',currentRun?'605':'720','-TargetY','570');
  events.push({time:(performance.now()-startedAt)/1000,input:{action:'panelExpanded'}});
  pointer('-Action','move','-X','1740','-Y','950');
  await sleep(22000);
} finally {
  if(owned){const stopped=await obs.request('StopRecord');await fs.writeFile(out+'/recording.json',JSON.stringify({output:out,...stopped,events},null,2));console.log(JSON.stringify(stopped));}
  obs.close();
}
