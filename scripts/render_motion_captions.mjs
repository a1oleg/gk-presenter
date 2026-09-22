import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from '../../drawio-inspector/node_modules/playwright/index.mjs';
const out=path.resolve(process.argv[2]),scene=JSON.parse(await fs.readFile(path.join(out,'scenario.json'),'utf8'));
await fs.mkdir(path.join(out,'caption-frames'),{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')console.error(m.text());});
 let frames=0;await page.exposeFunction('saveFrame',async(frame,data)=>{await fs.writeFile(path.join(out,'caption-frames',String(frame).padStart(5,'0')+'.png'),Buffer.from(data.split(',')[1],'base64'));frames++;});
 await page.goto('http://127.0.0.1:9031/render.html');
 await page.waitForFunction(()=>typeof window.renderCaptions==='function',{timeout:30000});
 const result=await page.evaluate(s=>window.renderCaptions(s),scene);
 if(errors.length||frames<Math.floor(scene.duration*30))throw Error(JSON.stringify({errors,frames}));
 await fs.writeFile(path.join(out,'motion-render.json'),JSON.stringify({...result,frames},null,2));console.log({...result,frames});
}finally{await browser.close();}
