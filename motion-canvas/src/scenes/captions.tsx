import {makeScene2D,Rect,Txt} from '@motion-canvas/2d';
import {createRef,createSignal,waitFor} from '@motion-canvas/core';
import {codePreview} from './code-preview';
import {addCodeScene} from './dual-code';

// Scene data is injected by the presenter, not inferred by the graphics layer.
export default makeScene2D(function*(view){
 const s=(window as any).presenterScene;
 if(s.kind==='code-preview'){yield* codePreview(view,s);return;}
 const animateCode=s.kind==='dual-scene'?addCodeScene(view,s):null;
 const values=createSignal(s.captions.values);
 const {x,y,width,height}=s.captions.rect;
 const panel=createRef<Rect>();
 view.add(<Rect ref={panel} x={x+width/2-960} y={y+height/2-540} width={width} height={height} radius={14} fill={'#101926f5'} stroke={'#697482'} lineWidth={1.4} shadowBlur={10} shadowColor={'#00000060'} shadowOffsetY={4} opacity={0}/>);
 const p=panel();const left=-width/2;
 const compact=s.captions.design==='compact';
 const geometry=compact?{first:155,pitch:48,cell:40,divider:530,current:593,index:680,value:824,valueWidth:170,lastDivider:932,random:1000,result:1140,resultWidth:76}:{first:175,pitch:62,cell:52,divider:667,current:755,index:860,value:1032,valueWidth:215,lastDivider:1175,random:1250,result:1390,resultWidth:104};
 const label=(text:string|(()=>string),cx:number,cy:number,size=22,fill:any='#efb65e')=>p.add(<Txt text={text} x={left+cx} y={cy} fontFamily={'Consolas'} fontSize={size} fill={fill}/>);
 label('alphabet',78,10,24);
 s.captions.values.alphabet.forEach((letter:string,i:number)=>{
  const cx=geometry.first+i*geometry.pitch,active=()=>i===values().current.index;
  label(String(i),cx,-31,17,()=>active()?'#ffc75b':'#9aa6b7');
  p.add(<Rect x={left+cx} y={11} width={geometry.cell} height={45} radius={6} stroke={()=>active()?'#ffc75b':'#505d70'} lineWidth={()=>active()?2:1.2} fill={()=>active()?'#554421':'#131e2c'}/>);
  label(()=>values().alphabet[i],cx,11,28,'#f7f8fc');
 });
 p.add(<Rect x={left+geometry.divider} width={1} height={66} fill={'#566476'}/>);
 label('current',geometry.current,10,24);label('index',geometry.index,-30,17,'#9aa6b7');label('value',geometry.value,-30,17,'#9aa6b7');
 for(const [cx,w,text,color] of [[geometry.index,66,()=>String(values().current.index),'#ffffff'],[geometry.value,geometry.valueWidth,()=>String(values().current.value),'#caa4f2']] as const){
  p.add(<Rect x={left+cx} y={11} width={w} height={45} radius={6} stroke={'#667080'} lineWidth={1.2} fill={'#111c29'}/>);label(text,cx,11,25,color);
 }
 p.add(<Rect x={left+geometry.lastDivider} width={1} height={66} fill={'#566476'}/>);
 label('random',geometry.random,10,23);p.add(<Rect x={left+geometry.result} y={11} width={geometry.resultWidth} height={45} radius={6} stroke={'#667080'} lineWidth={1.2} fill={'#111c29'}/>);label(()=>values().random==null?'—':String(values().random),geometry.result,11,25,'#c3cbd6');
 if(animateCode)yield animateCode();
 if(s.captionEvents?.length)yield (function*(){let time=0;for(const event of s.captionEvents){yield* waitFor(Math.max(0,event.time-time));values(event.values);time=event.time;}})();
 yield* p.opacity(1,.3);yield* waitFor(s.duration+.5);
});
