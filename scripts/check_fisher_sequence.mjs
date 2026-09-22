import fs from 'node:fs/promises';import path from 'node:path';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
const out=path.resolve(process.argv[2]);const s=JSON.parse(await fs.readFile(path.join(out,'scenario.json'),'utf8'));
const prep=JSON.parse(await fs.readFile(path.join(out,'scene-preparation.json'),'utf8')),camera=prep.cameraBefore.camera;
const c=new Client({name:'fisher-sequence-check',version:'1'});await c.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
try{
 const r=await c.callTool({name:'inspect_region',arguments:{file:prep.diagram,mode:'xml',cellId:'f0-n4',padding:1300,limit:500}});
 if(r.isError)throw Error(JSON.stringify(r));const data=JSON.parse(r.content[0].text);
 if(data.digest!==prep.diagramHash)throw Error('Diagram changed since recording');
 const checks=[];
 for(const id of new Set(s.events.map(e=>e.diagramCell))){const n=data.elements.find(e=>e.cellId===id);if(!n)throw Error('Missing '+id);
 const b=n.bounds,x=(b.x+camera.translate.x)*camera.scale-camera.scrollLeft+16,y=(b.y+camera.translate.y)*camera.scale-camera.scrollTop+90,w=b.width*camera.scale,h=b.height*camera.scale;
 if(x<0||y<90||x+w>s.code.rect.x||y+h>990)throw Error('Pointer target clipped: '+id);
 const title=s.captions.rect;if(x<title.x+title.width&&x+w>title.x&&y<title.y+title.height&&y+h>title.y)throw Error('Caption covers pointer target: '+id);
 checks.push({cellId:id,x,y,width:w,height:h});}
 const repeat=data.elements.find(e=>e.cellId==='f0-e24');const edgeRight=Math.max(...repeat.xmlWaypoints.map(p=>(p.x+camera.translate.x)*camera.scale-camera.scrollLeft+16));
 if(s.captions.rect.x-edgeRight<24)throw Error('Repeat/caption gap too small');
 if(prep.events.length!==s.events.length)throw Error('Missing recorded cue');
 await fs.writeFile(path.join(out,'sequence-check.json'),JSON.stringify({geometrySource:'drawio-inspector MCP',targets:checks,repeatGap:s.captions.rect.x-edgeRight,paragraphs:s.paragraphs.length,pointerEvents:prep.events.length,captionChanges:s.captionEvents.length},null,2));
 console.log(JSON.stringify({targets:checks.length,repeatGap:s.captions.rect.x-edgeRight,paragraphs:s.paragraphs.length,pointerEvents:prep.events.length}));
}finally{await c.close();}
