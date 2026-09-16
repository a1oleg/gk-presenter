// Six presentation frames derived from the user's real, manually arranged scene.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const require=createRequire(path.resolve('../coldKode/package.json'));
const {DOMParser,XMLSerializer}=require('@xmldom/xmldom');
const source=path.resolve('../coldKode/graph/draw/scenes/fisher.drawio');
const out=path.resolve('../coldKode/graph/draw/scenes/fisher-search');
const original=await fs.readFile(source,'utf8');
const distractors=Array.from({length:12},(_,i)=>String(i+5));
const indices=['3','4','6','8','10','12','14','16'];
const narration=[
 '',
 'Сразу скажу, что нас будут интересовать слова «меняет» и «случайный».',
 'Проблема в том, что во всём остальном коде много чего обменивается, и случайность также используется в разных местах.',
 'И когда придёт запрос: «Почему буквы меняются случайным образом?»…',
 '…даже если у нас есть индексы, мы найдём очень много вхождений, размазанных по всей кодовой базе.',
 'Но для всех найденных кандидатов мы можем провести кластеризацию и обнаружить, что эти двое из ларца — getRandom и swap — вызываются общим родителем shuffle. А значит, именно они являются приоритетными для разбора в ответе на запрос.'
];
const manifest={source,sourceSha256:createHash('sha256').update(original).digest('hex'),kind:'illustrative-search-not-live-retrieval',canvas:[1600,900],frames:[]};
for(let stage=1;stage<=6;stage++){
 const doc=new DOMParser().parseFromString(original,'text/xml');
 const objects=[...doc.getElementsByTagName('object')];
 const byId=id=>objects.find(o=>o.getAttribute('id')===id);
 const cell=o=>o.getElementsByTagName('mxCell')[0];
 const style=(o,k,v)=>{const c=cell(o);c.setAttribute('style',c.getAttribute('style').split(';').filter(s=>s&&!s.startsWith(k+'=')).concat(k+'='+v).join(';')+';');};
 const hide=o=>{style(o,'opacity',0);style(o,'textOpacity',0);};
 for(const id of indices){style(byId(id),'fontSize',14);style(byId(id),'spacing',6);style(byId(id),'verticalAlign','middle');}
 for(const id of distractors){
  const o=byId(id);if(!o)throw Error('Missing user-authored distractor '+id);
  // Copied example nodes must not masquerade as actual getRandom/swap entities.
  for(const key of ['stableId','annotationOwnerStableId','labels','revealOrder'])o.removeAttribute(key);
  o.setAttribute('presentationOnly','1');o.setAttribute('annotationSource','illustrative-search');
  if(stage<3)hide(o);
 }
 if(stage<2)for(const id of ['3','4'])hide(byId(id));
 const root=doc.getElementsByTagName('root')[0];
 // A fixed transparent camera anchor avoids zoom jumps as elements appear.
 const anchor=doc.createElement('mxCell');
 for(const [k,v] of Object.entries({id:'search-camera',value:'',vertex:'1',parent:'1',style:'fillColor=none;strokeColor=none;opacity=0;'}))anchor.setAttribute(k,v);
 const geom=doc.createElement('mxGeometry');for(const [k,v]of Object.entries({x:'0',y:'0',width:'1600',height:'900',as:'geometry'}))geom.setAttribute(k,v);
 anchor.appendChild(geom);root.appendChild(anchor);
 // Hide the annotation behind the query instead of leaving overlapping text.
 if(stage>=4)hide(byId('snippet-shuffle'));
 const banner=doc.createElement('object');banner.setAttribute('id','search-query');banner.setAttribute('label','Почему буквы меняются случайным образом?');banner.setAttribute('presentationOnly','1');
 const bc=doc.createElement('mxCell');bc.setAttribute('vertex','1');bc.setAttribute('parent','1');bc.setAttribute('style','rounded=1;whiteSpace=wrap;html=0;fontSize=24;fontStyle=1;spacing=16;fillColor=#e8efff;strokeColor=#4267b2;strokeWidth=2;');
 const bg=byId('snippet-shuffle').getElementsByTagName('mxGeometry')[0].cloneNode(true);bc.appendChild(bg);banner.appendChild(bc);root.appendChild(banner);if(stage<4)hide(banner);
 if(stage>=5){
  for(const id of indices){
   const o=byId(id),text=o.getAttribute('label');
   o.setAttribute('label',text.replace(/(Меняет|случайный)/gi,'<b style="background-color:#ffbd38;color:#172b4d;padding:2px">$1</b>'));
   style(o,'html',1);style(o,'strokeColor','#dc9600');style(o,'strokeWidth',2);
  }
 }
 // Annotation-index link already present in the user's source.
 const link=[...doc.getElementsByTagName('mxCell')].find(c=>c.getAttribute('id')==='17');
 if(stage<2)link.setAttribute('style',link.getAttribute('style')+'opacity=0;');
 if(stage===6){
  for(const id of distractors){style(byId(id),'opacity',30);style(byId(id),'textOpacity',30);}
  for(const o of objects){
   if(o.getAttribute('id').startsWith('e-')){style(o,'strokeColor','#159447');style(o,'strokeWidth',4);}
  }
  for(const id of ['3','4']){style(byId(id),'strokeColor','#159447');style(byId(id),'strokeWidth',4);}
 }
 const dir=path.join(out,`frame-${String(stage).padStart(2,'0')}`);await fs.mkdir(dir,{recursive:true});
 await fs.writeFile(path.join(dir,'source.drawio'),new XMLSerializer().serializeToString(doc));
 manifest.frames.push({stage,file:path.join(dir,'source.drawio'),narration:narration[stage-1]});
}
await fs.writeFile(path.join(out,'sequence.json'),JSON.stringify(manifest,null,2));
await fs.writeFile(path.join(out,'README.md'),'# Поиск по индексам и графовая близость\n\nШесть кадров из пользовательской сцены fisher.drawio. Исходник не изменяется.\nИндексы и отвлекающие Fn — иллюстрация, не результаты реального поиска.\nУ копий отвлекающих Fn удалены чужие stableId, чтобы они не представляли getRandom.\nРеальные связи сохранены: shuffle → узел вызова → реализация.\nБлизость повышает приоритет кандидатов, но не доказывает ответ.\n\n'+manifest.frames.map(f=>`${f.stage}. ${f.narration||'Фишер с аннотациями; без индексов и отвлекающих Fn.'}`).join('\n\n')+'\n');
if(createHash('sha256').update(await fs.readFile(source)).digest('hex')!==manifest.sourceSha256)throw Error('Source changed during build');
console.log(out);
