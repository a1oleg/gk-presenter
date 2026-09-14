import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
const root = fileURLToPath(new URL('../', import.meta.url));
const inspector = path.resolve(root, '../drawio-inspector');
const require = createRequire(path.join(inspector, 'package.json'));
const { chromium } = require('playwright');
const { Client } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')));
const { resolveViewer } = await import(pathToFileURL(path.join(inspector, 'src/render.mjs')));
const file = path.join(root, 'diagrams/hla-stages/001-code-graph-diagram.drawio');
const client = new Client({name:'presenter-hla-check',version:'1.0.0'});
try {
  await client.connect(new StdioClientTransport({command:process.execPath,args:[path.join(inspector,'src/mcp.mjs')]}));
  const result = await client.callTool({name:'validate_geometry',arguments:{file,mode:'rendered',limit:500}},undefined,{timeout:180000});
  if (result.isError) throw new Error(JSON.stringify(result.content));
  const report = result.structuredContent;
  await fs.writeFile(path.join(root,'diagrams/hla-stages/001-check.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
  if (report.truncated || report.findings?.length) throw new Error('Resolve MCP geometry findings before export');
} finally { await client.close(); }
const xml = await fs.readFile(file,'utf8');
const browser = await chromium.launch({channel:'chrome',headless:true});
try {
  const context = await browser.newContext({viewport:{width:1600,height:900},deviceScaleFactor:1,serviceWorkers:'block'});
  await context.route('**/*', r=>r.abort());
  const page = await context.newPage();
  await page.setContent('<html><body style="margin:0;background:white;overflow:hidden"><div id="graph" style="width:1600px;height:900px"></div></body></html>');
  await page.addScriptTag({path:await resolveViewer()});
  await page.evaluate(async xml=>{
    const graph = new Graph(document.getElementById('graph'));
    graph.setEnabled(false);
    const doc=mxUtils.parseXml(xml);
    new mxCodec(doc).decode(doc.getElementsByTagName('mxGraphModel')[0],graph.getModel());
    graph.getView().scaleAndTranslate(1,0,0);
    graph.getView().validate();
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('image')].map(e=>new Promise((resolve,reject)=>{
      const img=new Image(); img.onload=resolve; img.onerror=()=>reject(new Error('Embedded image failed'));
      img.src=e.getAttribute('href') || e.getAttribute('xlink:href');
    })));
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  },xml);
  await page.screenshot({path:file.replace('.drawio','.png')});
  console.log('Exported 1600 x 900 PNG');
} finally {await browser.close();}
