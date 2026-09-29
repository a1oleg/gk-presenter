// Export an unchanged draw.io scene and coordinates for narration targets.
// Geometry comes from the real draw.io engine/MCP, not screenshot inference.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import {inspectionCacheDir} from '../src/diagnostic-cache.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const inspector=path.resolve(root,'../drawio-inspector');
const require=createRequire(path.join(inspector,'package.json'));
const {chromium}=require('playwright');
const {Client}=await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')));
const {StdioClientTransport}=await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')));
const {resolveViewer}=await import(pathToFileURL(path.join(inspector,'src/render.mjs')));
const out=path.resolve(process.argv[2]);
const [canvasWidth,canvasHeight]=(process.env.PRESENTER_CANVAS||'1600x900').split('x').map(Number);
const fixedScale=process.env.PRESENTER_SCALE?Number(process.env.PRESENTER_SCALE):null;
const tightExport=process.env.PRESENTER_TIGHT_EXPORT==='1';
if(fixedScale!==null&&(!Number.isFinite(fixedScale)||fixedScale<=0))throw Error('Invalid fixed scale');
if(!Number.isInteger(canvasWidth)||!Number.isInteger(canvasHeight)||canvasWidth<100||canvasHeight<100)throw Error('Invalid canvas');
const file=path.join(out,'source.drawio');
const revealPlan=process.env.PRESENTER_REVEAL_PLAN?JSON.parse(await fs.readFile(process.env.PRESENTER_REVEAL_PLAN,'utf8')):null;
const sheetBounds=process.env.PRESENTER_SHEET_BOUNDS==='1'
 ? JSON.parse(await fs.readFile(path.join(out,'sheet-source.json'),'utf8')).values[0].slice(7,11).map(s=>s.replace(/^stableId:\s*/,'')):null;
