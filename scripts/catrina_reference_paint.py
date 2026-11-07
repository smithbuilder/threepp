"""Rectify user-supplied atlas paint into the model's UV orientation.

This is a documented derivative of the supplied reference, not newly authored
paint. Only paint fields are sampled; lamps, chrome, glazing and environment
pixels are excluded. Fine ornament masks are separated from broad illustration
lighting and remapped to the atlas's labeled paint pigments before UV resampling.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/la-catrina/references/La-Catrina-Master.jpg'
SOURCE_SHA='62c46159d87f29348a35ecb07584d752cf3a15161b19c655968d0da96a42d750'
# PIL QUAD order: upper left, lower left, lower right, upper right.
# Original image dimensions:4560x9413; every coordinate is in source pixels.
REGIONS={
    'roof':{'quad':[(1054,2917),(1047,3257),(1462,3260),(1450,2914)],'size':(406,344)},
    'hood_right':{'quad':[(503,2908),(499,3072),(821,3074),(851,2899)],'size':(333,166)},
    'hood_left':{'quad':[(500,3097),(508,3266),(850,3269),(820,3097)],'size':(331,170)},
    'deck':{'quad':[(1600,2900),(1600,3270),(1863,3270),(1863,2900)],'size':(263,370)},
}
SIDE_SCROLL_QUAD=[(1520,1330),(1520,1356),(1970,1324),(1970,1297)]
SIDE_SCROLL_SIZE=(450,27)
CANDY=np.array([183,37,99],np.float32)
CHAMPAGNE=np.array([203,162,108],np.float32)

def create_paint():
    data=SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:raise ValueError('La Catrina source atlas changed; recheck paint regions')
    source=Image.open(SOURCE).convert('RGB');result={}
    for name,spec in REGIONS.items():
        quad=[x for pair in spec['quad'] for x in pair]
        crop=source.transform(spec['size'],Image.Transform.QUAD,quad,Image.Resampling.BICUBIC)
        a=np.asarray(crop,dtype=np.float32)
        # A 35-source-pixel low-pass estimates only broad illumination. Limiting
        # correction avoids washing out the original ornament and paint grain.
        lum=a@np.array([.2126,.7152,.0722],np.float32)
        field=gaussian_filter(lum,35,mode='reflect');scale=np.clip(np.median(field)/np.maximum(field,5.1),.84,1.18)
        a*=scale[:,:,None]
        # Chroma retains broad champagne strokes; local green-channel contrast
        # recovers the fine fan/radial lines that chroma thresholding alone loses.
        # This removes baked illustration highlights without inventing a pattern.
        red_ratio=a[:,:,1]/np.maximum(a[:,:,0],1)
        broad=np.clip((red_ratio-.32)/.30,0,1)
        fine=np.clip((a[:,:,1]-gaussian_filter(a[:,:,1],2.5)-1.5)/25,0,1)
        mask=np.maximum(broad,.9*fine)[:,:,None]
        grain=np.clip(a[:,:,0]-gaussian_filter(a[:,:,0],.75),-3,3)[:,:,None]
        painted=CANDY*(1-mask)+CHAMPAGNE*mask+grain*(1-mask)
        out=Image.fromarray(np.uint8(np.clip(painted,0,255)))
        # Source car points left; model +Z front points toward texture bottom.
        out=out.transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        result[name]=out.resize((1024,1024),Image.Resampling.LANCZOS)
    # The cowl boundary is concave in the atlas; sampling each painted hood
    # panel separately prevents chrome ventilation slots from entering the UVs.
    hood=Image.new('RGB',(1024,1024),(183,37,99))
    hood.paste(result.pop('hood_left').resize((480,992),Image.Resampling.LANCZOS),(16,16))
    hood.paste(result.pop('hood_right').resize((480,992),Image.Resampling.LANCZOS),(528,16))
    result['hood']=hood
    # The main hero view resolves the flowing ornament at450x27 source pixels,
    # three times the former strip's height. Rectify between its chrome borders.
    scroll=np.asarray(source.transform(SIDE_SCROLL_SIZE,Image.Transform.QUAD,
        [v for xy in SIDE_SCROLL_QUAD for v in xy],Image.Resampling.BICUBIC),np.float32)
    ratio=scroll[:,:,1]/np.maximum(scroll[:,:,0],1)
    broad=np.clip((ratio-.28)/.34,0,1)
    fine=np.clip((scroll[:,:,1]-gaussian_filter(scroll[:,:,1],1.6)-1)/22,0,1)
    mask=np.maximum(broad,.65*fine)[:,:,None]
    scroll=np.array([132,28,58])*(1-mask)+CHAMPAGNE*mask
    result['side_scroll']=Image.fromarray(np.uint8(scroll))
    receipt={'source':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'sourceSha256':SOURCE_SHA,'sourceSize':[4560,9413],'regions':REGIONS,'sideScroll':{'quad':SIDE_SCROLL_QUAD,'sourceSize':SIDE_SCROLL_SIZE,'processing':'Hero paint-only strip, excluding chrome borders and cameos. Mask=max(clamp((G/R-.28)/.34),.65*clamp((G-Gaussian1.6(G)-1)/22)); remap between cherry RGB132,28,58 and labeled Champagne RGB203,162,108. Approximately0.96m repeat.'},'processing':['Bicubic QUAD rectification of paint-only quadrilaterals','Gaussian35px illumination estimate; luminance correction limited .84..1.18','Top ornament mask=max(clamp((G/R-.32)/.30),.9*clamp((G-Gaussian2.5(G)-1.5)/25)); remap to labeled Candy and Champagne pigments','Preserve source red-channel high-frequency grain, limited to +/-3 RGB values outside gold strokes','Rotate90CCW and mirror horizontally for model UV axes','Lanczos resample1024x1024'],'provenance':'Top paint and side-spear scroll ornament are masks derived from the user-supplied reference atlas. Geometry and small vector cameos remain original. No independent rights or public redistribution license is asserted for the supplied artwork.'}
    receipt['finishPalette']={'candy':{'sourceBox':[3000,1675,3230,1700],'medianRGB':[183,37,99]},'shellPink':{'sourceBox':[3290,1675,3520,1700],'medianRGB':[247,143,180]},'application':'Authored upper/lower pigments follow the explicitly labeled Candy and Shell pink swatches; their side transition is hidden beneath the gold spear. Plain upper painted parts and protected top-map pigment alignment use the same Candy value. These are illustrative reference pigments, not measured physical reflectance.'}
    receipt['finishPalette']['champagne']={'sourceBox':[3870,1675,4090,1700],'medianRGB':[203,162,108]}
    return result,receipt

if __name__=='__main__':
    textures,receipt=create_paint();out=ROOT/'build/la-catrina/reference-paint';out.mkdir(parents=True,exist_ok=True)
    for name,image in textures.items():image.save(out/(name+'.png'))
    (out/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
