import fs from 'node:fs/promises';import path from 'node:path';import {createRequire} from 'node:module';import vm from 'node:vm';
import {materialDir} from '../src/material-paths.mjs';
const require=createRequire(import.meta.url),ts=require('../motion-canvas/node_modules/typescript');
const {classify}=require('../../graphKoda/graph/vscode-source-colors/classify.js');
const file='C:/GitHub/graphKoda/examples/fisher-yates/src/shuffle.ts',source=await fs.readFile(file,'utf8');
const extension=await fs.readFile('C:/GitHub/graphKoda/graph/vscode-source-colors/extension.js','utf8');
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
// Base TS theme underneath the same semantic overlays used by VS Code.
const ast=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true);
function base(node){
 const tint=(n,c)=>colors.fill(c,n.getStart(ast),n.end);
 if(ts.isCallExpression(node)&&ts.isIdentifier(node.expression))tint(node.expression,palette.call);
 if(ts.isFunctionDeclaration(node)&&node.name)tint(node.name,palette.callableBinding);
 if(ts.isIdentifier(node)&&(ts.isVariableDeclaration(node.parent)||ts.isParameter(node.parent))&&node.parent.name===node)tint(node,palette.valueRoot);
 if(ts.isObjectLiteralExpression(node))for(const child of node.getChildren(ast))if([ts.SyntaxKind.OpenBraceToken,ts.SyntaxKind.CloseBraceToken].includes(child.kind))tint(child,'#CE9178');
 ts.forEachChild(node,base);
}base(ast);
for(const m of marks)if(palette[m.role])colors.fill(palette[m.role],m.start,m.end);
const chunks=source.match(/[^\n]*\n|[^\n]+$/g);let at=0,code='',lookup=[],lineMap=[];
for(let i=0;i<chunks.length;i++){const raw=chunks[i],line=raw.replace(/[\r\n]+$/,'');
 if(i<37&&i>=(process.argv[2]?24:0)&&line.trim()&&!line.trim().startsWith('//')){if(code){code+='\n';lookup.push('#D4D4D4');}code+=line;lookup.push(...colors.slice(at,at+line.length));lineMap.push(i+1);}at+=raw.length;
}
const out=process.argv[2]?path.resolve(process.argv[2]):path.join(materialDir(),`motion-code-preview-${Date.now()}`);await fs.mkdir(out,{recursive:true});
const scene={kind:'code-preview',duration:1,code,colors:lookup,lineMap,source:file,semanticSource:'graphKoda/graph/vscode-source-colors/classify.js',paletteSource:'graphKoda/graph/vscode-source-colors/extension.js'};
await fs.writeFile(path.join(out,process.argv[2]?'code-source.json':'scenario.json'),JSON.stringify(scene,null,2));console.log(out);
