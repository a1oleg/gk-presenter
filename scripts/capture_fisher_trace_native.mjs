// Native-resolution capture using the real draw.io editor and runtime-panel HTML.
// The saved real Fisher session is replayed locally; no fabricated graph or events.
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const root=path.resolve('../coldKode'),out=path.resolve(process.argv[2]);
const require=createRequire(path.join(root,'package.json'));
const {chromium}=require('@playwright/test'),ts=require('typescript');
const {boxImage}=await import(pathToFileURL(path.join(root,'dev/localCoordinateDrawio.mjs')));
const latest=JSON.parse(await fs.readFile(path.join(root,'tmp/fisher-yates/runtime/latest.json'),'utf8'));
const xml=await fs.readFile(path.join(root,'graph/draw/generated/Fisher-Yates.drawio'),'utf8');
const src=await fs.readFile(path.join(root,'graph/vscode-extension/extension.js'),'utf8');
const ast=ts.createSourceFile('extension.js',src,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);
const fn=ast.statements.find(n=>ts.isFunctionDeclaration(n)&&n.name?.text==='buildRuntimeAnalysisHtml');
const {buildRuntimeAnalysisHtml}=await import('data:text/javascript,'+encodeURIComponent('export '+fn.getText(ast)));
const webroot=path.join(root,'graph/vendor/drawio/src/main/webapp');
const server=http.createServer(async(req,res)=>{try{
 const url=new URL(req.url,'http://localhost');
 if(url.pathname==='/capture'){res.setHeader('Content-Type','text/html');res.end('<style>html,body{margin:0;overflow:hidden;background:#fff}iframe{position:absolute;top:0;height:1080px;border:0}#d{left:0;width:880px}#p{left:880px;width:1040px;border-left:1px solid #bbb;box-sizing:border-box}</style><iframe id="d" src="/index.html?dev=1&embed=1&proto=json&ui=min&plugins=1&p=codexGraph&noSaveBtn=1"></iframe><iframe id="p" src="/panel"></iframe>');return;}
 if(url.pathname==='/panel'){res.setHeader('Content-Type','text/html');res.end(buildRuntimeAnalysisHtml(boxImage(),boxImage({collection:true})));return;}
 const file=path.resolve(webroot,'.'+decodeURIComponent(url.pathname));if(!file.startsWith(webroot+path.sep))throw Error('Invalid path');
 let data=await fs.readFile(file);if(url.pathname.endsWith('/plugins/codexGraph.js'))data=Buffer.from('Draw.loadPlugin(function(ui){window.__captureUi=ui;});\n'+data);
 res.setHeader('Content-Type',({'.js':'application/javascript','.html':'text/html','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.xml':'application/xml'})[path.extname(file)]||'application/octet-stream');res.end(data);
}catch(e){res.writeHead(404);res.end(e.message);}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.addInitScript(()=>{window.acquireVsCodeApi=()=>({postMessage:m=>{window.__lastPanelMessage=m;}});});
 await page.route('http://127.0.0.1:17843/**',r=>r.fulfill({json:{revision:0,message:null,command:null}}));
 await page.goto(`http://127.0.0.1:${server.address().port}/capture`);
 const diagram=page.frames().find(f=>f.url().includes('/index.html')),panel=page.frames().find(f=>f.url().endsWith('/panel'));
 await diagram.waitForFunction(()=>!!window.__captureUi,{timeout:30000});
 await diagram.evaluate(xml=>{const ui=window.__captureUi;ui.editor.setGraphXml(mxUtils.parseXml(xml).getElementsByTagName('mxGraphModel')[0]);},xml);
 await panel.evaluate(analysis=>window.dispatchEvent(new MessageEvent('message',{data:{type:'analysis',analysis}})),latest.analysis);
 await panel.locator('#details tr').first().waitFor();
 await panel.locator('#details tr').first().click();
 await diagram.evaluate(selection=>window.postMessage(JSON.stringify({action:'runtimeHighlight',selection}),'*'),latest.analysis.cases[0]);
 const geo=await diagram.evaluate(()=>{
  const ui=window.__captureUi,g=ui.editor.graph,v=g.view,m=g.model;
  if(ui.formatWindow)ui.formatWindow.setVisible(false);
  g.container.style.position='fixed';g.container.style.left='0';g.container.style.top='0';g.container.style.width='880px';g.container.style.height='1080px';
  g.container.style.backgroundColor='white';g.container.style.zIndex='100';
  v.scaleAndTranslate(1,0,0);v.validate();
  const first=v.getState(m.getCell('f0-n4'));if(!first)throw Error('Missing actual loop');
  const states=Object.values(m.cells).filter(c=>c.vertex&&!/fold-row|layout-root|block|backplane/.test(c.id)).map(c=>v.getState(c)).filter(s=>s&&s.cell.id.startsWith('f0-')&&s.y>=first.y&&s.y<first.y+1250);
  const right=Math.max(...states.map(s=>s.x+s.width));
  const bottom=Math.max(...states.map(s=>s.y+s.height));
  const left=Math.min(...states.map(s=>s.x));
  const scale=Math.min(1.25,820/(right-left),1000/(bottom-first.y));
  v.scaleAndTranslate(scale,35/scale-left,38/scale-first.y);v.validate();g.container.scrollLeft=0;g.container.scrollTop=0;
  return {scale,viewport:[880,1080],bounds:{left,right,top:first.y,bottom},highlightedEdges:Object.values(m.cells).filter(c=>c.edge&&/strokeWidth=3;shadow=0/.test(c.style||'')).length};
 });
 if(!geo.highlightedEdges)throw Error('Trace highlight missing');
 const panelCheck=await panel.evaluate(()=>({rows:document.querySelectorAll('#details tr').length,selected:document.querySelector('#details tr.selected')?.getAttribute('data-case-index'),scrollWidth:document.documentElement.scrollWidth,width:innerWidth}));
 if(!panelCheck.rows||panelCheck.selected!=='0'||panelCheck.scrollWidth>panelCheck.width)throw Error(JSON.stringify(panelCheck));
 await page.evaluate(()=>document.fonts.ready);
 await fs.writeFile(path.join(out,'trace-native-metadata.json'),JSON.stringify({sessionId:latest.sessionId,source:'graph/draw/generated/Fisher-Yates.drawio',resolution:[1920,1080],deviceScaleFactor:1,geometry:geo,panel:panelCheck},null,2));
 await page.screenshot({path:path.join(out,'trace-native.png')});
 console.log(JSON.stringify({output:path.join(out,'trace-native.png'),geometry:geo,panel:panelCheck}));
}finally{await browser.close();await new Promise(r=>server.close(r));}
