import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {spawnSync} from 'node:child_process';
import {compileProduction} from '../src/production-plan.mjs';
import {materialDir} from '../src/material-paths.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const {values:v}=parseArgs({options:{lesson:{type:'string'},check:{type:'boolean',default:false}}});
if(!v.lesson) throw Error('Usage: npm run produce -- --lesson lesson.json [--check]');
const source=fs.realpathSync(v.lesson);
const lesson=JSON.parse(fs.readFileSync(source,'utf8').replace(/^\uFEFF/,''));
const plan=compileProduction(lesson,path.dirname(source));
const python=path.join(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
const pythonOptions={input:JSON.stringify(plan),encoding:'utf8',maxBuffer:4*1024*1024,env:{...process.env,PYTHONUTF8:'1'}};
// Check includes real asset decoding, audio timing and overlay bounds, without output files.
const preflight=spawnSync(python,[path.join(root,'scripts/render_production.py'),'--check'],pythonOptions);
if(preflight.error) throw preflight.error;
if(preflight.status!==0) {process.stderr.write(preflight.stderr||preflight.stdout);process.exit(preflight.status||1);}
if(v.check) {process.stdout.write(preflight.stdout);process.exit(0);}
const out=fs.mkdtempSync(path.join(materialDir(),'production-'));
fs.writeFileSync(path.join(out,'lesson-source.json'),JSON.stringify(lesson,null,2));
fs.writeFileSync(path.join(out,'production-plan.json'),JSON.stringify(plan,null,2));
console.log(`Output: ${out}`);
const result=spawnSync(python,[path.join(root,'scripts/render_production.py'),'--output',out],pythonOptions);
if(result.error) throw result.error;
process.stdout.write(result.stdout||'');process.stderr.write(result.stderr||'');
process.exitCode=result.status ?? 1;
