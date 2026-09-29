export function resolveCues(events,alignment,duration) {
  if(!Array.isArray(events))throw Error('events must be an array');
  let text;
  if(alignment){
    alignment=alignment.alignment||alignment;
    if(!Array.isArray(alignment.characters)||!Array.isArray(alignment.character_start_times_seconds)||alignment.characters.length!==alignment.character_start_times_seconds.length)throw Error('Invalid audio alignment');
    if(!alignment.characters.every(c=>typeof c==='string'&&c.length===1)||!alignment.character_start_times_seconds.every((t,i,a)=>Number.isFinite(t)&&t>=0&&(!i||t>=a[i-1])))throw Error('Invalid alignment characters/timestamps');
    text=alignment.characters.join('');
  }
  const result=events.map(e=>{
    if(typeof e.diagramCell!=='string'||!e.diagramCell||!Number.isInteger(e.codeLine)||e.codeLine<1)throw Error('Cue needs diagramCell and codeLine');
    if((e.time!==undefined)===(e.anchor!==undefined))throw Error('Cue requires exactly one of time or anchor');
    let time=e.time;
    if(e.anchor!==undefined){
      if(text===undefined||typeof e.anchor!=='string'||!e.anchor)throw Error('Word cues require alignment and a nonempty anchor');
      const hits=[];for(let i=text.indexOf(e.anchor);i>=0;i=text.indexOf(e.anchor,i+1))hits.push(i);
      if(!hits.length)throw Error('Anchor not found: '+e.anchor);
      if(hits.length>1&&e.occurrence===undefined)throw Error('Repeated anchor requires occurrence');
      const n=e.occurrence??1;
      if(!Number.isInteger(n)||n<1||n>hits.length)throw Error('Anchor occurrence not found');
      time=alignment.character_start_times_seconds[hits[n-1]];
    }
    if(!Number.isFinite(time)||time<0||time>=duration)throw Error('Cue outside clip duration');
    return {...e,time};
  });
  if(result.some((e,i)=>i&&e.time<result[i-1].time))throw Error('Cues must be chronological');
  return result;
}
