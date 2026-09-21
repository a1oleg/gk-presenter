import {bridge,diagramIndex} from '../../coldKode/graph/presentation/presentation.mjs';
const fn='services/api/claude.ts:1022:0:2911:1',file='graph/draw/generated/queryModel.drawio';
console.log(await bridge({surface:'editor',action:'openDiagram',functionStableId:fn,filePath:file}));
const idx=await diagramIndex({file});
console.log(idx.cells.filter(c=>['services/api/claude.ts:1051:5:1051:27','services/api/claude.ts:1052:4:1052:39','services/api/claude.ts:1062:4:1062:42','services/api/claude.ts:1063:10:1066:5'].includes(c.stableId)));
console.log(await bridge({surface:'diagram',action:'presentRead',functionStableId:fn,stableId:'services/api/claude.ts:1051:5:1051:27',cellId:'f0-n9'}));
