// Mechanical migration, with originals retained outside the material folders.
import fs from 'node:fs';import path from 'node:path';import {execFileSync} from 'node:child_process';
const repo=process.cwd(),config=JSON.parse(fs.readFileSync('materials.local.json','utf8'));
const backup=path.join(repo,'tmp/material-path-migration-originals');fs.mkdirSync(backup,{recursive:true});
const changed=[];
function save(file,text){const old=fs.readFileSync(file,'utf8');if(old===text)return;
 const name=String(changed.length).padStart(4,'0')+'-'+path.basename(file);
 fs.writeFileSync(path.join(backup,name),old);fs.writeFileSync(file,text);changed.push({file,backup:name});}
const tracked=execFileSync('git',['ls-files'],{encoding:'utf8'}).trim().split(/\r?\n/);
for(const rel of tracked.filter(f=>/^(scripts|tmp)\/.*\.(py|mjs)$/.test(f))){
 if(/material_paths|material-paths|publish_onedrive_paths|migrate_material/.test(rel))continue;
 let text=fs.readFileSync(rel,'utf8'),before=text,used=false;
 if(rel.endsWith('.py')){
  text=text.replace(/\b(?:ROOT|root)\s*\/\s*(['"])(output|data)(\/[^'"\r\n]*)?\1/g,(_,q,kind,rest)=>{used=true;return `material_dir('${kind}')`+(rest?` / ${q}${rest.slice(1)}${q}`:'');});
  if(used&&!/from material_paths import/.test(text)){
   const prefix=rel.startsWith('tmp/')?"import sys as _material_sys\nfrom pathlib import Path as _MaterialPath\n_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))\n":"";
   text=prefix+"from material_paths import material_dir\n"+text;
  }
 }else{
  text=text.replace(/path\.(?:resolve|join)\((?:(?:root|ROOT),\s*)?(['"])(output|data)\1\s*,/g,(_,q,kind)=>{used=true;return `path.join(materialDir('${kind}'),`;});
  text=text.replace(/`C:\/GitHub\/graphKoda-presenter\/(output|data)\//g,(_,kind)=>{used=true;return '`'+'${materialDir(\''+kind+'\')}/';});
  if(used&&!/import \{materialDir\}/.test(text))text="import {materialDir} from '../src/material-paths.mjs';\n"+text;
 }
 if(text!==before)save(path.resolve(rel),text);
}
const oldRoots=['C:/GitHub/graphKoda-presenter/','C:\\GitHub\\graphKoda-presenter\\'];
function remap(value){if(typeof value!=='string')return value;const normal=value.replaceAll('\\','/');
 for(const kind of ['output','data'])for(const prefix of [`C:/GitHub/graphKoda-presenter/${kind}/`,`${kind}/`,`../${kind}/`])if(normal.startsWith(prefix))return config[kind]+'/'+normal.slice(prefix.length);
 return value;}
function walk(value){if(Array.isArray(value))return value.map(walk);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,walk(v)]));return remap(value);}
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const history=/sheet|snapshot|before|scenario-source|publication-source|request|alignment|text-edits|manifest|inventory|migration|report-source/i;
const jsonFiles=[...tracked.filter(f=>f.startsWith('scenes/')&&f.endsWith('.json')).map(f=>path.resolve(f)),path.resolve('sources.local.json'),...files(config.output).filter(f=>f.endsWith('.json')&&!history.test(path.basename(f)))];
for(const file of jsonFiles){let parsed;try{parsed=JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));}catch{continue;}
 const next=walk(parsed);if(JSON.stringify(next)!==JSON.stringify(parsed))save(file,JSON.stringify(next,null,2)+'\n');}
for(const rel of tracked.filter(f=>f.endsWith('.md')&&(f.startsWith('scenes/')||f.startsWith('motion-canvas/')))){
 let text=fs.readFileSync(rel,'utf8');text=text.replace(/(?:\.\.\/)?output\/([\w.\/-]+)/g,(_,tail)=>config.output+'/'+tail);save(path.resolve(rel),text);
}
fs.writeFileSync(path.join(backup,'manifest.json'),JSON.stringify(changed,null,2));console.log(JSON.stringify({changed:changed.length,backup}));
