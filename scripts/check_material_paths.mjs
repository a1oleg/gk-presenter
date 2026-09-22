import fs from 'node:fs';import path from 'node:path';import {execFileSync} from 'node:child_process';
import {materialDir} from '../src/material-paths.mjs';
const tracked=execFileSync('git',['ls-files'],{encoding:'utf8'}).trim().split(/\r?\n/);
let syntax=0;
for(const file of tracked.filter(f=>/^(scripts|tmp|src)\/.*\.mjs$/.test(f))){execFileSync(process.execPath,['--check',file]);syntax++;}
const output=materialDir(),data=materialDir('data');
const latest=path.join(output,'fisher-sequence-A1-N9-1790063462428402500');
for(const name of ['scenario.json','scene-preparation.json','timeline.json','scene.mp4'])if(!fs.existsSync(path.join(latest,name)))throw Error('Missing '+name);
const scene=JSON.parse(fs.readFileSync(path.join(latest,'scenario.json'),'utf8'));
const prep=JSON.parse(fs.readFileSync(path.join(latest,'scene-preparation.json'),'utf8'));
if(!fs.existsSync(prep.recording)||!fs.existsSync(scene.audioSource))throw Error('Broken working scene paths');
const input=JSON.parse(fs.readFileSync('sources.local.json','utf8'));
if(!fs.existsSync(input.videoPath)||!input.videoPath.replaceAll('\\','/').startsWith(data.replaceAll('\\','/')))throw Error('Broken source');
const testDir=path.join(output,`material-path-check-${Date.now()}`);fs.mkdirSync(testDir);
fs.writeFileSync(path.join(testDir,'scenario.json'),JSON.stringify({...scene,duration:.4},null,2));
console.log(JSON.stringify({syntax,output,data,latest,testDir,workingReferences:true}));
