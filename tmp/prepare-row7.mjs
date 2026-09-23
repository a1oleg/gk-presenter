import {bridge,diagramIndex} from '../../graphKoda/graph/presentation/presentation.mjs';
import fs from 'node:fs/promises';
const stableId='examples/fisher-yates/src/shuffle.ts:6:7:33:1:flow-start';
const {glob}=await import('node:fs/promises');const candidates=[];
for await(const f of glob('C:/GitHub/graphKoda/graph/draw/generated/*.drawio')){
 const index=await diagramIndex({file:f});if(index.cells.some(c=>c.stableId===stableId))candidates.push(index);
}
const index=candidates.find(x=>x.file.endsWith('Fisher-Yates.drawio'));if(!index)throw Error('No function diagram contains the start node');
const fn=index.cells.find(c=>c.cellId==='f0-block').stableId;
const source='examples/fisher-yates/src/shuffle.ts:5:0:32:1';
const opened=await bridge({surface:'editor',action:'openSource',functionStableId:fn,filePath:index.file,stableId:source,placement:'RIGHT'});
const focus=await bridge({surface:'diagram',action:'presentFocus',functionStableId:fn,stableId,cellId:'f0-n1',scale:1.32});
console.log(JSON.stringify({opened,focus,diagram:index.file,functionStableId:fn}));
