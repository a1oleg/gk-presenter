import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
export function materialDir(kind='output') {
  if(!['output','data'].includes(kind))throw Error('Unknown material directory');
  const config=path.join(root,'materials.local.json');
  if(!fs.existsSync(config))throw Error('Configure materials.local.json before generating materials');
  const target=JSON.parse(fs.readFileSync(config,'utf8').replace(/^\uFEFF/,''))[kind];
  fs.mkdirSync(target,{recursive:true});return fs.realpathSync.native(target);
}
