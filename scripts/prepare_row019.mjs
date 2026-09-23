import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readScene,renderScene} from '../../graphKoda/graph/scene/scene.mjs';
const out=path.resolve(process.argv[2]);
const scene=await readScene('fisher');scene.pointers={};
const files=['../graphKoda/graph/draw/scenes/fisher.drawio','../graphKoda/graph/draw/generated/Fisher-Yates.drawio'];
const sources=[];
for(const file of files)sources.push({file:path.resolve(file),sha256:createHash('sha256').update(await fs.readFile(file)).digest('hex')});
for(const name of ['detail','overview','annotated'])await fs.mkdir(path.join(out,name),{recursive:true});
await fs.copyFile(files[1],path.join(out,'detail/source.drawio'));
const annotated=structuredClone(scene);annotated.snippets=annotated.snippets.filter(s=>s.order===1);annotated.annotationStep=1;
await fs.writeFile(path.join(out,'annotated/source.drawio'),renderScene(annotated));
// The empty overview keeps the annotation's geometry as an invisible spacer.
// This prevents a camera jump when its text appears.
const overview=renderScene(annotated).replace(/(<object[^>]*annotationOwnerStableId[^>]*>[\s\S]*?<mxCell[^>]*style=")([^"]*)/g,'$1$2opacity=0;textOpacity=0;');
await fs.writeFile(path.join(out,'overview/source.drawio'),overview);
await fs.writeFile(path.join(out,'scene-sources.json'),JSON.stringify(sources,null,2));
