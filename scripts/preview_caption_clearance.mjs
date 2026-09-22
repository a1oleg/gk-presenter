import {materialDir} from '../src/material-paths.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
const original=path.resolve(process.argv[2]);
const s=JSON.parse(await fs.readFile(path.join(original,'scenario.json'),'utf8'));
const prep=JSON.parse(await fs.readFile(path.join(original,'scene-preparation.json'),'utf8'));
const c=prep.cameraBefore.camera;
const client=new Client({name:'caption-clearance',version:'1'});
await client.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
try{
 const result=await client.callTool({name:'inspect_element',arguments:{file:'C:/GitHub/coldKode/graph/draw/generated/Fisher-Yates.drawio',mode:'xml',cellId:'f0-n5'}});
 if(result.isError)throw Error(JSON.stringify(result));
 const data=JSON.parse(result.content[0].text),node=data.elements[0];
 if(data.digest!==prep.diagramHash)throw Error('Diagram changed since recording; cannot safely reuse frame');
 const edgeResult=await client.callTool({name:'inspect_element',arguments:{file:data.file,mode:'xml',cellId:'f0-e24'}});
 if(edgeResult.isError)throw Error(JSON.stringify(edgeResult));
 const edge=JSON.parse(edgeResult.content[0].text).elements[0];
 const right=(Math.max(node.bounds.x+node.bounds.width,...edge.xmlWaypoints.map(p=>p.x))+c.translate.x)*c.scale-c.scrollLeft+16;
 const previousX=s.captions.rect.x;s.captions.rect.x=Math.ceil(right+34);
 s.captions.design='compact';s.captions.rect.width=1240;
 if(s.captions.rect.x+s.captions.rect.width>1896)throw Error('Caption exceeds frame');
 const out=path.join(materialDir('output'),`caption-clearance-${Date.now()}`);await fs.mkdir(out);
 await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(s,null,2));
 await fs.writeFile(path.join(out,'clearance.json'),JSON.stringify({previousX,x:s.captions.rect.x,nodeRight:right,gap:s.captions.rect.x-right,recording:path.resolve(prep.recording),original,geometrySource:'drawio-inspector MCP'},null,2));
 console.log(out);
}finally{await client.close();}
