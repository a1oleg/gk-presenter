import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';import {renderScene} from '../src/render-service.mjs';
const repo=fileURLToPath(new URL('../',import.meta.url)),cache=path.join(repo,'.cache/render-service');await fs.mkdir(cache,{recursive:true});
const tokenFile=path.join(cache,'token');let token;try{token=(await fs.readFile(tokenFile,'utf8')).trim();}catch{token=crypto.randomBytes(32).toString('hex');await fs.writeFile(tokenFile,token,{mode:0o600});}
const jobs=new Map(),queue=[];let running=false;
const publicJob=j=>({id:j.id,state:j.state,createdAt:j.createdAt,progress:j.progress,result:j.result,error:j.error});
const persist=j=>fs.writeFile(path.join(cache,j.id+'.json'),JSON.stringify(publicJob(j),null,2));
// Finished jobs remain inspectable after restart; active work is not silently
// resumed. A caller can explicitly submit an interrupted task again.
for(const name of await fs.readdir(cache))if(/^[a-f0-9-]{36}\.json$/.test(name)){
 const j=JSON.parse(await fs.readFile(path.join(cache,name),'utf8'));
 if(['queued','running'].includes(j.state)){j.state='interrupted';j.error='Service restarted before completion';}
 jobs.set(j.id,j);await persist(j);
}
async function pump(){if(running)return;running=true;try{while(queue.length){const j=queue.shift();if(j.state==='cancelled')continue;
 j.state='running';await persist(j);
 try{j.result=await renderScene({...j.input,signal:j.controller.signal,onProgress:p=>{j.progress=p;}});j.state='complete';}
 catch(e){j.state=j.controller.signal.aborted?'cancelled':'failed';j.error=e.message;}
 await persist(j);
}}finally{running=false;}}
const server=http.createServer(async(req,res)=>{
 const reply=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
 try{
  if(req.headers.origin)return reply(403,{error:'Browser-origin requests are disabled'});
  const url=new URL(req.url,'http://127.0.0.1');
  if(req.method==='GET'&&url.pathname==='/health'){
   let rendererReady=false;try{rendererReady=(await fetch('http://127.0.0.1:9031/render.html',{signal:AbortSignal.timeout(1500)})).ok;}catch{}
   return reply(200,{status:'ok',rendererReady,running,queued:queue.length});
  }
  if(req.headers.authorization!==`Bearer ${token}`)return reply(401,{error:'Local bearer token required'});
  const match=url.pathname.match(/^\/jobs\/([a-f0-9-]+)$/);
  if(match){const j=jobs.get(match[1]);if(!j)return reply(404,{error:'Unknown job'});
   if(req.method==='GET')return reply(200,publicJob(j));
   if(req.method==='DELETE'){
    if(['queued','running'].includes(j.state)){j.controller.abort();if(j.state==='queued')j.state='cancelled';await persist(j);}
    return reply(202,publicJob(j));
   }
  }
  if(req.method==='POST'&&['/render','/preview'].includes(url.pathname)){
   if(queue.length>=20)return reply(429,{error:'Queue full'});
   let body='';for await(const chunk of req){body+=chunk;if(body.length>65536)return reply(413,{error:'Request too large'});}
   const input=JSON.parse(body);if(typeof input.sceneDir!=='string')return reply(400,{error:'sceneDir required'});
   const j={id:crypto.randomUUID(),state:'queued',createdAt:new Date().toISOString(),controller:new AbortController(),input:{sceneDir:input.sceneDir,filename:input.filename,mode:url.pathname==='/preview'?'preview':'video',time:input.time??0}};
   jobs.set(j.id,j);queue.push(j);await persist(j);reply(202,publicJob(j));void pump();return;
  }
  reply(404,{error:'Unknown endpoint'});
 }catch(e){reply(400,{error:e.message});}
});
server.listen(9032,'127.0.0.1',()=>console.log('Render API: http://127.0.0.1:9032; token file: .cache/render-service/token'));
const shutdown=()=>{for(const j of jobs.values())j.controller?.abort();server.close();};
process.on('SIGINT',shutdown);process.on('SIGTERM',shutdown);
