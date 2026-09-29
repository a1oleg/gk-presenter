// Export the exact slide as vectors, then rasterize at video resolution.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../../drawio-inspector/package.json',import.meta.url));
const {chromium}=require('playwright');
const out=path.resolve(process.argv[2]);
const meta=JSON.parse(await fs.readFile(path.join(out,'google-slide.json'),'utf8'));
const url=`https://docs.google.com/presentation/d/${meta.presentationId}/export/svg?pageid=${meta.pageObjectId}`;
const response=await fetch(url);
if(!response.ok)throw Error(`Slide export HTTP ${response.status}`);
const svg=await response.text();
if(!svg.startsWith('<svg'))throw Error('Expected SVG');
const svgPath=path.join(out,'google-slide.svg');
try {await fs.writeFile(svgPath,svg,{flag:'wx'});} catch(e) {
 if(e.code!=='EEXIST'||await fs.readFile(svgPath,'utf8')!==svg)throw e;
}
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.setContent(`<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg{width:1920px;height:1080px}</style>${svg}`);
 await page.evaluate(()=>document.fonts.ready);
 await page.screenshot({path:path.join(out,'slide-1920.png')});
 console.log(JSON.stringify({output:path.join(out,'slide-1920.png'),width:1920,height:1080,source:'Google Slides vector export'}));
} finally {await browser.close();}
