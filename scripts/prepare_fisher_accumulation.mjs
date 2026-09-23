// Keep one camera framing while cumulative annotations become visible.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readScene,renderScene} from '../../graphKoda/graph/scene/scene.mjs';
const out=path.resolve(process.argv[2]);
const source=path.resolve('../graphKoda/graph/draw/scenes/fisher.drawio');
const original=await fs.readFile(source),scene=await readScene('fisher');scene.pointers={};scene.annotationStep=3;
const xml=renderScene(scene);
for(const count of [1,2,3]){
 const folder=path.join(out,`stage${count}`);await fs.mkdir(folder,{recursive:true});
 const copy=xml.replace(/<object\b[^>]*revealOrder="(\d+)"[^>]*>[\s\S]*?<\/object>/g,(object,order)=>Number(order)>count?object.replace('style="','style="opacity=0;textOpacity=0;'):object);
 await fs.writeFile(path.join(folder,'source.drawio'),copy);
}
await fs.writeFile(path.join(out,'scene-sources.json'),JSON.stringify([{file:source,sha256:createHash('sha256').update(original).digest('hex')}],null,2));
