import {makeScene2D,Rect,Txt} from '@motion-canvas/2d';
import {createRef,waitFor} from '@motion-canvas/core';
import {codePreview} from './code-preview';

// Scene data is injected by the presenter, not inferred by the graphics layer.
export default makeScene2D(function*(view){
 const s=(window as any).presenterScene;
 if(s.kind==='code-preview'){yield* codePreview(view,s);return;}
 const {x,y,width,height}=s.captions.rect;
 const panel=createRef<Rect>();
 view.add(<Rect ref={panel} x={x+width/2-960} y={y+height/2-540} width={width} height={height} radius={14} fill={'#101926f5'} stroke={'#697482'} lineWidth={1.4} shadowBlur={10} shadowColor={'#00000060'} shadowOffsetY={4} opacity={0}/>);
 const p=panel();const left=-width/2;
 const label=(text:string,cx:number,cy:number,size=22,fill='#efb65e')=>p.add(<Txt text={text} x={left+cx} y={cy} fontFamily={'Consolas'} fontSize={size} fill={fill}/>);
 label('alphabet',78,10,24);
 s.captions.values.alphabet.forEach((letter:string,i:number)=>{
  const cx=175+i*62,active=i===s.captions.values.current.index;
  label(String(i),cx,-31,17,active?'#ffc75b':'#9aa6b7');
  p.add(<Rect x={left+cx} y={11} width={52} height={45} radius={6} stroke={active?'#ffc75b':'#505d70'} lineWidth={active?2:1.2} fill={active?'#554421':'#131e2c'}/>);
  label(letter,cx,11,28,'#f7f8fc');
 });
 p.add(<Rect x={left+667} width={1} height={66} fill={'#566476'}/>);
 label('current',755,10,24);label('index',860,-30,17,'#9aa6b7');label('value',1032,-30,17,'#9aa6b7');
 for(const [cx,w,text,color] of [[860,66,String(s.captions.values.current.index),'#ffffff'],[1032,215,s.captions.values.current.value,'#caa4f2']] as const){
  p.add(<Rect x={left+cx} y={11} width={w} height={45} radius={6} stroke={'#667080'} lineWidth={1.2} fill={'#111c29'}/>);label(text,cx,11,25,color);
 }
 p.add(<Rect x={left+1175} width={1} height={66} fill={'#566476'}/>);
 label('random',1250,10,23);p.add(<Rect x={left+1390} y={11} width={104} height={45} radius={6} stroke={'#667080'} lineWidth={1.2} fill={'#111c29'}/>);label('—',1390,11,25,'#c3cbd6');
 yield* p.opacity(1,.3);yield* waitFor(s.duration+.5);
});
