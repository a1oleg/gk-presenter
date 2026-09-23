import fs from 'node:fs/promises';
import path from 'node:path';
import {renderScene} from '../src/render-service.mjs';
const [directory,reference]=process.argv.slice(2);
if(!directory||!reference)throw Error('Usage: preview_with_captions.mjs sceneDir referenceScenario');
const out=path.resolve(directory),ref=JSON.parse(await fs.readFile(reference,'utf8'));
const prepFile=path.join(out,'scene-preparation.json'),prep=JSON.parse(await fs.readFile(prepFile,'utf8'));
const scene={kind:'captions',duration:1,canvas:{width:1920,height:1080},captions:structuredClone(ref.captions)};
// Reuse row 11's actual caption design; top capture margin is above all framed nodes.
scene.captions.rect={x:80,y:0,width:1240,height:96};
scene.captions.values.current={index:7,value:'Ж'};scene.captions.values.random=6;
prep.recording=path.join(out,'preview.png');
prep.captions={reference:path.resolve(reference),moment:'before swap, first iteration',rect:scene.captions.rect};
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(scene,null,2),{flag:'wx'});
await fs.writeFile(prepFile,JSON.stringify(prep,null,2));
console.log(await renderScene({sceneDir:out,mode:'preview',time:.5,filename:'preview-captioned.png'}));
