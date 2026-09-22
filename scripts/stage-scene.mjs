import {parseArgs} from 'node:util';
import path from 'node:path';
import {materialDir} from '../src/material-paths.mjs';
import {prepareScene,applyPreparedScene,checkPreparedScene} from '../src/scene-staging.mjs';

const {values:v}=parseArgs({options:{action:{type:'string',default:'prepare'},row:{type:'string'},spreadsheet:{type:'string'},sheet:{type:'string',default:'!'},diagram:{type:'string'},function:{type:'string'},session:{type:'string'},output:{type:'string'}}});
if(!['prepare','apply','check'].includes(v.action))throw Error('Action must be prepare, apply or check');
if(v.action==='prepare'){
  if(!v.row||!v.diagram)throw Error('prepare requires --row and --diagram');
  const output=v.output||path.join(materialDir(),`scene-row${v.row}-${Date.now()}`);
  const result=await prepareScene({row:Number(v.row),spreadsheetId:v.spreadsheet,sheet:v.sheet,diagram:v.diagram,functionStableId:v.function,sessionFile:v.session,output});
  console.log(JSON.stringify({output:result.output,canvas:result.canvas,diagram:result.diagram,sessionId:result.sessionId},null,2));
} else {
  if(!v.output)throw Error('apply/check requires --output');
  const result=await (v.action==='apply'?applyPreparedScene:checkPreparedScene)(v.output);
  console.log(JSON.stringify({passed:result.passed,topGap:result.topGap,bottomGap:result.bottomGap},null,2));
}
