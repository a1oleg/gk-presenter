import {Code,Rect,Txt,Line} from '@motion-canvas/2d';
import {createRef,waitFor,all} from '@motion-canvas/core';

// Code is an independent scene. Its boundary comes from the rightmost diagram
// representation, while its pointers come from source line/column coordinates.
export function addCodeScene(view:any,s:any){
 const data=s.code.source,r=s.code.rect,top=s.code.contentY;
 const code=createRef<Code>(),arrow=createRef<Line>();
 const highlighter={initialize:()=>true,prepare:(text:string)=>{
  if(text!==data.code)throw Error('Semantic snapshot mismatch');return data.colors;
 },highlight:(index:number,cache:string[])=>{const color=cache[index]||'#D4D4D4';let end=index+1;while(end<cache.length&&cache[end]===color)end++;return {color,skipAhead:end-index};},tokenize:(text:string)=>text.split(/(\s+|[(){}\[\].,;])/).filter(Boolean)};
 view.add(<Rect x={r.x+r.width/2-960} y={r.y+r.height/2-540} width={r.width} height={r.height} fill={'#1e1e1e'}/>);
 view.add(<Rect x={r.x-960} y={r.y+r.height/2-540} width={2} height={r.height} fill={'#536173'}/>);
 const codeX=r.x+65,font=s.code.fontSize,lineHeight=font*1.55;
 view.add(<Code ref={code} code={data.code} highlighter={highlighter} offset={[-1,-1]} x={codeX-960} y={top-540} fontFamily={'Consolas'} fontSize={font} lineHeight={lineHeight}/>);
 const characterBox=(line:number,col:number)=>{
  const boxes=code().getSelectionBBox([[line,col],[line,col+1]]);
  if(!boxes.length)throw Error('Missing character geometry');return boxes[0];
 };
 const points=data.lineMap.map((line:number,i:number)=>{
  const box=characterBox(i,0),point=code().localToParent().transformPoint(box.center);
  view.add(<Txt text={String(line)} x={r.x+25-960} y={point.y} fill={'#798390'} fontFamily={'Consolas'} fontSize={font*.75}/>);
  const end=characterBox(i,Math.max(0,data.code.split('\n')[i].length-1));
  const right=code().localToParent().transformPoint(end.bottomRight);
  if(right.x+960>1920-16||right.y+540>r.y+r.height-16)throw Error('Code does not fit the independently allocated region');
  return {line,y:point.y+540,right:right.x+960};
 });
 (window as any).codeLayoutReport={points,rect:r,contentY:top,fontSize:font};
 const target=(e:any)=>{
  const i=data.lineMap.indexOf(e.codeLine),col=data.code.split('\n')[i]?.indexOf(e.codeToken);
  if(i<0||col<0)throw Error('Pointer source range missing');
  const box=characterBox(i,col);return code().localToParent().transformPoint(box.center);
 };
 const first=target(s.events[0]);
 view.add(<Line ref={arrow} points={[[0,0],[30,20]]} position={[first.x-36,first.y-27]} stroke={'#ef3939'} lineWidth={5} endArrow arrowSize={15} opacity={0}/>);
 return function* animatePointer(){
  let time=0;
  for(const e of s.events){yield* waitFor(Math.max(0,e.time-time));const p=target(e);
   yield* all(arrow().opacity(1,.1),arrow().position([p.x-36,p.y-27],.45));time=e.time+.45;
  }
 };
}
