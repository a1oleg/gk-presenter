import fs from 'node:fs/promises';
import path from 'node:path';
import {frameSheetScene} from '../../graphKoda/dev/frameSheetScene.mjs';
import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import {Client} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '../../drawio-inspector/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {materialDir} from '../src/material-paths.mjs';
import {connectObs} from './obs_control.mjs';

const row=Number(process.argv[2]),file=process.argv[3];
if(!row||!file)throw Error('Usage: preview_sheet_frame.mjs row diagramPath');
const index=await diagramIndex({file});
const owner=index.cells.find(c=>c.cellId==='f0-n1')?.stableId.replace(/:flow-start$/,'');
if(!owner)throw Error('Missing function root');
const plan=await frameSheetScene({row,file,functionStableId:owner,apply:false});
if(process.argv[4]!==undefined)plan.command.topPadding=Number(process.argv[4]);
const values=plan.source.values[0],column=re=>plan.headers.findIndex(h=>re.test(h.trim().toLowerCase()));
const start=String(values[column(/начало кода/)]||'').replace(/^stableId:\s*/i,'').replace(/:flow-start$/,'').trim();
const end=String(values[column(/конец кода/)]||'').replace(/^stableId:\s*/i,'').replace(/:end$/,'').trim();
const placement=String(values[column(/^код$/)]||'').trim()==='снизу'?'BELOW':'RIGHT';
if(['снизу','справа'].includes(String(values[column(/^код$/)]||'').trim())&&!start)throw Error('Code requested but start-of-code column is missing or empty');
let editorAreaHeight;
if(end&&placement==='BELOW'){
 const obs=await connectObs();try{
  const {currentProgramSceneName:sceneName}=await obs.request('GetCurrentProgramScene');
  const {sceneItems}=await obs.request('GetSceneItemList',{sceneName});
  const capture=sceneItems.find(i=>i.sourceName==='VS Code OBS'&&i.sceneItemEnabled);
  if(!capture||capture.sceneItemTransform.sourceHeight<200)throw Error('Presentation capture has no measured height');
  editorAreaHeight=capture.sceneItemTransform.sourceHeight-72;
 }finally{obs.close();}
}
const opened=start?await bridge({surface:'editor',action:'openSource',filePath:file,functionStableId:owner,stableId:start,endStableId:end||undefined,editorAreaHeight,placement}):null;
if(!start)await bridge({surface:'editor',action:'openDiagram',filePath:file,functionStableId:owner});
const focused=await bridge({...plan.command,durationMs:0});
const out=path.join(materialDir(),`scene-row${row}-preview-${Date.now()}`);await fs.mkdir(out);
const client=new Client({name:'scene-frame-check',version:'1'});
await client.connect(new StdioClientTransport({command:'node',args:['C:/GitHub/drawio-inspector/src/mcp.mjs']}));
const checks=[];
try{
 for(const target of [plan.upper,plan.lower,plan.leftmost,plan.rightmost].filter(Boolean)){
  const r=await client.callTool({name:'inspect_element',arguments:{file:index.file,cellId:target.cellId,mode:'xml'}});
  if(r.isError)throw Error(JSON.stringify(r.content));
  const live=await bridge({surface:'diagram',action:'presentRead',functionStableId:owner,stableId:target.stableId,cellId:target.cellId});
  checks.push(live);
 }
}finally{await client.close();}
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({source:plan.source,command:plan.command,code:{start,end,placement,opened,editorAreaHeight},focused,checks},null,2));
if(checks.some(c=>!c.visible))throw Error('Framing clips a requested boundary; see '+out);
const obs=await connectObs();
try{
 const {currentProgramSceneName:scene}=await obs.request('GetCurrentProgramScene');
 const screenshot=path.join(out,'preview.png');
 await obs.request('SaveSourceScreenshot',{sourceName:scene,imageFormat:'png',imageFilePath:screenshot,imageWidth:1920,imageHeight:1080});
 console.log(JSON.stringify({screenshot,checks},null,2));
}finally{obs.close();}
