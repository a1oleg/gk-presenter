import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);
export function selectSourceLines(source,colors,ranges) {
  const chunks=source.match(/[^\n]*\n|[^\n]+$/g)||[];
  if(!Array.isArray(ranges)||!ranges.length)throw Error('code.lines requires inclusive line ranges');
  const selected=new Set();let previous=0;
  for(const range of ranges){
    if(!Array.isArray(range)||range.length!==2||!range.every(Number.isInteger)||range[0]<1||range[1]<range[0]||range[1]>chunks.length||range[0]<=previous)throw Error('Line ranges must be ordered, non-overlapping and inside the source');
    for(let n=range[0];n<=range[1];n++)selected.add(n);previous=range[1];
  }
  let offset=0,code='',lookup=[],lineMap=[];
  for(const [i,chunk] of chunks.entries()){
    const line=chunk.replace(/[\r\n]+$/,'');
    if(selected.has(i+1)){
      if(lineMap.length){code+='\n';lookup.push('#D4D4D4');}
      code+=line;lookup.push(...colors.slice(offset,offset+line.length));lineMap.push(i+1);
    }
    offset+=chunk.length;
  }
  return {code,colors:lookup,lineMap};
}
export function semanticSnapshot({file,semanticRoot,lines}) {
  const ts=require('../motion-canvas/node_modules/typescript');
  const classifier=path.join(semanticRoot,'classify.js'),extension=path.join(semanticRoot,'extension.js');
  const {classify}=require(classifier);
  const source=fs.readFileSync(file,'utf8').replace(/^\uFEFF/,'');
  const paletteMatch=fs.readFileSync(extension,'utf8').match(/const palette = (\{[^\n]+\});/);
  if(!paletteMatch)throw Error('Semantic palette declaration not found');
  const palette=vm.runInNewContext('('+paletteMatch[1]+')',Object.create(null),{timeout:1000});
  const colors=Array(source.length).fill('#D4D4D4');
  const scan=ts.createScanner(ts.ScriptTarget.Latest,false,ts.LanguageVariant.Standard,source);
  while(true){
    const kind=scan.scan();if(kind===ts.SyntaxKind.EndOfFileToken)break;
    let color=null;
    if(kind>=ts.SyntaxKind.FirstKeyword&&kind<=ts.SyntaxKind.LastKeyword)color=palette.system;
    if(kind===ts.SyntaxKind.StringLiteral)color='#FFFFFF';
    if(kind===ts.SyntaxKind.NumericLiteral)color='#B5CEA8';
    if([ts.SyntaxKind.SingleLineCommentTrivia,ts.SyntaxKind.MultiLineCommentTrivia].includes(kind))color='#6A9955';
    if(color)colors.fill(color,scan.getTokenPos(),scan.getTextPos());
  }
  // Same TypeScript base colors as the existing code-preview adapter, followed
  // by graphKoda semantic overlays. The snapshot is independent of editor UI.
  const ast=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true);
  function base(node){
    const tint=(n,c)=>colors.fill(c,n.getStart(ast),n.end);
    if(ts.isCallExpression(node)&&ts.isIdentifier(node.expression))tint(node.expression,palette.call);
    if(ts.isFunctionDeclaration(node)&&node.name)tint(node.name,palette.callableBinding);
    if(ts.isIdentifier(node)&&(ts.isVariableDeclaration(node.parent)||ts.isParameter(node.parent))&&node.parent.name===node)tint(node,palette.valueRoot);
    if(ts.isObjectLiteralExpression(node))for(const child of node.getChildren(ast))if([ts.SyntaxKind.OpenBraceToken,ts.SyntaxKind.CloseBraceToken].includes(child.kind))tint(child,'#CE9178');
    ts.forEachChild(node,base);
  }
  base(ast);
  for(const mark of classify(ts,file,source))if(palette[mark.role])colors.fill(palette[mark.role],mark.start,mark.end);
  return {kind:'code-preview',...selectSourceLines(source,colors,lines),source:file,sourceSha256:createHash('sha256').update(fs.readFileSync(file)).digest('hex'),semanticSource:classifier,paletteSource:extension};
}
