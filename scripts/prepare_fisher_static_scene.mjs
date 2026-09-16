// Render-only copy: the editor's source scene and its annotations stay unchanged.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readScene,renderScene} from '../../coldKode/graph/scene/scene.mjs';
const out=path.resolve(process.argv[2]);
const snapshot=JSON.parse(await fs.readFile(path.join(out,'sheet-source.json'),'utf8'));
const source=snapshot.values[1][1];
const original=await fs.readFile(source);
const scene=await readScene('fisher');
if(path.resolve(source)!==path.resolve('../coldKode/graph/draw/scenes/fisher.drawio'))throw Error('Unexpected scene');
scene.visibleThrough=0;scene.snippets=[];scene.pointers={};
await fs.writeFile(path.join(out,'source.drawio'),renderScene(scene));
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({source,sha256:createHash('sha256').update(original).digest('hex'),annotationsVisible:false,focusSwitching:false,derivedRenderCopy:true},null,2));
console.log(scene.nodes[scene.rootStableId].cellId);
