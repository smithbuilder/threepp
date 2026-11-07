"""Deterministic original city materials, no downloads. All dimensions are pixels.

Rebuild: python scripts/generate-city-materials.py
Textures are portable JPG/PNG; seed and source are kept with the project.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parents[1] / 'showcase/assets/city'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(427)

def save(name, arr):
    im = arr if isinstance(arr, Image.Image) else Image.fromarray(np.clip(arr,0,255).astype('uint8'))
    im.save(OUT / (name+'.jpg'), quality=92)

size=1024
fine=rng.normal(0,7,(size,size))
coarse=np.asarray(Image.fromarray(rng.integers(0,255,(32,32),dtype='uint8')).resize((size,size),Image.Resampling.BICUBIC),dtype=float)/255-0.5
asphalt=np.stack([53+fine+coarse*12,56+fine+coarse*12,57+fine+coarse*12],axis=-1)
save('asphalt',asphalt)
for name,base in [('brick',(133,69,48)),('buff-brick',(169,142,103)),('concrete',(156,153,140))]:
    n=512
    if name=='concrete':
        noise=rng.normal(0,3,(n,n,1))
        arr=np.ones((n,n,3))*base+noise
        arr[::128]-=16;arr[:,::256]-=16
    else:
        arr=np.zeros((n,n,3))+np.array((104,99,85))
        for row in range(16):
            for col in range(-1,5):
                x=col*128+(row%2)*64;y=row*32
                x0,x1=max(0,x+2),min(n,x+126)
                if x1>x0:arr[y+2:y+30,x0:x1]=np.array(base)+rng.normal(0,9)+rng.normal(0,3,(28,x1-x0,1))
    save(name,arr)
arr=np.ones((512,512,3))*np.array((174,170,155))+rng.normal(0,2,(512,512,1))
arr[::128]-=32;arr[:,::128]-=32
save('paving',arr)

# A single sign atlas keeps every shop label in one texture and one draw batch.
labels=[('CORNER COFFEE','ESPRESSO  /  BAKERY',(31,64,57)),('MERCER LOFTS','EST. 1928   /   LIVE & WORK',(39,47,49)),
        ('NORTH SUPPLY','HARDWARE  /  GOODS',(165,74,37)),('CINDER MOTOR WORKS','SERVICE  /  REPAIR  /  RESTORE',(36,64,77)),
        ('BAY WAREHOUSE','LOADING  /  NO PARKING',(90,53,42)),('MERCER ST','WAREHOUSE DISTRICT',(38,70,57)),
        ('30','CITY SPEED LIMIT',(228,218,185)),('BLOCK 04','CINDER   /   WAREHOUSE DISTRICT',(34,44,48))]
atlas=Image.new('RGB',(1024,1024));draw=ImageDraw.Draw(atlas)
font_path=Path('C:/Windows/Fonts/arialbd.ttf')
small_path=Path('C:/Windows/Fonts/arial.ttf')
for i,(title,sub,color) in enumerate(labels):
    y=i*128;draw.rectangle((0,y,1024,y+127),fill=color)
    ink=(42,44,42) if i==6 else (237,223,188)
    f=ImageFont.truetype(str(font_path),53 if len(title)<18 else 43)
    sf=ImageFont.truetype(str(small_path),20)
    draw.text((512,y+47),title,font=f,anchor='mm',fill=ink)
    draw.text((512,y+92),sub,font=sf,anchor='mm',fill=ink)
    draw.line((32,y+15,992,y+15),fill=ink,width=2);draw.line((32,y+113,992,y+113),fill=ink,width=2)
atlas.save(OUT/'signs.png')
(OUT/'source.json').write_text(json.dumps({'name':'Mercer city block','units':'metres','authoring':'Original geometry, sign atlas and fallback procedural maps. Photographic PBR surfaces and sky are separately credited in photo-surfaces.json.','seed':427,'textureColorSpace':'sRGB','license':'Project-authored geometry and fallback textures use repository terms; photographic assets are CC0-1.0.','rebuild':'scripts/generate-city-materials.py, scripts/generate-city-details.py, scripts/fetch-city-surfaces.py','signFont':'Arial from local Windows; rasterized labels only, font not redistributed'},indent=2)+'\n')
print(f'Wrote 6 city textures and provenance to {OUT}')
