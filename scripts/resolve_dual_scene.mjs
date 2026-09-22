import fs from 'node:fs/promises';
import path from 'node:path';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
const out=path.resolve(process.argv[2]),s=JSON.parse(await fs.readFile(path.join(out,'scenario.json'),'utf8'));
const file=path.resolve('../coldKode',s.diagram.file),idx=await diagramIndex({file:s.diagram.file});
const client=new Client({name:'dual-scene-layout',version:'1.0'});
await client.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
try{
 const inspect=async selector=>{const r=await client.callTool({name:'inspect_element',arguments:{file,mode:'xml',...selector}});if(r.isError)throw Error(JSON.stringify(r));return JSON.parse(r.content.find(c=>c.type==='text').text).elements;};
 const pick=nodes=>nodes.filter(n=>n.kind==='vertex').sort((a,b)=>b.bounds.width*b.bounds.height-a.bounds.width*a.bounds.height)[0];
 const top=pick(await inspect({stableId:s.diagram.top})),bottom=pick(await inspect({stableId:s.diagram.bottom}));
 // Explicit migration for this user-approved coordinate change, not fuzzy binding.
 const migrations={'examples/fisher-yates/src/shuffle.ts:35:16:35:50:horizontal-owner-examples/fisher-yates/src/shuffle.ts-34-0-37-1':'examples/fisher-yates/src/shuffle.ts:35:22:35:56:horizontal-owner-examples/fisher-yates/src/shuffle.ts-34-0-37-1'};
 const rightId=migrations[s.diagram.rightmost]||s.diagram.rightmost,right=pick(await inspect({stableId:rightId}));
 if(!top||!bottom||!right)throw Error('Missing diagram framing selector');
 const fn=idx.cells.find(c=>c.cellId==='f0-n1').stableId.replace(/:flow-start$/,'');
 const call=(action,extra={})=>bridge({surface:'diagram',action,functionStableId:fn,stableId:s.diagram.top,cellId:top.cellId,...extra});
 const probe=await call('presentFocus',{scale:1,durationMs:0});
 const span=bottom.bounds.y+bottom.bounds.height-top.bounds.y;
 await call('presentFocus',{scale:(probe.viewport.height-64)/span,durationMs:0});
 const current=await call('presentRead'),c=current.camera;
 // Native diagram origin maps into this established OBS capture at (16,90).
 const project=b=>({x:(b.x+c.translate.x)*c.scale-c.scrollLeft+16,y:(b.y+c.translate.y)*c.scale-c.scrollTop+90,width:b.width*c.scale,height:b.height*c.scale});
 const t=project(top.bounds),b=project(bottom.bounds),r=project(right.bounds);
 const codeLeft=Math.ceil(r.x+r.width+32);
 if(codeLeft>1450||codeLeft<500||b.y+b.height>990)throw Error('Framing leaves insufficient code room or clips the bottom node');
 s.diagram.resolvedRightmost=rightId;s.diagram.camera=current;s.diagram.geometry={top:t,bottom:b,rightmost:r};
 s.code.source=JSON.parse(await fs.readFile(path.join(out,'code-source.json'),'utf8'));
 s.code.rect={x:codeLeft,y:90,width:1920-codeLeft,height:900};
 s.captions.rect={x:Math.ceil(t.x+t.width+100),y:Math.ceil(t.y-8),width:1480,height:96};
 // Clear all actual nodes intersecting the caption's vertical band, not only
 // its anchor (a predicate below `for` can project into the same band).
 const nearbyResult=await client.callTool({name:'inspect_region',arguments:{file,mode:'xml',cellId:top.cellId,padding:180,limit:500}});
 if(nearbyResult.isError)throw Error(JSON.stringify(nearbyResult));
 const nearby=JSON.parse(nearbyResult.content.find(c=>c.type==='text').text);
 const blockers=nearby.elements.filter(n=>n.kind==='vertex'&&/^f\d+-n\d+(?:-part-\d+)?$/.test(n.cellId)).map(n=>project(n.bounds)).filter(n=>n.y<s.captions.rect.y+96+10&&n.y+n.height>s.captions.rect.y-10);
 s.captions.rect.x=Math.ceil(Math.max(s.captions.rect.x,...blockers.map(n=>n.x+n.width+34)));
 const routesResult=await client.callTool({name:'inspect_region',arguments:{file,mode:'xml',cellId:top.cellId,padding:1200,limit:500}});
 if(routesResult.isError)throw Error(JSON.stringify(routesResult));
 const repeats=JSON.parse(routesResult.content.find(c=>c.type==='text').text).elements.filter(n=>n.kind==='edge'&&n.edgeType==='REPEATS');
 const routeRight=repeats.flatMap(n=>(n.xmlWaypoints||[]).map(p=>(p.x+c.translate.x)*c.scale-c.scrollLeft+16));
 if(routeRight.length){s.captions.design='compact';s.captions.rect.width=1240;s.captions.rect.x=Math.ceil(Math.max(s.captions.rect.x,...routeRight.map(x=>x+34)));}
 if(s.captions.rect.x+s.captions.rect.width>1896)throw Error('Caption overflow');
 s.code.contentY=s.captions.rect.y+s.captions.rect.height+40;
 const longest=Math.max(...s.code.source.code.split('\n').map(l=>l.length));
 s.code.fontSize=Math.min(26,Math.floor((s.code.rect.width-90)/(longest*.56)));
 if(s.code.fontSize<18)throw Error('Code would become unreadable');
 s.code.layout={safe:true,method:'rightmost-node + 32px; code below caption + 40px',fontSize:s.code.fontSize};
 const a=JSON.parse(await fs.readFile(path.join(out,'alignment.json'),'utf8')).alignment,text=a.characters.join('');
 for(const e of s.events){const i=text.indexOf(e.atWord);if(i<0)throw Error('Narration cue missing');e.time=a.character_start_times_seconds[i];}
 await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(s,null,2));
 await fs.writeFile(path.join(out,'layout-check.json'),JSON.stringify({geometrySource:'drawio-inspector MCP',diagram:s.diagram,code:s.code.rect,fontSize:s.code.fontSize,captions:s.captions.rect},null,2));
 console.log(JSON.stringify({code:s.code.rect,fontSize:s.code.fontSize,diagram:s.diagram.geometry,captions:s.captions.rect}));
}finally{await client.close();}
