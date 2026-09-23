// Export a narration-only copy with the requested cumulative annotation count.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readScene,renderScene} from '../../graphKoda/graph/scene/scene.mjs';
const out=path.resolve(process.argv[2]),count=Number(process.argv[3]);
if(!Number.isInteger(count)||count<0||count>3)throw Error('Annotation count must be 0..3');
const source=path.resolve('../graphKoda/graph/draw/scenes/fisher.drawio');
const original=await fs.readFile(source),scene=await readScene('fisher');
scene.pointers={};scene.annotationStep=count;
await fs.writeFile(path.join(out,'source.drawio'),renderScene(scene));
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({source,sha256:createHash('sha256').update(original).digest('hex'),annotationCount:count,focusSwitching:false,derivedRenderCopy:true},null,2));
