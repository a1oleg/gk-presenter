import {materialDir} from '../src/material-paths.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {connectObs} from '../scripts/obs_control.mjs';
const file='C:/GitHub/graphKoda/graph/draw/generated/Fisher-Yates.drawio';
const upper=process.argv[2],lower=process.argv[3];
const out=path.join(materialDir('output'),`range-preview-${Date.now()}`);await fs.mkdir(out);
const client=new Client({name:'presenter-range-preview',version:'1.0'});
await client.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
async function inspect(selector){const r=await client.callTool({name:'inspect_element',arguments:{file,mode:'xml',...selector}});if(r.isError)throw Error(JSON.stringify(r));return JSON.parse(r.content.find(c=>c.type==='text').text);}
try{
 const top=await inspect({stableId:upper}),bottom=await inspect({stableId:lower});
 const topNode=top.elements.find(c=>c.kind==='vertex');
 const bottomNodes=bottom.elements.filter(c=>c.kind==='vertex');
 if(!topNode||!bottomNodes.length)throw Error('Range endpoints missing');
 // Use the upper row as the horizontal anchor, retaining its small top inset.
 const row=(await inspect({cellId:topNode.parent})).elements[0];
 const bottomY=Math.max(...bottomNodes.map(c=>c.bounds.y+c.bounds.height));
 if(bottomY<=row.bounds.y)throw Error('Reversed range');
 const idx=await diagramIndex({file:'graph/draw/generated/Fisher-Yates.drawio'});
 const fn=idx.cells.find(c=>c.cellId==='f0-n1').stableId.replace(/:flow-start$/,'');
 const send=(extra)=>bridge({surface:'diagram',action:'presentFocus',functionStableId:fn,stableId:upper,cellId:topNode.cellId,...extra});
 const read=()=>bridge({surface:'diagram',action:'presentRead',functionStableId:fn,stableId:upper,cellId:topNode.cellId});
 const before=await read();
 // The current API anchors at the top node; get actual viewport without guessing.
 const probe=await send({scale:before.camera.scale,durationMs:0});
 const span=bottomY-topNode.bounds.y;
 const scale=(probe.viewport.height-64)/span;
 if(scale<.1||scale>4)throw Error('Requested range outside supported scale');
 const focused=await send({scale,durationMs:400});
 const after=await read();
 const bottomScreenY=(bottomY+after.camera.translate.y)*after.camera.scale-after.camera.scrollTop;
 const topScreenY=(topNode.bounds.y+after.camera.translate.y)*after.camera.scale-after.camera.scrollTop;
 if(topScreenY<0||bottomScreenY>focused.viewport.height)throw Error('Range is clipped');
 const obs=await connectObs();let screenshot;
 try{
  const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
  const scene=await obs.request('GetSceneItemList',{sceneName});
  const item=scene.sceneItems.find(c=>c.sourceName==='VS Code OBS');
  if(!item?.sceneItemEnabled||item.sceneItemTransform.sourceWidth!==1920||item.sceneItemTransform.sourceHeight!==1032)throw Error('Capture window is not full size');
  await new Promise(r=>setTimeout(r,500));screenshot=path.join(out,'preview.png');
  await obs.request('SaveSourceScreenshot',{sourceName:sceneName,imageFormat:'png',imageFilePath:screenshot,imageWidth:1920,imageHeight:1080});
 }finally{obs.close();}
 const report={upper,lower,before,after,scale,topScreenY,bottomScreenY,viewport:focused.viewport,screenshot,geometrySource:'drawio-inspector MCP',codeUnchanged:true};
 await fs.writeFile(path.join(out,'framing.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await client.close();}
