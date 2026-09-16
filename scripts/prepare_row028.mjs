import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const out=path.resolve(process.argv[2]);
const source=path.resolve('../coldKode/graph/draw/scenes/fisher-search');
const sources=[];
for(let n=1;n<=6;n++){
 const name=`frame-${String(n).padStart(2,'0')}`;
 const dir=path.join(out,name);await fs.mkdir(dir,{recursive:true});
 const check=JSON.parse(await fs.readFile(path.join(source,name,'validate_geometry.json'),'utf8'));
 if(check.totalFindings)throw Error('Unresolved geometry findings '+name);
 for(const file of ['source.drawio','scene.png','screen-geometry.json','validate_geometry.json']){
  const from=path.join(source,name,file),bytes=await fs.readFile(from);
  await fs.writeFile(path.join(dir,file),bytes);
  sources.push({file:from,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
}
await fs.writeFile(path.join(out,'scene-sources.json'),JSON.stringify(sources,null,2));
await fs.copyFile('scenes/row028.sequence.json',path.join(out,'sequence-plan.json'));
console.log('Copied six verified frames and saved source hashes.');
