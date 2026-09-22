import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn,execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {chromium} from '../../drawio-inspector/node_modules/playwright/index.mjs';
import {materialDir} from './material-paths.mjs';
const repo=fileURLToPath(new URL('../',import.meta.url));
const ffmpeg=()=>execFileSync(path.join(repo,'.venv/Scripts/python.exe'),['-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],{encoding:'utf8'}).trim();
const json=async file=>JSON.parse((await fs.readFile(file,'utf8')).replace(/^\uFEFF/,''));
function checkAbort(signal){if(signal?.aborted)throw new Error('Render cancelled');}

// PNG is an in-memory transport. Awaited writes apply backpressure; no frame
// sequence or transparent intermediate movie is written to disk.
export async function renderScene({sceneDir,mode='video',time=0,filename,signal,onProgress=()=>{}}){
 if(!['video','preview'].includes(mode))throw Error('Invalid render mode');
 const root=await fs.realpath(materialDir()),out=await fs.realpath(sceneDir);
 if(!out.toLowerCase().startsWith(root.toLowerCase()+path.sep))throw Error('Scene outside material output');
 const scene=await json(path.join(out,'scenario.json'));
 if(!Number.isFinite(scene.duration)||scene.duration<=0||scene.duration>3600)throw Error('Invalid scene duration');
 if(!Number.isFinite(time)||time<0||time>=scene.duration)throw Error('Preview time outside scene');
 const name=filename||(mode==='video'?'scene.mp4':`preview-${Math.round(time*1000)}.png`);
 if(path.basename(name)!==name||!name.endsWith(mode==='video'?'.mp4':'.png'))throw Error('Invalid output filename');
 const destination=path.join(out,name);
 try{await fs.access(destination);throw Error('Output already exists; choose a new filename');}catch(e){if(e.code!=='ENOENT')throw e;}
 const prep=await json(path.join(out,'scene-preparation.json')),recording=await fs.realpath(prep.recording);
 if(!recording.toLowerCase().startsWith(root.toLowerCase()+path.sep))throw Error('Recording outside material output');
 let speech;
 if(mode==='video'){speech=path.join(out,'speech.wav');try{await fs.access(speech);}catch{speech=path.join(out,'speech.mp3');await fs.access(speech);}}
 checkAbort(signal);
 const scratch=await fs.mkdtemp(path.join(os.tmpdir(),'coldkode-render-'));
 const partial=path.join(scratch,name);let browser,encoder,stderr='',sent=0,rendered=0,encoderError;
 const abort=()=>{encoder?.kill();void browser?.close().catch(()=>{});};signal?.addEventListener('abort',abort,{once:true});
 try{
  const args=['-nostdin','-n','-hide_banner','-loglevel','error'];
  if(mode==='preview')args.push('-ss',String(time));
  args.push('-i',recording,'-f','image2pipe','-framerate','30','-vcodec','png','-i','pipe:0');
  if(speech)args.push('-i',speech);
  args.push('-filter_complex','[0:v]fps=30,setsar=1[v];[v][1:v]overlay=0:0:format=auto[out]','-map','[out]');
  if(mode==='video')args.push('-map','2:a','-af','apad','-t',String(scene.duration),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart');
  else args.push('-frames:v','1','-update','1');
  args.push(partial);
  encoder=spawn(ffmpeg(),args,{windowsHide:true,stdio:['pipe','ignore','pipe']});
  encoder.stderr.on('data',b=>{stderr=(stderr+b.toString()).slice(-6000);});encoder.stdin.on('error',e=>{encoderError=e;});
  const finished=new Promise((resolve,reject)=>{encoder.once('error',reject);encoder.once('close',code=>code===0?resolve():reject(Error(`FFmpeg exit ${code}: ${stderr}`)));});
  finished.catch(e=>{encoderError=e;});
  browser=await chromium.launch({channel:'chrome',headless:true});checkAbort(signal);
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.exposeFunction('emitFrame',async(frame,data)=>{
   checkAbort(signal);rendered++;if(mode==='preview'&&sent)return;if(encoderError)throw encoderError;
   await new Promise((resolve,reject)=>encoder.stdin.write(Buffer.from(data.split(',')[1],'base64'),e=>e?reject(e):resolve()));
   sent++;onProgress({frames:sent,total:mode==='preview'?1:Math.ceil(scene.duration*30),phase:'rendering'});
  });
  await page.goto('http://127.0.0.1:9031/render.html');
  await page.waitForFunction(()=>typeof window.renderCaptions==='function',null,{timeout:30000});
  await page.evaluate(({scene,mode,time})=>window.renderCaptions(scene,mode==='preview'?{start:time,end:Math.min(scene.duration,time+1/30)}:{}),{scene,mode,time});
  if(errors.length)throw Error(errors.join('\n'));
  if(sent<(mode==='preview'?1:Math.floor(scene.duration*30)))throw Error('Too few rendered frames');
  encoder.stdin.end();onProgress({frames:sent,phase:'encoding'});await finished;checkAbort(signal);
  if((await fs.stat(partial)).size===0)throw Error('Empty render');
  await fs.copyFile(partial,destination,1); // COPYFILE_EXCL protects existing files.
  const report={artifact:destination,mode,time:mode==='preview'?time:null,duration:mode==='video'?scene.duration:null,frames:sent,renderedFrames:rendered,intermediatePngFiles:0,transport:'Motion Canvas -> bounded pipe -> FFmpeg',codeLayout:await page.evaluate(()=>window.codeLayoutReport||null)};
  await fs.writeFile(path.join(out,name+'.render.json'),JSON.stringify(report,null,2));return report;
 }finally{
  signal?.removeEventListener('abort',abort);encoder?.kill();await browser?.close().catch(()=>{});
  // Only the private mkdtemp directory is removed, never a caller-supplied path.
  await fs.rm(scratch,{recursive:true,force:true,maxRetries:3,retryDelay:200});
 }
}