const client=new Client({name:'presenter-scene',version:'1.0.0'});
try {
 await client.connect(new StdioClientTransport({command:process.execPath,args:[path.join(inspector,'src/mcp.mjs')]}));
 for(const [name,args] of [['inspect_region',{cellId:process.argv[3]||'228',padding:10000}],['validate_geometry',{}]]) {
  const r=await client.callTool({name,arguments:{file,mode:'rendered',limit:500,...args}},undefined,{timeout:180000});
  if(r.isError)throw Error(JSON.stringify(r.content));
  const reportDir=name==='inspect_region'?inspectionCacheDir(out):out;
  await fs.mkdir(reportDir,{recursive:true});
  await fs.writeFile(path.join(reportDir,`${name}.json`),JSON.stringify(r.structuredContent,null,2));
  console.log(name,JSON.stringify(name==='inspect_region'?{count:r.structuredContent.elements.length}:r.structuredContent));
 }
}finally{await client.close();}
let xml=await fs.readFile(file,'utf8');
const assets=[];
for(const url of new Set([...xml.matchAll(/image=(https?:[^;]+);/g)].map(m=>m[1]))) {
 const response=await fetch(url,{signal:AbortSignal.timeout(30000)});
 if(!response.ok)throw Error(`Asset ${response.status}: ${url}`);
 const bytes=Buffer.from(await response.arrayBuffer());
 const mime=(response.headers.get('content-type')||'').split(';')[0];
 if(!mime.startsWith('image/'))throw Error('Not an image: '+url);
 const data=mime==='image/svg+xml'?`data:${mime},${encodeURIComponent(bytes.toString('utf8'))}`:`data:${mime},${bytes.toString('base64')}`;
 xml=xml.replaceAll('image='+url+';','image='+data+';');
 assets.push({url,mime,bytes:bytes.length});
}
await fs.writeFile(path.join(out,'assets.json'),JSON.stringify(assets,null,2));
// Built-in draw.io clipart is relative to the webapp, not to about:blank.
for(const relative of new Set([...xml.matchAll(/image=(img\/[^;"]+)(?=;|")/g)].map(m=>m[1]))) {
 const candidates=['../graphKoda','../coldKode'];
 let webapp;
 for(const candidate of candidates){const p=path.resolve(root,candidate,'graph/vendor/drawio/src/main/webapp');try{await fs.access(p);webapp=p;break;}catch{}}
 if(!webapp)throw Error('draw.io webapp not found');
 const local=path.resolve(webapp,relative);
 if(!local.startsWith(webapp+path.sep))throw Error('Asset outside draw.io webapp');
 const bytes=await fs.readFile(local);
 const mime=relative.endsWith('.svg')?'image/svg+xml':'image/png';
 const data=mime==='image/svg+xml'?`data:${mime},${encodeURIComponent(bytes.toString('utf8'))}`:`data:${mime},${bytes.toString('base64')}`;
 xml=xml.replaceAll('image='+relative,'image='+data);
}
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const ctx=await browser.newContext({viewport:{width:canvasWidth,height:canvasHeight},deviceScaleFactor:1,serviceWorkers:'block'});
 await ctx.route('**/*',r=>r.abort());
 const page=await ctx.newPage();
 await page.setContent(`<html><body style="margin:0;overflow:hidden;background:white"><div id="graph" style="width:${canvasWidth}px;height:${canvasHeight}px"></div></body></html>`);
 await page.addScriptTag({path:await resolveViewer()});
 const geometry=await page.evaluate(async ({xml,focusCellId,canvasWidth,canvasHeight,fixedScale,sheetBounds,tightExport})=>{
  const graph=new Graph(document.getElementById('graph'));graph.setEnabled(false);
  window.presenterGraph=graph;
  const doc=mxUtils.parseXml(xml);
  new mxCodec(doc).decode(doc.getElementsByTagName('mxGraphModel')[0],graph.getModel());
  graph.getView().scaleAndTranslate(1,0,0);graph.getView().validate();
  // Fit visible content, not unused editor page margins; preserve all relative positions.
  let b=focusCellId?graph.getView().getState(graph.getModel().getCell(focusCellId)):graph.getGraphBounds();
  if(sheetBounds){
   const bounds=sheetBounds.map(id=>{
    const ids=Array.from(doc.querySelectorAll('[stableId]')).filter(e=>e.getAttribute('stableId')===id).map(e=>e.getAttribute('id'));
    const matches=ids.map(id=>graph.getModel().getCell(id)).filter(c=>c?.vertex).map(c=>graph.getView().getState(c)).filter(Boolean);
    if(!matches.length)throw Error('Missing framing stableId: '+id);
    return {x:Math.min(...matches.map(s=>s.x)),y:Math.min(...matches.map(s=>s.y)),right:Math.max(...matches.map(s=>s.x+s.width)),bottom:Math.max(...matches.map(s=>s.y+s.height))};
   });
   b={x:bounds[1].x-24,y:bounds[0].y-24,width:bounds[2].right-bounds[1].x+48,height:bounds[3].bottom-bounds[0].y+48};
   if(b.width<=0||b.height<=0)throw Error('Invalid framing bounds');
  }
  if(!b)throw Error('Focus cell missing: '+focusCellId);
  if(tightExport){
   const boxes=[];
   for(const c of Object.values(graph.getModel().cells)){
    const s=graph.getView().getState(c);if(!s||(!c.vertex&&!c.edge))continue;
    const group=c.vertex&&c.children?.some(k=>k.vertex)&&!s.shape;
    if(group||String(c.style||'').startsWith('group;'))continue;
    const box=s.shape?.boundingBox||s;boxes.push(box);
    if(s.text?.boundingBox)boxes.push(s.text.boundingBox);
   }
   const x=Math.min(...boxes.map(r=>r.x)),y=Math.min(...boxes.map(r=>r.y));
   b={x,y,width:Math.max(...boxes.map(r=>r.x+r.width))-x,height:Math.max(...boxes.map(r=>r.y+r.height))-y};
  }
  const scale=tightExport?(fixedScale??1.5):(fixedScale??Math.min(canvasWidth*(sheetBounds?1:.9)/b.width,canvasHeight*(sheetBounds?1:700/900)/b.height));
  if(tightExport){canvasWidth=Math.ceil(b.width*scale)+32;canvasHeight=Math.ceil(b.height*scale)+32;}
  const tx=tightExport?16/scale-b.x:(canvasWidth/scale-b.width)/2-b.x,ty=tightExport?16/scale-b.y:fixedScale!==null?32/scale-b.y:(canvasHeight/scale-b.height)/2-b.y;
  graph.getView().scaleAndTranslate(scale,tx,ty);graph.getView().validate();
  await document.fonts.ready;
  await Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((res,rej)=>{
   const img=new Image();img.onload=res;img.onerror=()=>rej(Error('Image decode failed: '+img.src.slice(0,160)));
   img.src=e.getAttribute('href')||e.getAttribute('xlink:href');
  })));
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const cells={};
  for(const cell of Object.values(graph.getModel().cells)){
   const s=graph.getView().getState(cell);if(!s)continue;
   cells[cell.id]={x:s.x,y:s.y,width:s.width,height:s.height,edge:!!cell.edge,points:s.absolutePoints?.filter(Boolean).map(p=>({x:p.x,y:p.y}))};
  }
  return{width:canvasWidth,height:canvasHeight,scale,translation:{x:tx,y:ty},cells};
 },{xml,focusCellId:process.argv[4]||null,canvasWidth,canvasHeight,fixedScale,sheetBounds,tightExport});
 if(tightExport)await page.setViewportSize({width:geometry.width,height:geometry.height});
 await fs.writeFile(path.join(out,'screen-geometry.json'),JSON.stringify(geometry,null,2));
 await page.screenshot({path:path.join(out,'scene.png')});
 if(revealPlan){
  for(const [index,stage] of revealPlan.stages.entries()){
   const state=await page.evaluate(({plan,stage})=>{
    const graph=window.presenterGraph,model=graph.getModel();
    const all=Object.values(model.cells);
    const original=window.presenterVisibility??=Object.fromEntries(all.map(c=>[c.id,c.visible]));
    function belongs(c,ids){for(let p=c;p;p=p.parent)if(ids.includes(p.id))return true;return false;}
    model.beginUpdate();try{
     for(const c of all){
      const owner=plan.groups.findIndex(g=>belongs(c,g));
      const visible=owner<0||owner<stage.show;
      model.setVisible(c,original[c.id]!==false&&visible&&!stage.hide?.includes(c.id));
     }
    }finally{model.endUpdate();}
    graph.getView().validate();
    return {scale:graph.view.scale,translation:graph.view.translate,visible:all.filter(c=>graph.view.getState(c)).map(c=>c.id)};
   },{plan:revealPlan,stage});
   if(state.scale!==geometry.scale||state.translation.x!==geometry.translation.x||state.translation.y!==geometry.translation.y)throw Error('Reveal changed framing');
   await page.screenshot({path:path.join(out,`stage-${index}.png`)});
   await fs.writeFile(path.join(out,`stage-${index}.json`),JSON.stringify({...stage,...state},null,2));
  }
 }
 console.log('Scene exported, objects:',Object.keys(geometry.cells).length);
}finally{await browser.close();}
