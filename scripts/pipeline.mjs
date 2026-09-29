import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {materialDir} from '../src/material-paths.mjs';
import {semanticSnapshot} from '../src/semantic-snapshot.mjs';
import {resolveCues} from '../src/pipeline-plan.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const {values:v}=parseArgs({options:{plan:{type:'string'},'prepare-only':{type:'boolean',default:false}}});
if(!v.plan)throw Error('Usage: npm run pipeline -- --plan plan.json [--prepare-only]');
const input=fs.realpathSync(v.plan),base=path.dirname(input);
const read=f=>JSON.parse(fs.readFileSync(f,'utf8').replace(/^\uFEFF/,''));
const plan=read(input);
if(plan.version!==1||typeof plan.title!=='string'||!plan.title.trim())throw Error('Plan version 1 and title required');
const local=f=>{if(typeof f!=='string'||!f)throw Error('Local path required');return fs.realpathSync(path.resolve(base,f));};
const diagram=local(plan.diagram?.file),code=local(plan.code?.file),semanticRoot=local(plan.code?.semanticRoot),font=local(plan.font);
const duration=plan.durationSeconds;
if(!Number.isFinite(duration)||duration<=0||duration>3600)throw Error('durationSeconds must be in (0,3600]');
if(!Array.isArray(plan.diagram.cellIds)||!plan.diagram.cellIds.length||!plan.diagram.cellIds.every(id=>typeof id==='string'&&id))throw Error('Explicit diagram.cellIds required');
const audio=plan.audio?local(plan.audio.file):null;
const alignmentFile=plan.audio?.alignment?local(plan.audio.alignment):null;
const alignment=alignmentFile?read(alignmentFile):null;
const narrationFile=plan.audio?.narration?local(plan.audio.narration):null;
if(alignmentFile&&!narrationFile)throw Error('Audio alignment requires narration file to guard stale text');
if(narrationFile&&((alignment?.alignment||alignment)?.characters||[]).join('')!==fs.readFileSync(narrationFile,'utf8').replace(/^\uFEFF/,''))throw Error('Alignment differs from narration file');
const events=resolveCues(plan.events||[],alignment,duration);
const originalFiles=[input,diagram,code,font,...[audio,alignmentFile,narrationFile].filter(Boolean),path.join(semanticRoot,'classify.js'),path.join(semanticRoot,'extension.js')];
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const hashes=Object.fromEntries(originalFiles.map(f=>[f,sha(f)]));
const snapshot=semanticSnapshot({file:code,semanticRoot,lines:plan.code.lines});
if(events.some(e=>!snapshot.lineMap.includes(e.codeLine)))throw Error('Cue codeLine is outside selected source lines');
const out=fs.mkdtempSync(path.join(materialDir(),'pipeline-'));
const save=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2));
const report={version:1,title:plan.title,status:'preparing',output:out,sourceHashes:hashes,stages:[]};
function stage(name,callback){report.currentStage=name;save('pipeline-report.json',report);callback();report.stages.push(name);save('pipeline-report.json',report);}
function execute(command,args,env={}){
  const result=spawnSync(command,args,{cwd:root,encoding:'utf8',env:{...process.env,PYTHONUTF8:'1',...env},maxBuffer:16*1024*1024});
  if(result.error)throw result.error;
  if(result.status!==0)throw Error(`${path.basename(args[0]||command)} failed: ${result.stderr||result.stdout}`);
  return result.stdout;
}
console.log('Pipeline: '+out);
try{
  save('plan-source.json',plan);save('code-source.json',snapshot);
  const diagramOut=path.join(out,'diagram');fs.mkdirSync(diagramOut);
  fs.copyFileSync(diagram,path.join(diagramOut,'source.drawio'));
  save('fragment.json',{cellIds:plan.diagram.cellIds});
  stage('diagram-export',()=>execute(process.execPath,[path.join(root,'scripts/render_drawio_scene.mjs'),diagramOut,plan.diagram.cellIds[0]],{PRESENTER_FRAGMENT:path.join(out,'fragment.json'),PRESENTER_TIGHT_EXPORT:'1',PRESENTER_SCALE:'1.5',PRESENTER_SHEET_BOUNDS:'0',PRESENTER_REVEAL_PLAN:''}));
  const composition={canvas:plan.canvas,durationSeconds:duration,tracks:plan.tracks,font,
    diagramImage:path.join(diagramOut,'scene.png'),diagramGeometry:path.join(diagramOut,'screen-geometry.json'),codeSnapshot:path.join(out,'code-source.json'),
    minimumDiagramScale:plan.diagram.minimumScale??0.75,minimumCodeFontSize:plan.code.minimumFontSize??18,codeFontSize:plan.code.fontSize??30,
    events,...(audio?{audio}:{})};
  save('composition.json',composition);
  const python=path.join(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
  stage('preflight',()=>execute(python,[path.join(root,'scripts/render_independent_scenes.py'),path.join(out,'composition.json'),'--check']));
  if(!v['prepare-only'])stage('render-tracks-and-compose',()=>{
    const result=execute(python,[path.join(root,'scripts/render_independent_scenes.py'),path.join(out,'composition.json'),'--output',path.join(out,'render')]);
    report.render=JSON.parse(result.trim().split(/\r?\n/).at(-1));
  });
  if(Object.entries(hashes).some(([f,h])=>sha(f)!==h))throw Error('Source changed during pipeline');
  report.status=v['prepare-only']?'prepared':'complete';delete report.currentStage;save('pipeline-report.json',report);
  console.log(JSON.stringify({status:report.status,output:out,video:report.render?path.join(out,'render','composed.mp4'):null}));
}catch(e){report.status='failed';report.error=e.message;save('pipeline-report.json',report);throw e;}
