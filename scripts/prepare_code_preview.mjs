import fs from 'node:fs/promises';import path from 'node:path';import {createRequire} from 'node:module';import vm from 'node:vm';
const require=createRequire(import.meta.url),ts=require('../motion-canvas/node_modules/typescript');
const {classify}=require('../../coldKode/graph/vscode-source-colors/classify.js');
const file='C:/GitHub/coldKode/examples/fisher-yates/src/shuffle.ts',source=await fs.readFile(file,'utf8');
const extension=await fs.readFile('C:/GitHub/coldKode/graph/vscode-source-colors/extension.js','utf8');
const palette=vm.runInNewContext('('+extension.match(/const palette = (\{[^\n]+\});/)[1]+')');
const marks=classify(ts,file,source),colors=Array(source.length).fill('#D4D4D4');
const scan=ts.createScanner(ts.ScriptTarget.Latest,false,ts.LanguageVariant.Standard,source);
while(true){const kind=scan.scan();if(kind===ts.SyntaxKind.EndOfFileToken)break;let color=null;
 if(kind>=ts.SyntaxKind.FirstKeyword&&kind<=ts.SyntaxKind.LastKeyword)color=palette.system;
 if(kind===ts.SyntaxKind.StringLiteral)color='#FFFFFF';
 if(kind===ts.SyntaxKind.NumericLiteral)color='#B5CEA8';
 if(kind===ts.SyntaxKind.SingleLineCommentTrivia)color='#6A9955';
 if(color)colors.fill(color,scan.getTokenPos(),scan.getTextPos());
}
for(const m of marks)if(palette[m.role])colors.fill(palette[m.role],m.start,m.end);
const chunks=source.match(/[^\n]*\n|[^\n]+$/g);let at=0,code='',lookup=[],lineMap=[];
for(let i=0;i<chunks.length;i++){const raw=chunks[i],line=raw.replace(/[\r\n]+$/,'');
 if(i<37&&line.trim()&&!line.trim().startsWith('//')){if(code){code+='\n';lookup.push('#D4D4D4');}code+=line;lookup.push(...colors.slice(at,at+line.length));lineMap.push(i+1);}at+=raw.length;
}
const out=path.resolve('output',`motion-code-preview-${Date.now()}`);await fs.mkdir(out);
const scene={kind:'code-preview',duration:1,code,colors:lookup,lineMap,source:file,semanticSource:'coldKode/graph/vscode-source-colors/classify.js',paletteSource:'coldKode/graph/vscode-source-colors/extension.js'};
await fs.writeFile(path.join(out,'scenario.json'),JSON.stringify(scene,null,2));console.log(out);
