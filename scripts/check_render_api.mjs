import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {materialDir} from '../src/material-paths.mjs';
const sceneDir=path.join(materialDir(),'fisher-sequence-A1-N9-1790063462428402500');
const token=(await fs.readFile('.cache/render-service/token','utf8')).trim(),base='http://127.0.0.1:9032';
async function call(method,url,body){const r=await fetch(base+url,{method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});assert(r.ok);return r.json();}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function terminal(id){for(let i=0;i<600;i++){const j=await call('GET','/jobs/'+id);if(['complete','failed','cancelled'].includes(j.state))return j;if(i%5===0)console.log(JSON.stringify({state:j.state,progress:j.progress}));await delay(500);}throw Error('Job timeout');}
assert.equal((await fetch(base+'/render',{method:'POST',body:'{}'})).status,401);
assert.equal((await fetch(base+'/health',{headers:{Origin:'https://example.com'}})).status,403);
const health=await call('GET','/health');assert(health.rendererReady);
const suffix=Date.now();
const cancelledName=`cancel-test-${suffix}.mp4`;
const cancel=await call('POST','/render',{sceneDir,filename:cancelledName});
const queued=await call('POST','/preview',{sceneDir,time:1,filename:`cancel-preview-${suffix}.png`});
await call('DELETE','/jobs/'+queued.id);assert.equal((await terminal(queued.id)).state,'cancelled');
for(let i=0;i<50;i++){const j=await call('GET','/jobs/'+cancel.id);if(j.progress?.frames>0)break;await delay(100);}
await call('DELETE','/jobs/'+cancel.id);assert.equal((await terminal(cancel.id)).state,'cancelled');
await assert.rejects(fs.access(path.join(sceneDir,cancelledName)));
const bad=await call('POST','/preview',{sceneDir:path.resolve('.'),time:0});assert.equal((await terminal(bad.id)).state,'failed');
const pngBefore=(await fs.readdir(sceneDir,{recursive:true})).filter(n=>n.endsWith('.png')).length;
const job=await call('POST','/render',{sceneDir,filename:`scene-stream-${suffix}.mp4`});const result=await terminal(job.id);assert.equal(result.state,'complete',result.error);
const pngAfter=(await fs.readdir(sceneDir,{recursive:true})).filter(n=>n.endsWith('.png')).length;assert.equal(pngAfter,pngBefore);
const report={health,unauthorizedRejected:true,browserOriginRejected:true,cancelQueued:true,cancelRunning:true,outsideRootRejected:true,pngBefore,pngAfter,result};
await fs.writeFile('.cache/render-service/integration-check.json',JSON.stringify(report,null,2));console.log(JSON.stringify({artifact:result.result.artifact,checks:'passed',pngDelta:pngAfter-pngBefore}));
