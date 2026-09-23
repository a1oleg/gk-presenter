import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {chromium} from '../../drawio-inspector/node_modules/playwright/index.mjs';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {parseDiagram} from '../../drawio-inspector/src/xml.mjs';
import {resolveViewer} from '../../drawio-inspector/src/render.mjs';
const out=process.argv[2];
const snapshot=JSON.parse(await fs.readFile(path.join(out,'sheet-source.json'),'utf8'));
const is18=snapshot.range.includes('A18:');
const is19=snapshot.range.includes('A19:');
const is20=snapshot.range.includes('A20:');
const source=snapshot.values[0][2]||(is18?'C:/GitHub/coldKode/graph/draw/FY-sequence.drawio':null);
const xml=await fs.readFile(source,'utf8');
// A scene-local annotation, not a persisted semantic annotation in the source graph.
const annotation='<mxCell id="presenter-wait" value="ожидание" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#b3b3b3;fontColor=#000000;fontSize=14;arcSize=15;" vertex="1" parent="1"><mxGeometry x="355" y="618" width="160" height="40" as="geometry"/></mxCell>';
let extra='';
if(is18||is19||is20){
 const old='C:/Users/a1ole/OneDrive/coldKode-presenter/output/scene-row019-1789539624179143600/annotated/source.drawio';
 const oldXml=await fs.readFile(old,'utf8');
 const label=oldXml.match(/id="snippet-random" label="([^"]+)"/)[1];
 extra=`<mxCell id="presenter-random" value="${label}" style="rounded=1;whiteSpace=wrap;html=0;fillColor=#f5f5f5;strokeColor=#b3b3b3;fontColor=#000000;fontSize=14;spacing=10;align=left;" vertex="1" parent="1"><mxGeometry x="785" y="752" width="430" height="110" as="geometry"/></mxCell>`;
 await fs.writeFile(path.join(out,'annotation-source.json'),JSON.stringify({file:old,cellId:'snippet-random',text:label},null,2));
}
let swap='';
if(is19||is20){
 const old='C:/Users/a1ole/OneDrive/coldKode-presenter/output/scene-row022-1789542834324742500/stage2/source.drawio';
 const label=(await fs.readFile(old,'utf8')).match(/id="snippet-swap" label="([^"]+)"/)[1];
 swap=`<mxCell id="presenter-swap" value="${label}" style="rounded=1;whiteSpace=wrap;html=0;fillColor=#f5f5f5;strokeColor=#b3b3b3;fontColor=#000000;fontSize=14;spacing=10;align=left;" vertex="1" parent="1"><mxGeometry x="935" y="1103" width="370" height="120" as="geometry"/></mxCell>`;
 await fs.writeFile(path.join(out,'swap-annotation-source.json'),JSON.stringify({file:old,cellId:'snippet-swap',text:label},null,2));
}
let shuffle=annotation;
if(is20){
 const old='C:/Users/a1ole/OneDrive/coldKode-presenter/output/scene-row022-1789542834324742500/stage2/source.drawio';
 const label=(await fs.readFile(old,'utf8')).match(/id="snippet-shuffle" label="([^"]+)"/)[1];
 shuffle=`<mxCell id="presenter-shuffle" value="${label}" style="rounded=1;whiteSpace=wrap;html=0;fillColor=#f5f5f5;strokeColor=#b3b3b3;fontColor=#000000;fontSize=14;spacing=10;align=left;" vertex="1" parent="1"><mxGeometry x="355" y="608" width="520" height="110" as="geometry"/></mxCell>`;
 await fs.writeFile(path.join(out,'shuffle-annotation-source.json'),JSON.stringify({file:old,cellId:'snippet-shuffle',text:label},null,2));
}
const steps=is20?[['1',735],['2',825]].map(([n,y])=>`<mxCell id="presenter-step-${n}" value="Шаг ${n}" style="rounded=1;whiteSpace=wrap;html=0;fillColor=#f5f5f5;strokeColor=#b3b3b3;fontColor=#000000;fontSize=14;spacing=10;" vertex="1" parent="1"><mxGeometry x="330" y="${y}" width="170" height="44" as="geometry"/></mxCell>`).join(''):'';
const staged=xml.replace('</root>',shuffle+extra+swap+steps+'</root>');
const stagedFile=path.join(out,'waiting.drawio');
await fs.writeFile(stagedFile,staged);await fs.writeFile(path.join(out,'source.drawio'),xml);
const client=new Client({name:'sequence-wait-check',version:'1'});
await client.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
try {
 const result=await client.callTool({name:'validate_geometry',arguments:{file:stagedFile,mode:'rendered',limit:500}});
 if(result.isError)throw Error(JSON.stringify(result.content));
 const report=result.structuredContent||JSON.parse(result.content[0].text);
 await fs.writeFile(path.join(out,'validate_geometry.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({findings:report.findings}));
 if(report.findings?.length)throw Error('Resolve geometry findings before rendering');
}finally{await client.close();}
const camera={x:110,y:598,width:1200,height:940,scale:1080/940};
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.route('**/*',r=>r.abort());
 const frames=[['before',(is18||is19||is20)?xml.replace('</root>',annotation+((is19||is20)?extra:'')+(is20?swap:'')+'</root>'):xml],['waiting',staged]];
 if(is20)frames.push(['steps',xml.replace('</root>',annotation+extra+swap+steps+'</root>')]);
 if(is18){const flow=await fs.readFile('C:/GitHub/coldKode/graph/draw/generated/Fisher-Yates.drawio','utf8');frames.push(['flow',flow]);await fs.writeFile(path.join(out,'flow.drawio'),flow);}
 for(const [name,content] of frames){
  await page.setContent('<body style="margin:0;background:white"><div id="g" style="width:1920px;height:1080px;overflow:hidden"></div></body>');
  await page.addScriptTag({path:await resolveViewer()});
  await page.evaluate(async({xml,camera})=>{
   const g=new Graph(document.getElementById('g'));g.setEnabled(false);
   const doc=mxUtils.parseXml(xml);new mxCodec(doc).decode(doc.documentElement,g.getModel());
   g.getView().scaleAndTranslate(camera.scale,-camera.x,-camera.y);g.getView().validate();
   await document.fonts.ready;
   await Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((resolve,reject)=>{const im=new Image();im.onload=resolve;im.onerror=reject;im.src=e.getAttribute('href')||e.getAttribute('xlink:href');})));
  },{xml:parseDiagram(content,0).modelXml,camera});
  if(is18){
   const geometry=await page.evaluate(()=>{const g=Graph.prototype;return [...document.querySelectorAll('#g svg')].length;});
   if(!geometry)throw Error('Diagram SVG missing');
  }
  await page.screenshot({path:path.join(out,name+'.png')});
 }
}finally{await browser.close();}
if(is18||is19||is20){
 execFileSync('C:/GitHub/coldKode-presenter/.venv/Scripts/python.exe',['C:/GitHub/coldKode-presenter/scripts/assemble_sequence_annotation.py',out],{stdio:'inherit',windowsHide:true});
 process.exit(0);
}
const result=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8'));
const a=result.normalized_alignment||result.alignment;
const text=a.characters.join('').toLowerCase();const needle='в таком случае';const index=text.indexOf(needle);
if(index<0||text.indexOf(needle,index+1)>=0)throw Error('Ambiguous speech cue');
const start=a.character_start_times_seconds[index];
const py='C:/GitHub/coldKode-presenter/.venv/Scripts/python.exe';
const duration=Number(execFileSync(py,['-c','import av,sys; m=av.open(sys.argv[1]);print(sum(f.samples/f.sample_rate for f in m.decode(audio=0)))',path.join(out,'speech.mp3')],{encoding:'utf8'}).trim());
const ff=execFileSync(py,['-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],{encoding:'utf8'}).trim();
const scenario={duration,source,camera,voice:'3.3',events:[{time:start,action:'show',cellId:'presenter-wait',text:'ожидание',cue:needle}],code:false};
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(scenario,null,2));
execFileSync(ff,['-hide_banner','-loglevel','error','-n','-loop','1','-framerate','30','-i',path.join(out,'before.png'),'-loop','1','-framerate','30','-i',path.join(out,'waiting.png'),'-i',path.join(out,'speech.mp3'),'-filter_complex',`[0:v][1:v]xfade=transition=fade:duration=0.2:offset=${start},format=yuv420p[v]`,'-map','[v]','-map','2:a','-t',String(duration),'-c:v','libx264','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart',path.join(out,'scene.mp4')],{windowsHide:true});
console.log(JSON.stringify({duration,start,video:path.join(out,'scene.mp4')}));
