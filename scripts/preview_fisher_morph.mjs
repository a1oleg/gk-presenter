import fs from 'node:fs/promises';import path from 'node:path';import {execFileSync} from 'node:child_process';
import {chromium} from '../../drawio-inspector/node_modules/playwright/index.mjs';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {parseDiagram} from '../../drawio-inspector/src/xml.mjs';
import {resolveViewer} from '../../drawio-inspector/src/render.mjs';
import {materialDir} from '../src/material-paths.mjs';
const files=['C:/GitHub/graphKoda/graph/draw/generated/Fisher-Yates.drawio','C:/GitHub/graphKoda/graph/draw/FY-sequence.drawio'];
const out=path.join(materialDir(),`fisher-flow-sequence-${Date.now()}`);await fs.mkdir(out);
const c=new Client({name:'fisher-morph-check',version:'1'});await c.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
const reports=[];let anchors;
try{
 const inspect=async(file,cellId)=>{const r=await c.callTool({name:'inspect_element',arguments:{file,cellId,mode:'rendered'}});if(r.isError)throw Error(JSON.stringify(r.content));return (r.structuredContent||JSON.parse(r.content[0].text)).elements[0];};
 anchors=[];
 for(const [flowId,sequenceId] of [['f0-n5','c8'],['f1-n1','c10'],['f2-n1','c14']]){
  const f=await inspect(files[0],flowId),s=await inspect(files[1],sequenceId);
  const dx=(f.bounds.x+f.bounds.width/2)-(s.bounds.x+s.bounds.width/2);
  const dy=sequenceId==='c8'?f.bounds.y-(s.bounds.y+s.bounds.height):(f.bounds.y+f.bounds.height/2)-(s.bounds.y+s.bounds.height/2);
  if(Math.abs(dx)>.05||(sequenceId==='c8'?Math.abs(dy-12)>.05:Math.abs(dy)>.05))throw Error('Axis/header alignment failed');
  anchors.push({flowId,sequenceId,dx,dy});
 }
 const result=await c.callTool({name:'validate_geometry',arguments:{file:files[1],mode:'rendered',limit:500}});if(result.isError)throw Error(JSON.stringify(result.content));
 reports.push(result.structuredContent||JSON.parse(result.content[0].text));
}finally{await c.close();}
await fs.writeFile(path.join(out,'alignment-check.json'),JSON.stringify({anchors,reports},null,2));
// One world coordinate system and one camera for BOTH diagrams: no fit per page.
const camera={x:110,y:598,width:1200,height:940,scale:1};
camera.scale=Math.min(1920/camera.width,1080/camera.height);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.route('**/*',r=>r.abort());
 for(let i=0;i<files.length;i++){
  await page.setContent('<body style="margin:0;background:white"><div id="g" style="width:1920px;height:1080px;overflow:hidden"></div></body>');
  await page.addScriptTag({path:await resolveViewer()});
  const xml=await fs.readFile(files[i],'utf8');
  await page.evaluate(async({xml,camera})=>{
   const g=new Graph(document.getElementById('g'));g.setEnabled(false);
   new mxCodec(mxUtils.parseXml(xml)).decode(mxUtils.parseXml(xml).documentElement,g.getModel());
   g.getView().scaleAndTranslate(camera.scale,-camera.x,-camera.y);g.getView().validate();
   await document.fonts.ready;await Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((resolve,reject)=>{const im=new Image();im.onload=resolve;im.onerror=reject;im.src=e.getAttribute('href')||e.getAttribute('xlink:href');})));
  },{xml:parseDiagram(xml,0).modelXml,camera});
  await page.screenshot({path:path.join(out,i?'sequence.png':'flow.png')});
 }
}finally{await browser.close();}
const ff=execFileSync('C:/GitHub/graphKoda-presenter/.venv/Scripts/python.exe',['-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],{encoding:'utf8'}).trim();
execFileSync(ff,['-hide_banner','-loglevel','error','-n','-loop','1','-framerate','30','-t','4','-i',path.join(out,'flow.png'),'-loop','1','-framerate','30','-t','4','-i',path.join(out,'sequence.png'),'-filter_complex','[0:v][1:v]xfade=transition=fade:duration=2:offset=2,format=yuv420p[v]','-map','[v]','-t','6','-c:v','libx264','-crf','18',path.join(out,'transition.mp4')],{windowsHide:true});
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify({files,camera,anchors,transition:{kind:'fade',start:2,duration:2,total:6}},null,2));
console.log(JSON.stringify({out,anchors,findings:reports[0].findings}));
