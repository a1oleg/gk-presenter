"""Compile speech alignment, sheet snapshots and real source targets into one scene."""
import copy,json,subprocess,sys,wave
from pathlib import Path
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]).resolve()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
s=load(ROOT/'output/caption-clearance-1790062901829/scenario.json')
rows=load(out/'scenario-source.json')['values'];sheet=load(out/'sheet-source.json')['values'][0]
assert sheet[5]==s['diagram']['top'] and sheet[6]==s['diagram']['bottom'] and sheet[7]==s['diagram']['rightmost'],'Framing selectors changed'
ff=imageio_ffmpeg.get_ffmpeg_exe();chunks=[];segments=[];clock=0
alignment={'characters':[],'character_start_times_seconds':[],'character_end_times_seconds':[]}
for number in range(4,10):
 part=out/f'row-{number:02d}';wav=part/'speech.wav'
 if not wav.exists():subprocess.run([ff,'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(part/'speech.mp3'),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(wav)],check=True)
 with wave.open(str(wav),'rb') as media:raw=media.readframes(media.getnframes());duration=media.getnframes()/48000
 a=load(part/'alignment.json')['alignment'];text=''.join(a['characters'])
 segments.append({'row':number,'start':clock,'speechDuration':duration,'duration':duration+.35,'text':text,'alignment':a})
 alignment['characters']+=a['characters']
 for field in ['character_start_times_seconds','character_end_times_seconds']:alignment[field]+=[clock+t for t in a[field]]
 chunks.extend([raw,b'\x00\x00'*16800]);clock+=duration+.35
with wave.open(str(out/'speech.wav'),'wb') as media:
 media.setparams((1,2,48000,0,'NONE','not compressed'))
 for chunk in chunks:media.writeframes(chunk)
if not (out/'speech.mp3').exists():subprocess.run([ff,'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(out/'speech.wav'),'-c:a','libmp3lame','-b:a','192k',str(out/'speech.mp3')],check=True)
save(out/'alignment.json',{'alignment':alignment})
def moment(row,word):
 segment=segments[row-4];index=segment['text'].lower().find(word.lower())
 assert index>=0,(row,word,segment['text'])
 return segment['start']+segment['alignment']['character_start_times_seconds'][index]
targets={
4:[('массив','f0-n9-part-1',26,'alphabet'),('объект','f0-n5-part-1',25,'current.index')],
5:[('Из массива','f0-n9-part-1',26,'alphabet'),('по индексу','f0-n9-part-4',26,'current.index'),('присваиваем','f0-n7-part-2',26,'current.value')],
6:[('переменную','f0-n8-part-1',27,'random'),('функцию','f0-n11-part-1',27,'getRandom'),('количество','f0-n11-part-2',27,'current.index'),('Вызовы функций','f0-n11-part-1',27,'getRandom')],
7:[('актуальную длину','f1-n4-part-6',34,'length'),('генерирует','f1-n4-part-4',35,'random'),('округляет','f1-n4-part-2',35,'floor'),('возвращает','f1-n3-part-2',36,'randomIndex'),('получаем','f0-n8-part-1',27,'random')],
8:[('вызываем','f0-n10',28,'swap'),('массиве','f0-n15',28,'alphabet'),('актуальное','f0-n13',28,'current'),('рандом','f0-n14',28,'random'),('наоборот','f0-n15',28,'alphabet')],
9:[('завершим цикл','f0-n12-part-1',25,'current.index--'),('уменьшим','f0-n12-part-2',25,'--'),('проверки','f0-n5-part-3',25,'>'),('передавать','f0-n11-part-2',27,'current.index'),('Таким образом','f0-n15',28,'alphabet')]
}
s['events']=[{'row':row,'atWord':word,'time':moment(row,word),'diagramCell':cell,'codeLine':line,'codeToken':token} for row,items in targets.items() for word,cell,line,token in items]
s['events'].sort(key=lambda e:e['time'])
v=copy.deepcopy(s['captions']['values']);s['captionEvents']=[]
triggers={5:'присваиваем',7:'6',8:'наоборот'}
for number in range(5,10):
 row=rows[number-1]+['']*14
 for i,value in enumerate(row[1:9]):
  if value:v['alphabet'][i]=value
 if row[10]:v['current']['index']=int(row[10])
 if row[11]:v['current']['value']=row[11]
 if row[13]:v['random']=None if row[13]=='-' else int(row[13])
 if number in triggers:s['captionEvents'].append({'time':moment(number,triggers[number]),'row':number,'values':copy.deepcopy(v),'source':'nonblank sheet cells; blank = retain previous'})
 if number==9:
  v['current']['index']-=1
  s['captionEvents'].append({'time':moment(9,'уменьшим'),'row':9,'values':copy.deepcopy(v),'source':'narrated decrement by one; shuffle.ts:25 current.index--'})
s['duration']=clock;s['id']='fisher-scenario-A1-N9';s['scenarioRange']="'ФЙ-сценарий'!A1:N9";s['audioSource']=str(out/'speech.wav');s['voiceNote']='3.3; first paragraph reused, remaining generated'
if (out/'sheet-headers.json').exists():
 video_index=load(out/'sheet-headers.json')['values'][0].index('ссылка на видео')
 s['sheetRange']='!A11:Z11';s['publishRange']=f"'Видео'!{chr(65+video_index)}11"
s['paragraphs']=[{k:v for k,v in segment.items() if k!='alignment'} for segment in segments]
save(out/'scenario.json',s);save(out/'code-source.json',s['code']['source'])
save(out/'timeline.json',{'paragraphs':s['paragraphs'],'events':s['events'],'captionEvents':s['captionEvents'],'duration':clock})
print(json.dumps({'duration':clock,'paragraphs':len(segments),'pointers':len(s['events']),'captionChanges':len(s['captionEvents'])}))
