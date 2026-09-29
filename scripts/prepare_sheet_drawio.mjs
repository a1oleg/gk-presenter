// Snapshot the exact diagram selected in the sheet, without modifying its source.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const out=path.resolve(process.argv[2]);
const snapshot=JSON.parse(await fs.readFile(path.join(out,'sheet-source.json'),'utf8'));
const source=(process.argv[3]||(snapshot.values.length===1?snapshot.values[0][2]:snapshot.values[1][1])).trim().replace(/^"|"$/g,'');
if(path.extname(source).toLowerCase()!=='.drawio')throw Error('Expected a draw.io scene');
const bytes=await fs.readFile(source);
await fs.writeFile(path.join(out,'source.drawio'),bytes,{flag:'wx'});
await fs.writeFile(path.join(out,'scene-preparation.json'),JSON.stringify({source,sha256:createHash('sha256').update(bytes).digest('hex'),sourceUnchanged:true},null,2));
