import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
out=Path(sys.argv[1]);rows=json.loads((out/'scenario-source.json').read_text(encoding='utf8'))['values']
im=Image.new('RGBA',(1920,90),'#171b22');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',24);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
d.text((32,4),'alphabet',font=font,fill='#eab86c');d.text((1120,4),'current',font=font,fill='#eab86c');d.text((1710,4),'random',font=font,fill='#eab86c')
for i in range(8):
 x=75+i*115;d.text((x,33),rows[2][1+i],font=small,fill='#9ba5b7',anchor='mt');d.text((x,56),rows[3][1+i],font=font,fill='white',anchor='mt')
for x,col in [(1190,10),(1420,11)]:
 d.text((x,33),rows[2][col],font=small,fill='#9ba5b7',anchor='mt');d.text((x,56),rows[3][col],font=font,fill='#c8a6ec' if col==11 else 'white',anchor='mt')
d.text((1760,56),rows[3][13],font=font,fill='white',anchor='mt');im.save(out/'captions.png')
