import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {frameSheetScene} from '../../graphKoda/dev/frameSheetScene.mjs';
import {bridge} from '../../graphKoda/graph/presentation/presentation.mjs';
import {materialDir} from './material-paths.mjs';

const codeRoot=fileURLToPath(new URL('../../graphKoda/',import.meta.url));
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const save=(file,value)=>fs.writeFile(file,JSON.stringify(value,null,2),{flag:'wx'});
async function outputDirectory(directory){
  const root=await fs.realpath(materialDir());
  const target=path.resolve(directory);
  const relative=path.relative(root,target);
  if(!relative||relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative))throw Error('Scene directory must be inside configured materials/output');
  await fs.mkdir(target,{recursive:true});
  const real=await fs.realpath(target);
  const check=path.relative(root,real);
  if(check==='..'||check.startsWith('..'+path.sep)||path.isAbsolute(check))throw Error('Scene directory resolves outside materials');
  return real;
}

export async function prepareScene({row,spreadsheetId,sheet,diagram,functionStableId,sessionFile,output}){
  const out=await outputDirectory(output);
  const planFile=path.join(out,'scene-preparation.json');
  try{await fs.access(planFile);throw Error('Scene already prepared; use apply/check or a new output directory');}catch(error){if(error.code!=='ENOENT')throw error;}
  const file=path.resolve(codeRoot,diagram);
  const run=sessionFile?await read(path.resolve(sessionFile)):null;
  const owner=functionStableId||run?.root;
  if(!owner)throw Error('Specify functionStableId or a runtime session file');
  if(run&&run.root!==owner)throw Error('Runtime function differs from scene function');
  const framing=await frameSheetScene({row,spreadsheetId,sheet,file,functionStableId:owner,apply:false});
  const values=framing.source.values[0];
  const resolution=/^(\d+)\s*[x×]\s*(\d+)$/.exec(values[1]||'');
  if(!resolution)throw Error('B must contain a canvas size such as 1920x1080');
  const source=await fs.readFile(file);
  const plan={version:1,kind:'live-diagram',createdAt:new Date().toISOString(),source:file,sha256:digest(source),
    functionStableId:owner,sessionId:run?.sessionId||null,
    sheet:{spreadsheetId:framing.source.spreadsheetId,range:framing.source.range,row},
    canvas:{width:Number(resolution[1]),height:Number(resolution[2]),fps:30},
    diagram:{file,top:framing.upper.stableId,bottom:framing.lower.stableId,rightmost:values[7]||null},
    pointer:values[4],voice:values[11],code:values[3],captions:values[9],interactive:values[10],
    upper:framing.upper,lower:framing.lower,rightmost:framing.rightmost,command:framing.command,padding:16};
  await save(path.join(out,'scene-sheet-source.json'),framing.source);
  await fs.writeFile(path.join(out,'source.drawio'),source,{flag:'wx'});
  if(run)await save(path.join(out,'runtime-session.json'),run);
  await save(planFile,plan);
  return {output:out,...plan};
}

export async function loadPreparedScene(directory){
  const out=await outputDirectory(directory);
  const plan=await read(path.join(out,'scene-preparation.json'));
  if(plan.version!==1||plan.kind!=='live-diagram')throw Error('Unsupported scene preparation');
  if(digest(await fs.readFile(plan.source))!==plan.sha256)throw Error('Diagram changed after scene preparation');
  if(plan.sessionId){const run=await read(path.join(out,'runtime-session.json'));if(run.sessionId!==plan.sessionId||run.root!==plan.functionStableId)throw Error('Prepared runtime session changed');}
  return {out,plan};
}

export async function checkPreparedScene(directory){
  const {out,plan}=await loadPreparedScene(directory);
  const frames={};
  for(const key of ['upper','lower',...(plan.rightmost?['rightmost']:[])]){
    const target=plan[key];
    frames[key]=await bridge({surface:'diagram',action:'presentRead',functionStableId:plan.functionStableId,stableId:target.stableId,cellId:target.cellId});
  }
  const upper=frames.upper,lower=frames.lower;
  const topGap=upper.screenBounds.y;
  const bottomGap=lower.viewport.height-lower.screenBounds.y-lower.screenBounds.height;
  const report={checkedAt:new Date().toISOString(),sha256:plan.sha256,frames,topGap,bottomGap,
    passed:upper.visible&&lower.visible&&(!frames.rightmost||frames.rightmost.visible)&&Math.abs(topGap-plan.padding)<2&&Math.abs(bottomGap-plan.padding)<2};
  await fs.writeFile(path.join(out,'screen-geometry.json'),JSON.stringify(report,null,2));
  if(!report.passed)throw Error(`Framing failed: upper ${topGap}px, lower ${bottomGap}px; inspect screen-geometry.json`);
  return report;
}

export async function applyPreparedScene(directory){
  const {plan}=await loadPreparedScene(directory);
  await bridge({surface:'editor',action:'openDiagram',filePath:plan.source,functionStableId:plan.functionStableId});
  await bridge(plan.command);
  await new Promise(resolve=>setTimeout(resolve,500));
  return checkPreparedScene(directory);
}
